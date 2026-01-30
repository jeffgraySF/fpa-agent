# FP&A Agent

Google Sheets automation for financial planning.

## Welcome Message
When a user starts a new conversation (their first message is a greeting like "hi", "hello", "hey", or they ask what the agent can do), respond with:

```
FP&A Agent - Google Sheets automation for financial planning

Available commands:
  /connect  - Connect to a spreadsheet
  /create   - Build a full FP&A model from input data
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

## Reconciliation Checks

After building or modifying a model, verify that key outputs tie to known input values. Run these checks whenever a change could affect cash, headcount, ARR, or revenue totals.

**Cash**: If a known cash balance exists (e.g., from a balance sheet), the model's Ending Cash for that month MUST equal the provided balance. Read the Ending Cash value and compare. If they don't match, trace the discrepancy.

**Headcount**: Total headcount in the model for recent months should match the number of active employees in the input data. Count employees with start dates before the month and no end date (or end date after the month). Note: rows with $0 total compensation (e.g., variable comp placeholders) are correctly excluded from HC count formulas that use `>0` checks.

**ARR**: Total ARR in the model should match the sum of active ARR records from the input data for any given month.

**Revenue**: If actual monthly revenue data exists (e.g., from a P&L), compare the model's revenue for those months to the actuals. Flag any discrepancies.

Report format:
```
## Reconciliation
- Cash ($[date]): Model $[X] vs. Input $[Y] — [MATCH / MISMATCH by $Z]
- Headcount ([month]): Model [N] vs. Input [M] — [MATCH / MISMATCH]
- ARR ([month]): Model $[X] vs. Input $[Y] — [MATCH / MISMATCH]
```

## When to Read Docs
- **Creating new sheets or sections**: Read `template_specs.md` for standard layouts, row mappings, and formula patterns
- **Discretionary decisions**: Read `template_specs.md` when you have flexibility on structure
- **After structural changes**: Update `INSTRUCTIONS.md` and `template_specs.md`

## When to Update README
After making changes, check if `README.md` needs updating. Update it when:
- A new command is added or an existing command's purpose changes
- The setup process changes (new dependencies, new config steps)
- The project structure changes (new directories, renamed files)
- User-facing behavior changes significantly

Don't update README for internal-only changes (formula tweaks, prompt wording, bug fixes).
