---
model: haiku
---
# Connect to Spreadsheet

Switch to a different Google Spreadsheet.

## Arguments

$ARGUMENTS - Google Sheets URL or spreadsheet ID

## Instructions

1. Extract the URL or ID from `$ARGUMENTS`
2. Run this Python to connect and get spreadsheet info:

```python
from src.sheets.client import SheetsClient
client = SheetsClient()
info = client.set_spreadsheet('$ARGUMENTS')
print(info)
```

Run with `.venv/bin/python` from the project root.

3. List all sheets with row/column counts from `info['sheets']`
4. Confirm connection successful
