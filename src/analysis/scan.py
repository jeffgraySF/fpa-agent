"""Full formula scan — detects errors, static values in formula rows, and pattern breaks."""

import re
from typing import Any


def _formula_pattern(formula: str) -> str:
    """Normalize a formula to its structural pattern by replacing all cell refs.

    e.g. =SUMIF($A$2:$A$100,B$1,'Sheet'!C5) -> =SUMIF(CELL,CELL,CELL)
    This lets us compare formulas structurally without caring which cells they ref.
    """
    # Replace cross-sheet refs like 'Sheet Name'!A1 or Sheet!A1
    result = re.sub(r"'[^']+'![A-Z$]{1,3}\$?\d*", "CELL", formula)
    result = re.sub(r"[A-Za-z_][A-Za-z0-9_]*![A-Z$]{1,3}\$?\d*", "CELL", result)
    # Replace remaining cell refs like $A$1, A1, $A1, A$1, AA1, etc.
    result = re.sub(r"\$?[A-Z]{1,3}\$?\d+", "CELL", result)
    return result


def scan_sheet(sheet_name: str, client: Any) -> dict[str, Any]:
    """Scan an entire sheet for formula anomalies.

    Reads every cell in the sheet and checks for:
    - Error values (#REF!, #VALUE!, #NAME?, #DIV/0!, #N/A, #NULL!, #NUM!)
    - Static values sitting inside a formula row (likely overwritten formulas)
    - Formula pattern breaks (a cell whose structure differs from the row norm)

    Args:
        sheet_name: Name of the sheet to scan.
        client: SheetsClient instance connected to the spreadsheet.

    Returns:
        Dict with keys:
        - sheet_name, rows_scanned, cols_scanned
        - errors: list of {cell, row_label, error, formula}
        - static_in_formula_rows: list of {cell, row_label, value}
        - pattern_breaks: list of {cell, row_label, formula, dominant_pattern}
    """
    info = client.get_spreadsheet_info()
    sheet_info = next((s for s in info["sheets"] if s["name"] == sheet_name), None)
    if not sheet_info:
        raise ValueError(f"Sheet '{sheet_name}' not found")

    col_count = min(sheet_info["column_count"], 52)
    end_col = client._col_index_to_letter(col_count - 1)

    # Find actual data extent via column A
    col_a_vals = client.read_range(sheet_name, "A1:A1000")
    last_row = max(
        (i + 1 for i, r in enumerate(col_a_vals) if r and r[0]),
        default=0,
    )

    if last_row == 0:
        return {
            "sheet_name": sheet_name,
            "rows_scanned": 0,
            "cols_scanned": col_count,
            "errors": [],
            "static_in_formula_rows": [],
            "pattern_breaks": [],
        }

    # Two API calls — formulas and display values for the whole sheet
    formulas = client.read_formulas(sheet_name, f"A1:{end_col}{last_row}")
    values = client.read_range(sheet_name, f"A1:{end_col}{last_row}")

    errors: list[dict] = []
    static_in_formula_rows: list[dict] = []
    pattern_breaks: list[dict] = []

    error_prefixes = ("#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#N/A", "#NULL!", "#NUM!", "#ERROR!")

    for row_idx in range(last_row):
        formula_row = formulas[row_idx] if row_idx < len(formulas) else []
        value_row = values[row_idx] if row_idx < len(values) else []
        row_label = str(formula_row[0]).strip() if formula_row and formula_row[0] else ""

        formula_cols: list[tuple[int, str]] = []  # (col_idx, formula)
        static_cols: list[tuple[int, str]] = []   # (col_idx, value)

        for col_idx in range(1, col_count):  # skip col A (labels)
            formula = formula_row[col_idx] if col_idx < len(formula_row) else ""
            value = value_row[col_idx] if col_idx < len(value_row) else ""

            if isinstance(formula, str) and formula.startswith("="):
                formula_cols.append((col_idx, formula))
                # Check if the computed value is an error
                if isinstance(value, str) and any(value.startswith(e) for e in error_prefixes):
                    errors.append({
                        "cell": f"{client._col_index_to_letter(col_idx)}{row_idx + 1}",
                        "row_label": row_label,
                        "error": value,
                        "formula": formula,
                    })
            elif formula or value:
                static_cols.append((col_idx, str(formula or value)))

        # Static-in-formula-row: a non-formula cell sitting between the first
        # and last formula column of a row that has at least 3 formula cells
        if len(formula_cols) >= 3:
            first_fc = formula_cols[0][0]
            last_fc = formula_cols[-1][0]
            for col_idx, val in static_cols:
                if first_fc <= col_idx <= last_fc:
                    static_in_formula_rows.append({
                        "cell": f"{client._col_index_to_letter(col_idx)}{row_idx + 1}",
                        "row_label": row_label,
                        "value": val,
                    })

        # Pattern-break: a formula whose structural pattern appears only once
        # while a different pattern dominates the rest of the row
        if len(formula_cols) >= 4:
            patterns = [(_formula_pattern(f), col_idx, f) for col_idx, f in formula_cols]
            counts: dict[str, int] = {}
            for pat, _, _ in patterns:
                counts[pat] = counts.get(pat, 0) + 1
            dominant = max(counts, key=counts.get)

            for pat, col_idx, formula in patterns:
                if pat != dominant and counts[pat] == 1:
                    pattern_breaks.append({
                        "cell": f"{client._col_index_to_letter(col_idx)}{row_idx + 1}",
                        "row_label": row_label,
                        "formula": formula,
                        "dominant_pattern": dominant,
                    })

    return {
        "sheet_name": sheet_name,
        "rows_scanned": last_row,
        "cols_scanned": col_count,
        "errors": errors,
        "static_in_formula_rows": static_in_formula_rows,
        "pattern_breaks": pattern_breaks,
    }
