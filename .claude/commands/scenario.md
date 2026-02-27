---
model: sonnet
---
# Scenario Analysis

Run a what-if analysis on the model without modifying the sheet.

## Arguments

$ARGUMENTS - Parameter change(s) and optional breakeven threshold

Examples:
- `/scenario Enterprise CAC = $150`
- `/scenario Enterprise initial units = 3`
- `/scenario Enterprise CAC halved, breakeven at $200k`
- `/scenario Professional Services adds a second deal in Nov-26`

## Instructions

Parse the arguments to identify:
- **Parameter**: which business line and which assumption to change
- **New value or transformation**: absolute value, multiplier (halved, doubled), or delta
- **Threshold**: breakeven target (default $175k)

### Context Check

Before reading the sheet, assess whether the revenue model structure is already known from this session:

- **Known** (e.g., `/inspect` or `/breakeven` was just run): the row positions for Revenue, COGS, and CAC per business line are in context — proceed directly to the override step, skipping re-discovery.
- **Unknown** (cold start or new sheet): a discovery pass is needed to identify which rows are Revenue, COGS, and CAC for each line. This adds ~5–10s. Proceed automatically — no need to ask — but note it in output.

If the sheet name is ambiguous or not previously seen in this session, check `get_spreadsheet_info()` to confirm it exists before reading.

### Steps

1. Read the Revenue Build sheet (or equivalent revenue input sheet)
2. For each business line, find and extract the monthly Revenue, COGS, and CAC rows
3. Build a Python dict of all current values indexed by line and month
4. Apply the override in memory — do NOT write to the sheet
5. Recompute monthly CAC-adjusted GM per line: `gm_adj = revenue - cogs - cac`
6. Sum across lines for total monthly CAC-adjusted GM
7. Find the crossing month for the threshold (before and after)
8. Show the comparison

### Output Format

```
Scenario: [description]

Monthly CAC-Adjusted GM:
Month       Before        After         Delta
Apr-27     $98,400     $116,800      +$18,400
May-27    $143,200     $170,100      +$26,900
Jun-27    $184,500     $219,700      +$35,200
...

Breakeven ($175k):
  Base:     Jun-27
  Scenario: May-27  (1 month earlier)

Driver: [which line changed and magnitude of change]
```

Only show months where the delta is non-zero. If breakeven doesn't change, say so.
If the scenario makes breakeven unreachable within the model horizon, say so.
