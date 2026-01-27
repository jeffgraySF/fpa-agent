# FP&A Agent

Google Sheets automation for financial planning.

## Welcome Message
When a user starts a new conversation (their first message is a greeting like "hi", "hello", "hey", or they ask what the agent can do), respond with:

```
FP&A Agent - Google Sheets automation for financial planning

Available commands:
  /connect  - Connect to a spreadsheet
  /inspect  - Inspect sheet structure and data
  /modify   - Modify sheet formulas or data
  /explain  - Explain a formula
  /audit    - Audit sheet for errors or issues

Type a command or describe what you'd like to do.
```

## Quick Reference
- Spreadsheet: https://docs.google.com/spreadsheets/d/1yYJlj3KNXtln6DzsVguwadnQPD5KIOPc7eWMl8zHAVU
- Credentials: `~/.fpa-agent/token.json` (OAuth), `./credentials.json` (client ID)
- Python env: `.venv` with google-api-python-client

## Reading Sheets
```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id_or_url>')
_ = client.read_range('Sheet', 'A1:A1')  # init workaround
data = client.read_range('Sheet', 'A1:Z50')
```

## Sheet Structure
| Sheet | Purpose | Key Rows |
|-------|---------|----------|
| Monthly Summary | P&L, ARR waterfall, cash | Revenue r10, COGS r11, OpEx r16-21, Cash r34-35 |
| Quarterly Summary | Same as Monthly, aggregated | SUMIF on quarter labels |
| Headcount Input | Employee data + monthly costs | Cols A-I metadata, J+ monthly |
| Headcount Summary | Costs by dept | HC r4-10, Salary r13-19, Total r40-46 |
| ARR | Customer data | Start/Churn dates, monthly ARR helper |
| ARR Summary | MRR, ARR, customer counts | MRR r4, New/Expansion/Churned r13-15 |
| OpEx Assumptions | Non-HC expenses, scaling rules | CS COGS % in E4 (40%) |
| Costs by Department | OpEx + COGS breakdown | Dept sections, Total OpEx r41, COGS r43-46 |
| Cash Flow | Collections + payments | Begin r3, Burn r7, End r13 |

## Formula Standards
- **No hardcoded labels**: Use `$A{row}` not `"G&A"` or `"Sales"`
- **Skip headers in ranges**: Use `$B$2:$B$100` not `$B:$B`
- **Dates**: Real dates, not text. Monthly Summary row 2 is source of truth
- **Department ref**: `$A{row}` (absolute col, relative row)
- **Month ref**: `{col}$1` (relative col, absolute row)

## Key Formulas
```
Quarter label:     =IF(C2="","","Q"&ROUNDUP(MONTH(C2)/3,0)&"-"&RIGHT(YEAR(C2),2))
ARR helper:        =IF(AND($C2<=G$1,OR($E2="",$E2>G$1)),$D2,0)
Quarterly SUM:     =SUMIF('Monthly Summary'!$C$1:$Z$1,C$1,'Monthly Summary'!$C{row}:$Z{row})
CS COGS split:     =CS_Subtotal * 'OpEx Assumptions'!$E$4
Allocated OpEx:    =(Dept HC / Total HC) * SUMIF('OpEx Assumptions'!$A:$A,"Overall",month_col)
```

## Audit Checklist
1. No quoted department names ("G&A", "Sales", etc.)
2. Ranges skip headers ($B$2:$B$100)
3. Formulas copy/paste correctly
4. No #REF!, #VALUE!, #ERROR!

## Documentation
After structural changes, update `INSTRUCTIONS.md` and `template_specs.md`.
