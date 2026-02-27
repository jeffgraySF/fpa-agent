---
model: sonnet
---
# Full Formula Scan

Scan an entire sheet for formula errors and anomalies — checks every cell, not just a sample.

## Arguments

$ARGUMENTS - Sheet name (required)

Examples:
- `/scan Revenue Build`
- `/scan Summary`
- `/scan Cost of Revenue`

## Instructions

First, get sheet dimensions and set expectations (one fast cached call):

```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id>')
info = client.get_spreadsheet_info()
sheet = next(s for s in info["sheets"] if s["name"] == "<sheet_name>")
rows = sheet["row_count"]
cols = min(sheet["column_count"], 52)
print(f"Scanning {sheet['name']}: {rows} rows × {cols} cols — reading all cells now...")
```

Then run the scan (2 API calls for the full sheet — no blocking check needed since the user chose this):

```python
import sys
sys.path.insert(0, '.')
from src.analysis.scan import scan_sheet

results = scan_sheet('<sheet_name>', client)
```

Replace `<spreadsheet_id>` with the active spreadsheet ID and `<sheet_name>` with the argument.

### Output Format

```
Scan: Revenue Build (96 rows × 35 cols)

Errors (0): None ✓

Static Values in Formula Rows (2):
  C45  [EHR AI — CAC]        Static "450" between formula columns D45–AE45
  M22  [Consumer AI — CAC]   Static "0" between formula columns N22–AE22

Formula Pattern Breaks (1):
  Q15  [Consumer PGx — Revenue]   Formula differs from row pattern
    Actual:   =P15*1.04
    Expected pattern: =SUMPRODUCT(CELL,CELL)

Summary: 3 anomalies in 96 rows × 35 cols
```

If no anomalies found:
```
Scan: Revenue Build (96 rows × 35 cols)
All formulas look clean ✓  (96 rows × 35 cols scanned, 0 anomalies)
```

For each anomaly, explain what it likely means (e.g. "this may be an overwritten formula" or "this column may have been manually adjusted").
