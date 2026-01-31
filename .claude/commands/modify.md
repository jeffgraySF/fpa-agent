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

### 2. Read the ENTIRE Sheet Before Modifying

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

### 3. Plan the Changes

Before executing, create a clear plan:

```
## Modification Plan

**Target**: [Sheet]![Range]
**Action**: [Add/Update/Fix/Delete]

**Current state**:
[What exists now]

**Proposed changes**:
1. [Specific change 1]
2. [Specific change 2]

**Formulas to apply**:
- Column B: [formula]
- Column C: [formula]
...

**Cross-sheet impact**:
- [Any sheets that reference this area]
- [Any formulas that need updating elsewhere]

**Baseline values to preserve** (capture BEFORE modifying):
- [Key calculated values that should remain unchanged, e.g., "Ending Cash Balance: Q4'25=$5.9M, Q1'26=$5.7M"]
- [These will be verified after modification]
```

### 4. Common Modification Patterns

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

### 5. Execute Changes

Use SheetsClient methods:
- `write_range()` for updating values/formulas
- `batch_update()` for structural changes (insert rows/columns)
- `clear_range()` for removing data (preserves formatting)

Write formulas as strings starting with `=`:
```python
client.write_range('Sheet', 'B10', [['=SUM(B3:B9)']])
```

Follow the **Data Type Rules** and **Number Formatting** standards from CLAUDE.md when writing values. For bulk formula changes, follow **Test Before Bulk Write** from CLAUDE.md.

**Column letter generation**: When building formulas programmatically across many columns, use `client._col_index_to_letter(index)` (0-based) to convert column indices to letters. Do NOT use `chr()` arithmetic — it breaks past column Z (index 25) because `chr(90+1)` is `[`, not `AA`.

### 6. Verify After Changes

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

### 7. Post-Modification Integrity Checks

After verification, run a focused integrity check on the modified sheet. This is NOT a full audit — skip FP&A assessments, missing KPI suggestions, and industry benchmark analysis. Only check for issues that indicate the modification broke something:

1. **Error scan**: Scan all cells in the modified sheet for #REF!, #VALUE!, #NAME?, #DIV/0!, #ERROR!, #N/A
2. **Formula standard violations introduced by this change**: Check only the rows/cells you touched for hardcoded labels, whole-column refs, or missing formulas
3. **Cross-sheet breakage**: If your change shifted rows or renamed things, verify that other sheets referencing the modified area still resolve correctly

Do NOT:
- Suggest new KPIs, metrics, or rows to add
- Evaluate completeness, clarity, or industry standards
- Flag pre-existing issues unrelated to the change
- Run `/audit` (the user can run that separately if they want a full review)

### 8. Reconciliation

Run the **Reconciliation Checks** from CLAUDE.md using the appropriate tier:

- **Tier 1 (skip)**: Cosmetic changes — formatting, labels, column headers
- **Tier 2 (spot check)**: Single-sheet formula fix or value update — read one downstream cell per relevant check
- **Tier 3 (full)**: Structural changes (add/remove rows/columns), bulk formula rewrites, multi-sheet changes

Use the dependency table in CLAUDE.md to determine which checks (HC, ARR, Cash, Revenue) apply based on the sheet you modified.

### 9. Output Format

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
