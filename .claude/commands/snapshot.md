---
model: sonnet
---
# Take Model Snapshot

Save the current model outputs as a named snapshot for future comparison with /diff.

## Arguments

$ARGUMENTS - Label for this snapshot (e.g. "base case" or "after EHR CAC cut to 225")

## Instructions

### Context Check

Before reading the sheet, assess whether the revenue model structure is already known from this session:

- **Known** (e.g., `/inspect`, `/breakeven`, or `/scenario` was just run): the row positions for Revenue, COGS, and CAC per business line are in context — proceed directly to extraction, skipping re-discovery.
- **Unknown** (cold start or new sheet): a discovery pass is needed to identify which rows are Revenue, COGS, and CAC for each line. This adds ~5–10s. Proceed automatically — no need to ask — but note it in output.

If the sheet name is ambiguous or not previously seen in this session, check `get_spreadsheet_info()` to confirm it exists before reading.

1. Read the revenue model sheet (Revenue Build or equivalent)
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
        "Consumer PGx": {
            "rev":    [0, 3750, 4265, ...],
            "cogs":   [0, 2625, 2986, ...],
            "cac":    [0, 0,    0,    ...],
            "gm_adj": [0, 1125, 1279, ...],
        },
        # ... all lines
    },
    "total_gm_adj": [1125, 454, 25778, ...],
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
  Spreadsheet: Point Health Forecast_2026-02_Rev_Breakout
  Months: Mar'26 – Dec'27 (22 months)
  CAC-adj GM at Dec-27: $537,041
  Breakeven ($175k): Jun-27
```
