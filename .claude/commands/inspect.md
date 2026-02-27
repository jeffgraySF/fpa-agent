---
model: sonnet
---
# Inspect Sheet

Analyze the structure of a sheet in the active spreadsheet.

## Arguments

$ARGUMENTS - Sheet name and optional focus (natural language or flags)

Examples:
- `/inspect Monthly Summary` - Full structure analysis
- `/inspect Monthly Summary errors` - Find errors only
- `/inspect Monthly Summary formulas` - Focus on formula patterns
- `/inspect Monthly Summary refs` - Cross-sheet references only
- `/inspect Monthly Summary rows 15-25` - Inspect specific rows
- `/inspect Monthly Summary trace B15` - Trace where B15's value comes from
- `/inspect Monthly Summary trace B15 dependents` - What depends on B15

## If No Arguments Provided

List sheets, separating active from archived:
```
Active sheets:
  Revenue Build        (996 rows × 35 cols)
  Summary v2          (1004 rows × 36 cols)
  Cost of Revenue      (1000 rows × 29 cols)
  ...

Archived (hidden/old):
  Revenue Build OLD    (996 rows × 35 cols)
  Summary ORIG        (1001 rows × 37 cols)

Usage:
  /inspect <sheet>                   Full structure analysis
  /inspect <sheet> errors            Find errors only (#REF!, #VALUE!, etc.)
  /inspect <sheet> formulas          Focus on formula patterns
  /inspect <sheet> refs              Cross-sheet references only
  /inspect <sheet> rows 15-25        Inspect specific rows
  /inspect <sheet> trace B15         Trace where a cell's value comes from
  /inspect <sheet> trace B15 dependents   What depends on a cell

Which sheet would you like to inspect?
```

Archived sheets are detected by names containing `OLD`, `ORIG`, `BACKUP`, `COPY`, `ARCHIVE`, or a lower version number when a higher one exists (e.g., `v1` when `v2` is present). List them separately so the user knows they exist but isn't nudged toward them by default.

**If the user names an archived sheet**, proceed but note it: `Note: "Revenue Build OLD" looks like an archived sheet — inspecting anyway.`

## Instructions

Parse the arguments to determine:
- **Sheet name**: Required (unless listing sheets)
- **Focus mode**: Optional - errors, formulas, refs, rows, trace, or full (default)
- **Trace target**: If trace mode, the cell to trace (e.g., B15)
- **Trace direction**: precedents (default), dependents, or both

Natural language is fine (e.g., "just show me the errors" = errors mode).

### Complexity Check

Run this **before reading any sheet data**. It costs one API call (cached).

```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id>')
info = client.get_spreadsheet_info()
sheet = next(s for s in info["sheets"] if s["name"] == "<sheet_name>")
data_cells = sheet["row_count"] * min(sheet["column_count"], 35)
```

Use this table to decide whether to warn:

| Mode | Condition | Approx. time | Warn? |
|------|-----------|--------------|-------|
| full | data_cells > 1,000 | 20–40s, 15+ API calls | **Yes** |
| refs | data_cells > 1,000 | 15–25s, 12+ API calls | **Yes** |
| errors | any size | 5–10s | No |
| formulas | any size | 8–12s | No |
| rows (specific range) | any size | 3–5s | No |
| trace | any cell | 5–10s | No |

If a warning is needed, respond with this **before doing any further reads**:

```
[Sheet] is [R] rows × [C] cols (~[N] data cells). Full inspection will take ~[X] seconds.

Faster options:
  /inspect [sheet] errors          (~5s)   scan for broken formulas only
  /inspect [sheet] formulas        (~8s)   formula patterns and structure
  /inspect [sheet] refs            (~15s)  cross-sheet references only
  /inspect [sheet] rows [1-20]     (~3s)   specific rows in full detail

Proceed with full inspection, or narrow the scope?
```

Wait for a response before reading the sheet. If the user says proceed, continue with full mode.

### Reading Strategy

1. Use SheetsClient to connect to the spreadsheet in CLAUDE.md
2. Get sheet dimensions to understand full extent
3. Read strategically (not just first N rows):
   - **Column A fully** - All row labels to understand complete vertical structure
   - **First data column fully** (usually B) - Formula/data patterns per row
   - **Sample columns** (middle + last) - Check if formulas are just filled right

### Mode-Specific Behavior

**Full mode (default):**
- Row-by-row breakdown: label, purpose (header/data/subtotal/total), formula pattern
- For each row's formula, show ONE example and note if it repeats across columns
- Flag rows where formulas VARY across columns
- List cross-sheet references
- Note any errors

**Errors mode:**
- Scan all cells for #REF!, #VALUE!, #ERROR!, #NAME?, #DIV/0!, #N/A, #NULL!
- Report each error: location, the formula causing it, likely cause
- Skip structure analysis

**Formulas mode:**
- Group rows by formula pattern (e.g., "Rows 3-10: =SUMIF(...)")
- Show unique formula patterns with example
- Highlight complex formulas (nested functions, multiple cross-refs)

**Refs mode:**
- Find all cross-sheet references
- Group by target sheet
- Show which rows/formulas reference each external sheet

**Rows mode (e.g., "rows 15-25"):**
- Full detail for specified row range only
- Show every formula in those rows (all columns, not just samples)
- Include values and formulas side by side

**Trace mode (e.g., "trace B15"):**
- Start with the target cell's current value and formula
- **Precedents (default)**: Trace upstream - where does this value come from?
  - Parse the formula, extract all cell references (same-sheet and cross-sheet)
  - For each referenced cell, show its value and formula
  - Recursively trace up to 3 levels deep (or more if requested)
  - Build a dependency tree showing the flow
- **Dependents**: Trace downstream - what breaks if this changes?
  - Scan all formulas in the workbook for references to this cell
  - Show each formula that depends on the target
  - Trace up to 3 levels of downstream dependencies
- **Both**: Show precedents and dependents together

Output format for trace:
```
Tracing: B15 = 1500 (formula: =SUM(B3:B14))

Precedents (where it comes from):
  B15: =SUM(B3:B14)
  ├─ B3: 100 (static)
  ├─ B4: 200 (static)
  ├─ B5: =B3*2
  │   └─ B3: 100 (static)
  ...

Dependents (what uses it):
  B15 is referenced by:
  ├─ B20: =B15+B16 (Subtotal row)
  │   └─ B25: =SUM(B20:B24) (Total row)
  └─ 'Quarterly'!B5: =SUMIF(...)
```

### Output Format

Adapt output to the mode. Always start with:
```
Sheet: [name] ([rows] rows x [cols] columns)
```

Then show mode-appropriate details.
