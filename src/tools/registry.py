"""Tool registry - defines tools available to the agent."""

from typing import Any

from src.sheets import SheetsClient

# ─────────────────────────────────────────────────────────────────────────────
# Tool definitions (in Anthropic's tool format)
# ─────────────────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "connect_to_spreadsheet",
        "description": "Connect to a Google Sheets spreadsheet. Call this first when a user provides a spreadsheet URL or ID. Returns basic info about the spreadsheet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url_or_id": {
                    "type": "string",
                    "description": "Google Sheets URL (e.g., https://docs.google.com/spreadsheets/d/ABC123/edit) or just the spreadsheet ID.",
                },
            },
            "required": ["url_or_id"],
        },
    },
    {
        "name": "get_spreadsheet_info",
        "description": "Get information about the currently connected spreadsheet including all sheet names, their IDs, and dimensions.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "inspect_sheet",
        "description": "Get a comprehensive view of a sheet's structure for analysis. Returns headers, sample data, sample formulas, and identifies which columns contain formulas vs static data. Use this to understand how a sheet is organized and what calculations it performs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab) to inspect.",
                },
                "sample_rows": {
                    "type": "integer",
                    "description": "Number of rows to sample (default 20). Increase for sheets with more data.",
                    "default": 20,
                },
            },
            "required": ["sheet_name"],
        },
    },
    {
        "name": "read_range",
        "description": "Read values from a range of cells. Returns the displayed/formatted values.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab) to read from.",
                },
                "range": {
                    "type": "string",
                    "description": "A1 notation range to read (e.g., 'A1:D10', 'A:A', '1:5').",
                },
            },
            "required": ["sheet_name", "range"],
        },
    },
    {
        "name": "read_formulas",
        "description": "Read formulas from a range of cells. Returns the formula text (e.g., '=SUM(A1:A10)') rather than computed values. Use this to understand how cells are calculated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab) to read from.",
                },
                "range": {
                    "type": "string",
                    "description": "A1 notation range to read (e.g., 'A1:D10').",
                },
            },
            "required": ["sheet_name", "range"],
        },
    },
    {
        "name": "write_range",
        "description": "Write values or formulas to a range of cells. Formulas should start with '=' and will be parsed. Values are written starting at the top-left cell of the range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab) to write to.",
                },
                "range": {
                    "type": "string",
                    "description": "A1 notation for where to start writing (e.g., 'A1', 'B5:D10').",
                },
                "values": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {},
                    },
                    "description": "2D array of values to write. Each inner array is a row. Formulas start with '='.",
                },
            },
            "required": ["sheet_name", "range", "values"],
        },
    },
    {
        "name": "append_rows",
        "description": "Append rows to the end of existing data in a sheet. Useful for adding new entries (employees, customers, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab) to append to.",
                },
                "values": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {},
                    },
                    "description": "2D array of rows to append. Each inner array is a row.",
                },
            },
            "required": ["sheet_name", "values"],
        },
    },
    {
        "name": "clear_range",
        "description": "Clear values from a range of cells. Keeps formatting intact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab).",
                },
                "range": {
                    "type": "string",
                    "description": "A1 notation range to clear (e.g., 'A1:D10').",
                },
            },
            "required": ["sheet_name", "range"],
        },
    },
    {
        "name": "format_range",
        "description": "Apply formatting to a range of cells (number format, bold, font).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab).",
                },
                "range": {
                    "type": "string",
                    "description": "A1 notation range to format (e.g., 'A1:D10').",
                },
                "number_format": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["TEXT", "NUMBER", "CURRENCY", "DATE", "PERCENT", "SCIENTIFIC"],
                            "description": "The type of number format.",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Format pattern (e.g., '$#,##0' for currency, '0.0%' for percent, 'M/d/yyyy' for dates).",
                        },
                    },
                    "description": "Number format to apply.",
                },
                "bold": {
                    "type": "boolean",
                    "description": "Whether to make text bold.",
                },
                "font_family": {
                    "type": "string",
                    "description": "Font family name (e.g., 'Roboto', 'Arial').",
                },
                "font_size": {
                    "type": "integer",
                    "description": "Font size in points.",
                },
            },
            "required": ["sheet_name", "range"],
        },
    },
    {
        "name": "set_freeze",
        "description": "Freeze rows and/or columns in a sheet. Frozen rows/columns stay visible when scrolling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet (tab).",
                },
                "rows": {
                    "type": "integer",
                    "description": "Number of rows to freeze from the top. Use 0 to unfreeze.",
                    "default": 0,
                },
                "columns": {
                    "type": "integer",
                    "description": "Number of columns to freeze from the left. Use 0 to unfreeze.",
                    "default": 0,
                },
            },
            "required": ["sheet_name"],
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Tool execution
# ─────────────────────────────────────────────────────────────────────────────

def execute_tool(client: SheetsClient, tool_name: str, tool_input: dict[str, Any]) -> Any:
    """Execute a tool by name with given inputs.

    Args:
        client: The SheetsClient instance.
        tool_name: Name of the tool to execute.
        tool_input: Dictionary of input parameters.

    Returns:
        The result of the tool execution.

    Raises:
        ValueError: If tool_name is not recognized.
    """
    match tool_name:
        case "connect_to_spreadsheet":
            return client.set_spreadsheet(tool_input["url_or_id"])

        case "get_spreadsheet_info":
            return client.get_spreadsheet_info()

        case "inspect_sheet":
            return client.inspect_sheet(
                sheet_name=tool_input["sheet_name"],
                sample_rows=tool_input.get("sample_rows", 20),
            )

        case "read_range":
            return client.read_range(
                sheet_name=tool_input["sheet_name"],
                range_spec=tool_input["range"],
            )

        case "read_formulas":
            return client.read_formulas(
                sheet_name=tool_input["sheet_name"],
                range_spec=tool_input["range"],
            )

        case "write_range":
            return client.write_range(
                sheet_name=tool_input["sheet_name"],
                range_spec=tool_input["range"],
                values=tool_input["values"],
            )

        case "append_rows":
            return client.append_rows(
                sheet_name=tool_input["sheet_name"],
                values=tool_input["values"],
            )

        case "clear_range":
            return client.clear_range(
                sheet_name=tool_input["sheet_name"],
                range_spec=tool_input["range"],
            )

        case "format_range":
            return client.format_range(
                sheet_name=tool_input["sheet_name"],
                range_spec=tool_input["range"],
                number_format=tool_input.get("number_format"),
                bold=tool_input.get("bold"),
                font_family=tool_input.get("font_family"),
                font_size=tool_input.get("font_size"),
            )

        case "set_freeze":
            return client.set_freeze(
                sheet_name=tool_input["sheet_name"],
                rows=tool_input.get("rows", 0),
                columns=tool_input.get("columns", 0),
            )

        case _:
            raise ValueError(f"Unknown tool: {tool_name}")
