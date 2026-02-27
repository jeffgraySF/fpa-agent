---
model: sonnet
---
# Modify Sheet

Make structural or formula changes to the spreadsheet.

## Arguments

$ARGUMENTS - Description of the modification to make (natural language)

Examples:
- `/modify add a new department row for "Product" below Engineering`
- `/modify fix the COGS formula in row 24 to exclude header`
- `/modify add Q3 2026 column to Monthly Summary`
- `/modify update all SUMIF formulas to use date matching instead of column refs`

## Instructions

### 1. Understand the Request

Parse what the user wants:
- **Add**: New rows, columns, sections, or sheets
- **Update**: Change existing formulas or values
- **Fix**: Correct errors or broken references
- **Delete**: Remove rows, columns, or data (requires explicit confirmation)
- **Restructure**: Move or reorganize existing content

### 2. Scope Check

Run this **before reading the sheet**. The goal is to catch vague requests on large sheets before burning 10+ API calls on discovery.

**Step 1** — Get sheet list and resolve the target sheet (one fast call, cached):
```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id>')
info = client.get_spreadsheet_info()
```

If the user named a sheet explicitly, use it — but warn if the name looks archived (contains OLD, ORIG, BACKUP, COPY, ARCHIVE).

If the sheet must be inferred from the request, filter the sheet list:
- Find candidates that match the request's intent (e.g., "Monthly Summary" for a summary-type change)
- Exclude archived sheets: names containing `OLD`, `ORIG`, `BACKUP`, `COPY`, `ARCHIVE`, or a lower version when a higher one exists
- **1 candidate** → proceed; **2+ candidates** → ask before reading:
  ```
  I see multiple candidate sheets — which should I use?
    Summary v2      (1004 rows × 36 cols)  ← likely current
    Summary ORIG    (1001 rows × 37 cols)
  ```

```python
sheet = next((s for s in info["sheets"] if s["name"] == "<resolved_sheet_name>"), None)
data_cells = sheet["row_count"] * min(sheet["column_count"], 35) if sheet else 0
```

**Step 2** — Classify the request:

| Request type | Examples | Check needed? |
|---|---|---|
| Specific cell or range | "fix B5", "update C12:C20", "row 45" | No — proceed directly |
| Named row with clear label | "the Enterprise CAC row", "the date header row" | No — proceed directly |
| Section-level, sheet is small (≤1,000 data cells) | any | No — proceed directly |
| Section-level, sheet is large (>1,000 data cells) | "fix the Enterprise formulas", "update the revenue section" | **Yes — ask** |
| Whole-sheet or vague | "fix the formulas", "clean up this sheet" | **Yes — ask** |
| Multi-sheet cascade | any change that touches 3+ sheets | **Yes — ask** |

**Step 3** — If a check is needed, respond before reading anything:

```
To make this change efficiently, it helps to know:
  - Which row(s) or range? (e.g., "row 45" or "B45:AE45")
  - Do you know the current formula, or should I look it up? (adds ~10s)
  - Which sheet, if not [inferred sheet]?

Or I can inspect first and propose a plan — that takes ~20–30s total.

Narrow the scope, or proceed with full discovery?
```

If the request is already specific, skip this step entirely and go straight to reading.

### 3. Read the Sheet Before Modifying

CRITICAL: Read ALL values and formulas for the entire sheet, not just the rows you plan to change. `write_range` overwrites whatever is in the target cells — if you only read rows 14-16 and write to rows 14-21, you will silently destroy rows 17-21 without knowing what was there.

```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id>')
_ = client.read_range('Sheet', 'A1:A1')  # required init workaround
values = client.read_range('Sheet', 'A1:Z100')
formulas = client.read_formulas('Sheet', 'A1:Z100')
```

Then understand:
- The full layout — every row with content, including rows below your target
- Current formulas in the target range and adjacent rows
- Cross-sheet references pointing TO this area (what will break?)
- Cross-sheet references FROM this area (what patterns to follow?)

For row additions, also read:
- Formulas in adjacent rows to understand the pattern
- Column headers to understand what each column needs

### 4. Plan the Changes

Before executing, create a clear plan. **Show the exact formulas that will be written** — not intent summaries. The user needs to be able to spot errors before they're committed.

```
## Modification Plan

**Target**: [Sheet]![Range]
**Action**: [Add/Update/Fix/Delete]

**Current state**:
[What exists now — show the actual current formula or value for each cell being changed]

**Proposed changes**:
| Cell | Before | After |
|------|--------|-------|
| B10  | =SUM(B3:B8) | =SUM(B3:B9) |
| C10  | =SUM(C3:C8) | =SUM(C3:C9) |
| ...  | ...         | ...         |

**Cross-sheet impact**:
- [Any sheets that reference this area]
- [Any formulas that need updating elsewhere]

**Baseline values to preserve** (capture BEFORE modifying):
- [Key calculated values that should remain unchanged, e.g., "Ending Cash Balance: Q4'25=$5.9M, Q1'26=$5.7M"]
- [These will be verified after modification]
```

