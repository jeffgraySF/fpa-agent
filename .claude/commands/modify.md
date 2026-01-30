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

### 2. Read Before Modifying

ALWAYS read the affected area first:
- Current structure and formulas in the target range
- Adjacent rows/columns that may need to stay consistent
- Cross-sheet references pointing TO this area (what will break?)
- Cross-sheet references FROM this area (what patterns to follow?)

For row additions, also read:
- The row above and below the insertion point
- Formulas in those rows to understand the pattern
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

**Adding a new row (e.g., new department)**:
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

### 7. Post-Modification Audit

After verification, run `/audit` on the modified sheet to check for formula standard violations and FP&A best practices. This catches issues beyond simple errors — hardcoded labels, fragile references, whole-column ranges, and missing calculations that the basic verification step won't find.

- Run `/audit [sheet name]` on the sheet you modified
- If `/audit` finds issues introduced by your changes, fix them immediately
- If `/audit` finds pre-existing issues unrelated to your changes, report them in the Notes section but do not fix them (the user didn't ask for that)
- Include the audit result summary in your output

### 8. Output Format

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

**Audit result**: [summary from /audit — "All checks passed" or list of issues found and whether they were fixed]

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
