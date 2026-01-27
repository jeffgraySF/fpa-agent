# Inspect Sheet

Analyze the structure of a sheet in the active spreadsheet.

## Instructions

1. Use SheetsClient to connect to the spreadsheet in CLAUDE.md
2. Read the first 30 rows of the specified sheet (values + formulas)
3. Identify:
   - Section headers (bold text in column A)
   - Which columns contain formulas vs static data
   - Cross-sheet references
   - Row labels and their purpose
4. Summarize the structure concisely

## Arguments

$ARGUMENTS - Sheet name to inspect (e.g., "Monthly Summary", "Costs by Department")

If no argument provided, list all sheets and ask which one to inspect.