#### Approval Gate

After presenting the plan, decide whether to proceed immediately or wait:

- **Specific / targeted** (single cell, named row, small fix): proceed directly — no pause needed.
- **Section-level on a large sheet, vague request, or multi-sheet change**: stop after presenting the plan and ask:

  ```
  Ready to execute [N] changes across [range]. Proceed?
  ```

  Wait for the user to confirm (e.g. "yes", "go", "looks good") before writing anything. If the user asks to skip or modify part of the plan, adjust and re-present before executing.

### 5. Common Modification Patterns

**Adding rows to a section (e.g., new department, splitting a line item)**:
- Use `insertDimension` via `batch_update()` to insert blank rows first — this pushes existing rows down and preserves their formulas. Never overwrite rows below the insertion point.
```python
client.batch_update([{
    "insertDimension": {
        "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": row_0idx, "endIndex": row_0idx + count},
        "inheritFromBefore": False
    }
}])
```
- Then write formulas into the new blank rows
- Copy formula patterns from adjacent row of same type
- Update row references in formulas appropriately
- Ensure subtotals/totals include the new row
- Check if any SUMIF/SUMIFS ranges need expanding

**Adding a new column (e.g., new month)**:
- Copy formulas from the previous column
- Update any hardcoded date references
- Verify column headers are correct
- Check if any cross-sheet references need the new column

**Removing/restructuring columns**:
- CRITICAL: When moving formulas to new column positions, ALL column references must be updated
  - Header refs: `E$2` → `B$2` if formula moves from column E to column B
  - Range refs: `=SUM(E10:E12)` → `=SUM(B10:B12)`
  - Cross-refs within formulas: `=G7` → `=C7`
- Formulas reference their original columns - they don't auto-adjust when copied as values
- Use regex or find/replace to update all column letters systematically

**Fixing formulas**:
- Identify the root cause (wrong range, wrong reference, typo)
- Check if the same error exists in other cells (fill-right pattern)
- Fix all instances, not just the one reported

**Updating formula patterns**:
- Identify all cells using the old pattern
- Test the new formula on one cell first
- Apply to all cells once verified

### 6. Execute Changes

Use SheetsClient methods:
- `write_range()` for updating values/formulas
- `batch_update()` for structural changes (insert rows/columns)
- `clear_range()` for removing data (preserves formatting)

Write formulas as strings starting with `=`:
```python
client.write_range('Sheet', 'B10', [['=SUM(B3:B9)']])
```

**Data Type Rules** — never write formatted strings:
- **Dates**: Always `=DATE(year,month,day)`. Never text like "8/1/25" or "2025-08-01" — text dates break formula comparisons.
- **Currency**: Numeric values (175000), not formatted strings ("$175,000")
- **Percentages**: Decimals (0.15), not text ("15%")
- **Date headers**: Reference the master date row rather than writing standalone date values.

**Number Formatting** — apply formats after writing so output is readable:
- Currency cells (revenue, expenses, cash, salaries, ARR): `$#,##0`
- Percentage cells (margins, growth rates, NRR): `0.0%`
- Date cells (headers, start/end dates): `M/D/YYYY`
- Integer cells (headcount, customer counts): `#,##0`
- Header rows: Bold

```python
client.batch_update([{
    "repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }
}])
```

