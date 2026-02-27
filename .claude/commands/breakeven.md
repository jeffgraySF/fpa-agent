---
model: sonnet
---
# Breakeven Analysis

Find the month(s) where CAC-adjusted gross margin crosses one or more thresholds.

## Arguments

$ARGUMENTS - Optional threshold(s) in dollars. If omitted, the threshold is read from the sheet or confirmed with the user.

Examples:
- `/breakeven` — detect threshold from sheet, or ask
- `/breakeven $100k $175k $250k` — multiple explicit thresholds
- `/breakeven $200k` — single explicit threshold

## Instructions

### Context Check

Before reading the sheet, assess whether the revenue model structure is already known from this session:

- **Known** (e.g., `/inspect` or `/scenario` was just run): the row positions for Revenue, COGS, and CAC per business line are in context — proceed directly to the extraction step, skipping re-discovery.
- **Unknown** (cold start or new sheet): a discovery pass is needed to identify which rows are Revenue, COGS, and CAC for each line. This adds ~5–10s. Proceed automatically — no need to ask — but note it in output.

If the sheet name is ambiguous or not previously seen in this session, check `get_spreadsheet_info()` to confirm it exists before reading.

### Single-Read Approach

Read the entire sheet in **one API call** using dimensions from the cached `get_spreadsheet_info()`:

```python
info = client.get_spreadsheet_info()
sheet = next(s for s in info["sheets"] if s["name"] == "Revenue Build")
last_col = client._col_index_to_letter(min(sheet["column_count"] - 1, 51))
last_row = min(sheet["row_count"], 200)
data = client.read_range("Revenue Build", f"A1:{last_col}{last_row}")
```

Then parse in one pass from `data`:
- **Month columns**: scan row 0 for date-like strings → record col indices + labels
- **Output rows**: scan the column just before the first month col for `Revenue`, `COGS`, `CAC` → record row index + business line (from col A)
- Build `model[line][metric] = [float values per month]`

### Threshold Detection

If the user provided explicit threshold(s) in the arguments, use those. Otherwise:

1. **Scan the sheet** (already in memory from the single read) for cells containing phrases like "need", "target", "breakeven", "goal" near a dollar amount. A note cell like "Need $175,000 monthly of CAC-adjusted GM" is a valid source.
2. **If found**: use that value and tell the user where it came from — e.g., `Threshold: $175k (from Revenue Inputs A17)`
3. **If not found**: ask before assuming:
   ```
   No breakeven target found in the sheet. What threshold should I use? (e.g. $175k)
   ```

### Steps

1. Parse Revenue, COGS, CAC per business line from the single read
2. Resolve the threshold (from arguments, sheet, or user confirmation)
3. Compute monthly CAC-adjusted GM per line: `Revenue - COGS - CAC`
4. Sum all lines for total monthly CAC-adjusted GM
5. For each threshold, find the first month it is crossed
6. Identify the primary driver(s) at each crossing point

### Output Format

```
Breakeven Analysis

Threshold    Month      CAC-adj GM    Primary Driver
$100k        Apr-27      $98,400      Partner + Enterprise
$175k        Jun-27     $184,500      Partner + Enterprise
$250k        Sep-27     $261,300      Enterprise

Monthly CAC-Adjusted GM by Line:
Month      Entpr     SMB   ProfSvc  Support    TOTAL
Mar'26    $2,100      $0        $0       $0    $2,100
Apr'26    $2,380      $0    $1,800  -$3,200      $980
...

Key observations:
- [Which line is the primary engine]
- [Which lines are net drags due to CAC]
- [The single assumption that most affects the timeline]
```

Show all months from first revenue through model horizon.
Flag any line that is CAC-negative (spending more on CAC than generating in GM) and when it turns positive.
