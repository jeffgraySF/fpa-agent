# FP&A Agent

Google Sheets automation for financial planning. Read INSTRUCTIONS.md for formula standards and template_specs.md for sheet structure.

## Quick Reference
- Spreadsheet: https://docs.google.com/spreadsheets/d/1yYJlj3KNXtln6DzsVguwadnQPD5KIOPc7eWMl8zHAVU
- Credentials: `~/.fpa-agent/token.json` (OAuth token), `./credentials.json` (client ID)
- Python env: `.venv` with google-api-python-client

## Reading Sheets
```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id_or_url>')
_ = client.read_range('Sheet', 'A1:A1')  # init _sheets (workaround)
data = client.read_range('Sheet', 'A1:Z50')
```

## Key Sheets
- Monthly Summary: P&L, ARR waterfall, cash
- Costs by Department: OpEx + COGS breakdown (CS split 40% to COGS)
- OpEx Assumptions: Scaling rules, CS COGS % in E4

## Documentation
After making structural changes to the spreadsheet, update:
- `INSTRUCTIONS.md` - Formula standards, sheet dependencies, key formulas
- `template_specs.md` - Row/column mappings, section structures, test data assumptions