**Test Before Bulk Write** — for complex formulas (proration, SUMPRODUCT, nested IF):
1. Write the formula to a single cell (first data row, first month column)
2. Read back the calculated value
3. Verify it is not an error (#ERROR!, #REF!, #VALUE!, etc.)
4. Verify the value makes sense (e.g., monthly salary should be ~1/12 of annual)
5. Only then apply to all remaining rows/columns

**Column letter generation**: When building formulas programmatically across many columns, use `client._col_index_to_letter(index)` (0-based) to convert column indices to letters. Do NOT use `chr()` arithmetic — it breaks past column Z (index 25) because `chr(90+1)` is `[`, not `AA`.

### 7. Verify After Changes

After making changes:

**Check ALL rows, not just a sample:**
- Different rows may have different formula patterns
- A fix that works for row 10 may not work for row 13 if formulas differ
- Scan every row with formulas to ensure none show $0, blank, or errors unexpectedly

**Verify calculated values match expected:**
- Capture key values BEFORE making changes (e.g., Ending Cash Balance)
- Compare AFTER to ensure values are unchanged (unless change was intentional)
- If a value that shouldn't change shows $0 or different amount, formula references are likely wrong

**Check for errors:**
- Scan all cells for #REF!, #VALUE!, #NAME?, #DIV/0!, #N/A
- A #DIV/0! often indicates a formula references an empty/zero cell due to wrong column

**Verify formatting:**
- When deleting/moving columns, formatting (colors, shading, borders) shifts with data
- Clear formatting from deleted column positions
- Update formatting on remaining columns if needed (e.g., remove shading from quarterly columns that inherited annual column formatting)

### 8. Post-Modification Integrity Checks

After verification, run a focused integrity check on the modified sheet. This is NOT a full audit — skip FP&A assessments, missing KPI suggestions, and industry benchmark analysis. Only check for issues that indicate the modification broke something:

1. **Error scan**: Scan all cells in the modified sheet for #REF!, #VALUE!, #NAME?, #DIV/0!, #ERROR!, #N/A
2. **Formula standard violations introduced by this change**: Check only the rows/cells you touched for hardcoded labels, whole-column refs, or missing formulas
3. **Cross-sheet breakage**: If your change shifted rows or renamed things, verify that other sheets referencing the modified area still resolve correctly

Do NOT:
- Suggest new KPIs, metrics, or rows to add
- Evaluate completeness, clarity, or industry standards
- Flag pre-existing issues unrelated to the change
- Run `/audit` (the user can run that separately if they want a full review)

### 9. Reconciliation

After making changes, verify key outputs still tie to known input values.

**Tier 1 — Skip**: Cosmetic changes (formatting, bold, colors, column widths, labels that don't affect formulas).

**Tier 2 — Spot Check**: Single-sheet formula fix or value update. Read **one cell** per relevant check and compare to the known baseline. Costs 1-2 API reads total.

**Tier 3 — Full Reconciliation**: Structural changes (add/remove rows/columns), bulk formula rewrites, or multi-sheet changes. Run all relevant checks across multiple months.

**Which checks to run** — trace what the modified sheet feeds into:
1. Run `/inspect [modified sheet] refs` to find which other sheets reference it
2. Follow the chain downstream
3. Map impact to checks:
   - Feeds into ARR/MRR calculations → check ARR
   - Feeds into revenue or COGS → check GP
   - Feeds into cash balances → check Ending Cash
4. If the modified sheet is a downstream endpoint (nothing references it), skip reconciliation

| Sheet | Typically affects |
|---|---|
| ARR | ARR, Ending Cash |
| Revenue / Services | GP, Ending Cash |
| COGS / Cost of Revenue | GP, Ending Cash |
| OpEx Assumptions | Ending Cash |
| Costs by Department | Ending Cash |
| Cash Flow | Ending Cash |
| Monthly / Quarterly Summary | Nothing (endpoint) |

**Check definitions** — find the relevant cells by inspecting the actual sheet; don't assume row numbers:
- **ARR**: Total ARR row vs. sum of active ARR records from input data for the same month.
- **GP**: Gross profit row (Revenue − COGS). Compare to actuals if they exist; otherwise verify formula and margin % match model assumptions.
- **Ending Cash**: Compare to a known balance (from balance sheet or user-provided). If mismatch, trace through the dependency chain.

**Report format**:
```
## Reconciliation ([tier])
- ARR ([month]): Model $[X] vs. Input $[Y] — [MATCH / MISMATCH by $Z]
- GP ([month]): Model $[X] ($[margin]% margin) vs. Expected $[Y] — [MATCH / MISMATCH by $Z]
- Ending Cash ([date]): Model $[X] vs. Input $[Y] — [MATCH / MISMATCH by $Z]
```

### 10. Output Format

```
## Modification Complete

**Sheet**: [name]
**Action**: [what was done]

**Changes made**:
| Location | Before | After |
|----------|--------|-------|
| B10 | =SUM(B3:B8) | =SUM(B3:B9) |
| ... | ... | ... |

**Verification**:
- [x] No errors introduced
- [x] Formulas calculating correctly
- [x] Cross-sheet references intact

**Integrity checks**: [errors found and fixed, or "No errors introduced ✓"]

**Reconciliation**: [if applicable — summary from reconciliation checks, or "N/A — cosmetic change only"]

**Notes**:
[Any follow-up actions needed, e.g., "You may want to update Quarterly Summary to include this new row"]
```

### Safety Rules

1. **Always confirm destructive changes** (delete, clear, overwrite) before executing
2. **Never modify without reading first** - understand what you're changing
3. **Preserve existing patterns** - match the style of surrounding formulas
4. **Check dependencies** - what else references this area?
5. **Test first** - for bulk changes, apply to one cell and verify before applying to all
6. **Report what changed** - always show before/after for transparency
