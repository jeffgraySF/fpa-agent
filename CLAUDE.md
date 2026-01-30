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

## Data Type Rules

When writing data to sheets, enforce proper types. Never write formatted strings.

- **Dates**: Always use `=DATE(year,month,day)` formulas. Never write text like "8/1/25" or "2025-08-01" — text dates break date comparisons in formulas.
- **Currency**: Write as numeric values (175000), not formatted strings ("$175,000")
- **Percentages**: Write as decimals (0.15), not text ("15%")
- **Date headers**: All sheets reference `='Monthly Summary'!{col}$2`. Never write standalone date values in other sheets.

## Number Formatting

When writing data to sheets, apply number formats so output is readable without manual formatting:

- **Currency cells** (revenue, expenses, cash, salaries, ARR): `$#,##0`
- **Percentage cells** (margins, growth rates, NRR): `0.0%`
- **Date cells** (headers, start/end dates): `M/D/YYYY`
- **Integer cells** (headcount, customer counts): `#,##0`
- **Header rows**: Bold

```python
client.batch_update([{
    "repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }
}])
```

## Model Structure

Standard FP&A model sheets and their dependencies. Use this to understand downstream impact when modifying, auditing, or explaining formulas.

```
Headcount Input ──┐
                   ├─→ Headcount Summary ──┐
ARR ───────────────┤                       ├─→ Costs by Department ──┐
                   ├─→ ARR Summary ────────┤                        ├─→ Monthly Summary ─→ Quarterly Summary
                   │                       │                        │
                   └─→ OpEx Assumptions ───┘                        │
                                                                    │
                                           Cash Flow ───────────────┘
```

**Key cross-sheet relationships:**
- Headcount Summary pulls from Headcount Input (SUMPRODUCT/SUMIF by department)
- ARR Summary aggregates ARR (SUM, COUNTIF by month)
- Costs by Department combines Headcount Summary + OpEx Assumptions
- Cash Flow uses ARR Summary (collections) + Costs by Department (cash out)
- Monthly Summary wires together ARR Summary, Costs by Department, and Cash Flow
- Quarterly Summary aggregates Monthly Summary via SUMIF on quarter labels

## Test Before Bulk Write

When writing complex formulas (proration, SUMPRODUCT, nested IF), test on one cell first:

1. Write the formula to a single cell (first data row, first month column)
2. Read back the calculated value
3. Verify it is not an error (#ERROR!, #REF!, #VALUE!, etc.)
4. Verify the value makes sense (e.g., monthly salary should be ~1/12 of annual)
5. Only then apply to all remaining rows/columns

This prevents writing hundreds of broken formulas that cascade errors through downstream sheets.

## Audit Checklist
1. No quoted department names ("G&A", "Sales", etc.)
2. Ranges skip headers ($B$2:$B$100)
3. Formulas copy/paste correctly
4. No #REF!, #VALUE!, #ERROR!

## Reconciliation Checks

After any change to a model, run reconciliation checks to verify key outputs still tie to known input values. Use the tiered approach below to balance thoroughness with token cost.

### Tier 1 — Skip

No reconciliation needed for cosmetic changes: formatting, bold, colors, column widths, labels that don't affect formulas.

### Tier 2 — Spot Check

For single-sheet formula fixes or value updates. Read **one cell** per relevant check and compare to the known baseline. Costs 1-2 API reads total.

Example: after fixing a formula in Costs by Department, read Ending Cash for Dec 2025 and compare to $5.91M. If it matches, done.

### Tier 3 — Full Reconciliation

For structural changes (add/remove rows/columns), bulk formula rewrites, or changes that touch multiple sheets. Run all relevant checks across multiple months.

### Which Checks to Run

Use the Model Structure dependency graph to scope checks to what's actually affected:

| Modified sheet | Check HC | Check ARR | Check Cash | Check Revenue |
|---|---|---|---|---|
| Headcount Input | yes | | yes | |
| ARR | | yes | yes | |
| Services | | | yes | yes |
| OpEx Assumptions | | | yes | |
| Costs by Department | | | yes | |
| Cash Flow | | | yes | |
| Headcount Summary | yes | | yes | |
| ARR Summary | | yes | yes | |
| Monthly / Quarterly Summary | | | | |

Changes to Monthly or Quarterly Summary are downstream endpoints — nothing to reconcile.

### Check Definitions

**Cash**: If a known cash balance exists (e.g., from a balance sheet), the model's Ending Cash for that month MUST equal the provided balance. Read the Ending Cash value and compare. If they don't match, trace the discrepancy.

**Headcount**: Total headcount in the model for recent months should match the number of active employees in the input data. Count employees with start dates before the month and no end date (or end date after the month). Note: rows with $0 total compensation (e.g., variable comp placeholders) are correctly excluded from HC count formulas that use `>0` checks.

**ARR**: Total ARR in the model should match the sum of active ARR records from the input data for any given month.

**Revenue**: If actual monthly revenue data exists (e.g., from a P&L), compare the model's revenue for those months to the actuals. Flag any discrepancies.

### Report Format
```
## Reconciliation ([tier])
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
