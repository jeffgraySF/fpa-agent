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

## Skill Auto-Invocation
When the user asks to make changes to a sheet (write formulas, update data, fix errors, add rows/columns), automatically invoke the `/modify` skill before proceeding — don't wait for the user to ask. Similarly, invoke `/inspect` when exploring structure and `/audit` when checking for errors.

## Quick Reference
- Credentials: `~/.fpa-agent/token.json` (OAuth), `./credentials.json` (client ID)
- Python env: `.venv` with google-api-python-client
- Use `/connect <url>` to connect to a spreadsheet

## Reading Sheets
```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id_or_url>')
_ = client.read_range('Sheet', 'A1:A1')  # init workaround
data = client.read_range('Sheet', 'A1:Z50')
```

## Formula Standards
- **No hardcoded labels**: Use `$A{row}` not `"G&A"` or `"Sales"` — reference the row label cell
- **Skip headers in ranges**: Use `$B$2:$B$100` not `$B:$B` — avoid including header rows in calculations
- **Dates**: Always real dates (`=DATE()`), never text strings. Find the date source-of-truth row by inspecting the actual sheet — don't assume a specific row number or sheet name
- **Department ref**: `$A{row}` (absolute col, relative row)
- **Month ref**: `{col}$1` or `{col}$2` (relative col, absolute row) — use whichever row contains date headers in the actual sheet
- **Discover before assuming**: Always run `/inspect` to find the actual date row, label column, and formula patterns before writing. Different models may use different layouts.

## Data Type Rules

When writing data to sheets, enforce proper types. Never write formatted strings.

- **Dates**: Always use `=DATE(year,month,day)` formulas. Never write text like "8/1/25" or "2025-08-01" — text dates break date comparisons in formulas.
- **Currency**: Write as numeric values (175000), not formatted strings ("$175,000")
- **Percentages**: Write as decimals (0.15), not text ("15%")
- **Date headers**: If the model has a master date row, all other sheets should reference it rather than writing standalone date values. Find the master date sheet by inspecting cross-sheet references.

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

### Discovering the actual structure

Every model is different. Before modifying, auditing, or explaining formulas, discover the actual dependency graph:

1. List all sheets (`get_spreadsheet_info()`)
2. Run `/inspect [sheet] refs` on key sheets to find cross-sheet references
3. Build a mental model of what feeds what

Don't assume sheet names, row numbers, or column positions. Read first.

### Standard template (for reference only)

When `/create` builds a new model, it uses this default layout. Existing models may differ.

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

**Typical cross-sheet patterns** (names and positions vary):
- A headcount summary sheet pulls from a headcount detail/input sheet
- An ARR/revenue summary aggregates from a deal-level or booking-level sheet
- A costs/expenses sheet combines headcount costs + operating expenses
- A cash flow sheet uses revenue (collections) + expenses (cash out)
- An executive summary wires together revenue, expenses, and cash
- A quarterly view aggregates from the monthly view

## Test Before Bulk Write

When writing complex formulas (proration, SUMPRODUCT, nested IF), test on one cell first:

1. Write the formula to a single cell (first data row, first month column)
2. Read back the calculated value
3. Verify it is not an error (#ERROR!, #REF!, #VALUE!, etc.)
4. Verify the value makes sense (e.g., monthly salary should be ~1/12 of annual)
5. Only then apply to all remaining rows/columns

This prevents writing hundreds of broken formulas that cascade errors through downstream sheets.

## Audit Checklist
1. No hardcoded labels in formulas — reference the label cell instead of quoting strings
2. Ranges skip headers (e.g., `$B$2:$B$100` not `$B:$B`)
3. Formulas copy/paste correctly across rows and columns
4. No #REF!, #VALUE!, #ERROR!, #DIV/0!, #N/A

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

Determine which checks are relevant by tracing what the modified sheet feeds into. Don't rely on sheet names — use the actual cross-sheet references.

**How to determine scope:**
1. Run `/inspect [modified sheet] refs` to find which other sheets reference it
2. Follow the chain downstream: if Sheet A feeds Sheet B which feeds Cash Flow, a change to A affects cash
3. Map the downstream impact to check categories:
   - Feeds into anything that calculates **headcount totals** → check HC
   - Feeds into anything that calculates **ARR/MRR** → check ARR
   - Feeds into anything that calculates **cash balances** → check Cash
   - Feeds into anything that calculates **revenue** → check Revenue
4. If the modified sheet is a downstream endpoint (nothing references it), skip reconciliation

**Standard model example** (for reference — actual models may differ):

| Sheet | Typically affects |
|---|---|
| Headcount Input | HC, Cash |
| ARR | ARR, Cash |
| Services | Revenue, Cash |
| OpEx Assumptions | Cash |
| Costs by Department | Cash |
| Cash Flow | Cash |
| Monthly / Quarterly Summary | Nothing (endpoint) |

### Check Definitions

Each check compares a model output to a known input value. To run a check, first find the relevant cells by inspecting the actual sheet structure — don't assume specific row numbers or sheet names.

**Cash**: Find the sheet/row that calculates ending cash balance. If a known cash balance exists (e.g., from a balance sheet or user-provided value), compare the model's value for that date. If they don't match, trace the discrepancy through the dependency chain.

**Headcount**: Find the sheet/row that calculates total headcount. Compare to the count of active employees in the input data for the same period. "Active" means: start date before the period end, and no end date (or end date after the period). Note: the model's HC formula may exclude certain rows (e.g., $0 comp placeholders) — understand how the formula counts before flagging a mismatch.

**ARR**: Find the sheet/row that calculates total ARR. Compare to the sum of active ARR records from the input data for the same month.

**Revenue**: If actual revenue data exists (e.g., from a P&L or accounting system), find the model's revenue row and compare to actuals for overlapping periods.

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
