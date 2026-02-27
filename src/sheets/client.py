"""Google Sheets API client wrapper."""

import os
import time
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .auth import get_credentials
from .url import extract_spreadsheet_id

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class SheetsClient:
    """High-level client for Google Sheets operations."""

    def __init__(self, spreadsheet_id: str | None = None):
        """Initialize the Sheets client.

        Args:
            spreadsheet_id: The ID of the spreadsheet to work with, or a full URL.
                           Defaults to SPREADSHEET_ID env var.
        """
        raw_id = spreadsheet_id or os.getenv("SPREADSHEET_ID")
        if raw_id:
            self.spreadsheet_id = extract_spreadsheet_id(raw_id)
        else:
            self.spreadsheet_id = None  # No spreadsheet set yet

        creds = get_credentials()
        self._service = build("sheets", "v4", credentials=creds)
        self._sheets = self._service.spreadsheets()
        self._info_cache: dict[str, Any] | None = None

    def set_spreadsheet(self, url_or_id: str) -> dict[str, Any]:
        """Switch to a different spreadsheet.

        Args:
            url_or_id: Google Sheets URL or spreadsheet ID.

        Returns:
            Info about the spreadsheet that was connected.
        """
        self.spreadsheet_id = extract_spreadsheet_id(url_or_id)
        self._info_cache = None
        return self.get_spreadsheet_info()

    def _require_spreadsheet(self):
        """Raise an error if no spreadsheet is set."""
        if not self.spreadsheet_id:
            raise ValueError(
                "No spreadsheet connected. Use connect_to_spreadsheet tool with a Google Sheets URL first."
            )

    def _execute(self, request, retries: int = 4) -> Any:
        """Execute an API request with exponential backoff on retryable errors.

        Args:
            request: A googleapiclient request object.
            retries: Maximum number of retry attempts.

        Returns:
            API response.
        """
        delay = 1.0
        for attempt in range(retries + 1):
            try:
                return request.execute()
            except HttpError as e:
                if e.status_code in _RETRYABLE_STATUS_CODES and attempt < retries:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

    # ─────────────────────────────────────────────────────────────────────────
    # Read operations
    # ─────────────────────────────────────────────────────────────────────────

    def get_spreadsheet_info(self) -> dict[str, Any]:
        """Get metadata about the spreadsheet including all sheet names.

        Result is cached for the lifetime of this spreadsheet connection.
        """
        self._require_spreadsheet()
        if self._info_cache is not None:
            return self._info_cache
        result = self._execute(self._sheets.get(spreadsheetId=self.spreadsheet_id))
        self._info_cache = {
            "title": result["properties"]["title"],
            "sheets": [
                {
                    "name": sheet["properties"]["title"],
                    "sheet_id": sheet["properties"]["sheetId"],
                    "row_count": sheet["properties"]["gridProperties"]["rowCount"],
                    "column_count": sheet["properties"]["gridProperties"]["columnCount"],
                }
                for sheet in result["sheets"]
            ],
        }
        return self._info_cache

    def _read_range(self, sheet_name: str, range_spec: str, render_option: str) -> list[list[Any]]:
        """Internal range read with a given valueRenderOption."""
        self._require_spreadsheet()
        result = self._execute(
            self._sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!{range_spec}",
                valueRenderOption=render_option,
            )
        )
        return result.get("values", [])

    def read_range(self, sheet_name: str, range_spec: str) -> list[list[Any]]:
        """Read values from a range.

        Args:
            sheet_name: Name of the sheet (tab).
            range_spec: A1 notation range (e.g., "A1:D10").

        Returns:
            2D list of cell values.
        """
        return self._read_range(sheet_name, range_spec, "FORMATTED_VALUE")

    def read_formulas(self, sheet_name: str, range_spec: str) -> list[list[Any]]:
        """Read formulas from a range (returns formula text, not computed values).

        Args:
            sheet_name: Name of the sheet (tab).
            range_spec: A1 notation range (e.g., "A1:D10").

        Returns:
            2D list of cell formulas/values.
        """
        return self._read_range(sheet_name, range_spec, "FORMULA")

    def inspect_sheet(self, sheet_name: str, sample_rows: int = 20) -> dict[str, Any]:
        """Get a comprehensive view of a sheet's structure for analysis.

        Returns headers, sample data, sample formulas, and identifies which
        columns contain formulas vs static data.

        Args:
            sheet_name: Name of the sheet to inspect.
            sample_rows: Number of rows to sample (default 20).

        Returns:
            Dict with structure information:
            - headers: First row values
            - row_labels: First column values (often row labels)
            - sample_values: Sample of data values
            - sample_formulas: Sample of formulas
            - formula_columns: Which columns contain formulas
            - data_columns: Which columns contain static data
            - row_count: Approximate row count with data
        """
        self._require_spreadsheet()

        # Get sheet dimensions (uses cache)
        info = self.get_spreadsheet_info()
        sheet_info = next((s for s in info["sheets"] if s["name"] == sheet_name), None)
        if not sheet_info:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        col_count = min(sheet_info["column_count"], 50)  # Cap at 50 columns
        end_col = self._col_index_to_letter(col_count - 1)

        # Read headers (row 1)
        headers = self.read_range(sheet_name, f"A1:{end_col}1")
        headers = headers[0] if headers else []

        # Read sample values and formulas
        sample_range = f"A1:{end_col}{sample_rows}"
        values = self.read_range(sheet_name, sample_range)
        formulas = self.read_formulas(sheet_name, sample_range)

        # Analyze which columns have formulas
        formula_columns = set()
        data_columns = set()

        for row in formulas[1:]:  # Skip header row
            for col_idx, cell in enumerate(row):
                if isinstance(cell, str) and cell.startswith("="):
                    formula_columns.add(col_idx)
                elif cell:  # Non-empty, non-formula
                    data_columns.add(col_idx)

        # Get row labels (column A) from already-fetched values
        row_labels = [row[0] if row else "" for row in values]

        # Estimate total rows from column A in the sample; if sample is full,
        # fetch a larger range to find the true extent
        if len(values) >= sample_rows:
            col_a_extended = self._read_range(sheet_name, "A1:A500", "FORMATTED_VALUE")
            last_row = len([r for r in col_a_extended if r and r[0]])
        else:
            last_row = len([r for r in values if r and r[0]])

        return {
            "sheet_name": sheet_name,
            "headers": headers,
            "row_labels": row_labels,
            "sample_values": values,
            "sample_formulas": formulas,
            "formula_columns": sorted(formula_columns),
            "data_columns": sorted(data_columns),
            "estimated_row_count": last_row,
            "column_count": len(headers),
        }

    def _col_index_to_letter(self, index: int) -> str:
        """Convert a 0-based column index to letter (0=A, 25=Z, 26=AA)."""
        result = ""
        index += 1  # Convert to 1-based
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def get_sheet_id(self, sheet_name: str) -> int:
        """Get the numeric sheet ID for a sheet name."""
        info = self.get_spreadsheet_info()
        for sheet in info["sheets"]:
            if sheet["name"] == sheet_name:
                return sheet["sheet_id"]
        raise ValueError(f"Sheet '{sheet_name}' not found")

    # ─────────────────────────────────────────────────────────────────────────
    # Write operations
    # ─────────────────────────────────────────────────────────────────────────

    def write_range(
        self,
        sheet_name: str,
        range_spec: str,
        values: list[list[Any]],
        raw: bool = False,
    ) -> dict[str, Any]:
        """Write values to a range.

        Args:
            sheet_name: Name of the sheet (tab).
            range_spec: A1 notation range (e.g., "A1:D10").
            values: 2D list of values to write.
            raw: If True, values are written as-is. If False, values are parsed
                 (e.g., "=SUM(A1:A10)" becomes a formula).

        Returns:
            API response with update details.
        """
        self._require_spreadsheet()
        return self._execute(
            self._sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!{range_spec}",
                valueInputOption="RAW" if raw else "USER_ENTERED",
                body={"values": values},
            )
        )

    def append_rows(
        self,
        sheet_name: str,
        values: list[list[Any]],
        start_column: str = "A",
    ) -> dict[str, Any]:
        """Append rows to the end of a sheet.

        Args:
            sheet_name: Name of the sheet (tab).
            values: 2D list of row values to append.
            start_column: Column to start appending from.

        Returns:
            API response with update details.
        """
        self._require_spreadsheet()
        return self._execute(
            self._sheets.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!{start_column}:{start_column}",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values},
            )
        )

    def clear_range(self, sheet_name: str, range_spec: str) -> dict[str, Any]:
        """Clear values from a range (keeps formatting).

        Args:
            sheet_name: Name of the sheet (tab).
            range_spec: A1 notation range (e.g., "A1:D10").

        Returns:
            API response.
        """
        self._require_spreadsheet()
        return self._execute(
            self._sheets.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!{range_spec}",
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Batch operations
    # ─────────────────────────────────────────────────────────────────────────

    def batch_update(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch of update requests.

        This is the low-level method for formatting, inserting rows/columns,
        and other structural changes.

        Args:
            requests: List of request objects per the Sheets API spec.

        Returns:
            API response.
        """
        self._require_spreadsheet()
        return self._execute(
            self._sheets.batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests},
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Formatting helpers
    # ─────────────────────────────────────────────────────────────────────────

    def set_freeze(self, sheet_name: str, rows: int = 0, columns: int = 0) -> dict[str, Any]:
        """Freeze rows and/or columns.

        Args:
            sheet_name: Name of the sheet.
            rows: Number of rows to freeze from top.
            columns: Number of columns to freeze from left.

        Returns:
            API response.
        """
        sheet_id = self.get_sheet_id(sheet_name)
        return self.batch_update([
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "frozenRowCount": rows,
                            "frozenColumnCount": columns,
                        },
                    },
                    "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
                }
            }
        ])

    def format_range(
        self,
        sheet_name: str,
        range_spec: str,
        number_format: dict[str, str] | None = None,
        bold: bool | None = None,
        font_family: str | None = None,
        font_size: int | None = None,
    ) -> dict[str, Any]:
        """Apply formatting to a range.

        Args:
            sheet_name: Name of the sheet.
            range_spec: A1 notation range.
            number_format: Dict with 'type' and 'pattern' keys.
                          Types: TEXT, NUMBER, CURRENCY, DATE, PERCENT, etc.
            bold: Whether text should be bold.
            font_family: Font name (e.g., "Roboto").
            font_size: Font size in points.

        Returns:
            API response.
        """
        sheet_id = self.get_sheet_id(sheet_name)
        grid_range = self._a1_to_grid_range(range_spec, sheet_id)

        cell_format: dict[str, Any] = {}
        fields: list[str] = []

        if number_format:
            cell_format["numberFormat"] = number_format
            fields.append("userEnteredFormat.numberFormat")

        text_format: dict[str, Any] = {}
        if bold is not None:
            text_format["bold"] = bold
            fields.append("userEnteredFormat.textFormat.bold")
        if font_family:
            text_format["fontFamily"] = font_family
            fields.append("userEnteredFormat.textFormat.fontFamily")
        if font_size:
            text_format["fontSize"] = font_size
            fields.append("userEnteredFormat.textFormat.fontSize")

        if text_format:
            cell_format["textFormat"] = text_format

        return self.batch_update([
            {
                "repeatCell": {
                    "range": grid_range,
                    "cell": {"userEnteredFormat": cell_format},
                    "fields": ",".join(fields),
                }
            }
        ])

    def _a1_to_grid_range(self, range_spec: str, sheet_id: int) -> dict[str, Any]:
        """Convert A1 notation to GridRange format.

        Examples:
            "A1:D10" -> {sheetId: 0, startRowIndex: 0, endRowIndex: 10, startColumnIndex: 0, endColumnIndex: 4}
            "B:D" -> {sheetId: 0, startColumnIndex: 1, endColumnIndex: 4}
            "2:5" -> {sheetId: 0, startRowIndex: 1, endRowIndex: 5}
        """
        grid_range: dict[str, Any] = {"sheetId": sheet_id}

        # Handle range with colon
        if ":" in range_spec:
            start, end = range_spec.split(":")
            start_col, start_row = self._parse_cell_ref(start)
            end_col, end_row = self._parse_cell_ref(end)

            if start_col is not None:
                grid_range["startColumnIndex"] = start_col
            if end_col is not None:
                grid_range["endColumnIndex"] = end_col + 1
            if start_row is not None:
                grid_range["startRowIndex"] = start_row
            if end_row is not None:
                grid_range["endRowIndex"] = end_row + 1
        else:
            # Single cell
            col, row = self._parse_cell_ref(range_spec)
            if col is not None:
                grid_range["startColumnIndex"] = col
                grid_range["endColumnIndex"] = col + 1
            if row is not None:
                grid_range["startRowIndex"] = row
                grid_range["endRowIndex"] = row + 1

        return grid_range

    def _parse_cell_ref(self, ref: str) -> tuple[int | None, int | None]:
        """Parse a cell reference like 'A1' into (column_index, row_index)."""
        col_str = ""
        row_str = ""

        for char in ref:
            if char.isalpha():
                col_str += char.upper()
            elif char.isdigit():
                row_str += char

        col_index = None
        if col_str:
            col_index = 0
            for char in col_str:
                col_index = col_index * 26 + (ord(char) - ord("A") + 1)
            col_index -= 1  # Convert to 0-based

        row_index = None
        if row_str:
            row_index = int(row_str) - 1  # Convert to 0-based

        return col_index, row_index
