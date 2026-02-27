---
model: sonnet
---
# Take Model Snapshot

Save the current model outputs as a named snapshot for future comparison with /diff.

## Arguments

$ARGUMENTS - Label for this snapshot (e.g. "base case" or "after Enterprise CAC cut")

## Instructions

### Context Check

Before reading the sheet, assess whether the revenue model structure is already known from this session:

- **Known** (e.g., `/inspect`, `/breakeven`, or `/scenario` was just run): the row positions for Revenue, COGS, and CAC per business line are in context — proceed directly to extraction, skipping re-discovery.
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

1. Parse Revenue, COGS, CAC per business line from the single read
2. For each business line, extract monthly Revenue, COGS, CAC as float lists
3. Compute CAC-adjusted GM per line per month: `gm_adj = rev - cogs - cac`
4. Compute total CAC-adjusted GM per month (sum across lines)
5. Find the breakeven month ($175k default threshold)
6. Save using the snapshot utility:

```python
import sys
sys.path.insert(0, '.')
from src.analysis.snapshot import save_snapshot

metrics = {
    "months": ["Mar'26", "Apr'26", ...],   # all months with revenue
    "by_line": {
        "Enterprise": {
            "rev":    [0, 12000, 13600, ...],
            "cogs":   [0,  8400,  9520, ...],
            "cac":    [0,  1500,  1500, ...],
            "gm_adj": [0,  2100,  2580, ...],
        },
        # ... all lines
    },
    "total_gm_adj": [2100, 980, 31400, ...],
    "breakeven": "Jun-27",          # or None if not reached
    "breakeven_threshold": 175000,
}

path = save_snapshot(
    label="<label from arguments>",
    spreadsheet_id="<spreadsheet_id>",
    spreadsheet_title="<spreadsheet_title>",
    metrics=metrics,
)
print(f"Saved: {path}")
```

### Output Format

```
Snapshot saved: "base case"
  Spreadsheet: [Spreadsheet Name]
  Months: Jan'26 – Dec'27 (24 months)
  CAC-adj GM at Dec-27: $412,000
  Breakeven ($175k): Jun-27
```
