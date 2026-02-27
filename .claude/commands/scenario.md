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

### Revenue Build Sheet Structure

Before reading, know the layout so you can parse it in one pass — no exploratory reads needed:

- **Row 1**: Month headers. Scan across to find the first and last date column (typically col G onward). Everything left of the first date header is a label column.
- **Col F** (or whichever column just before the first month): Output row label — values are `Revenue`, `COGS`, `CAC`, `MRR`, `New Units`, etc.
- **Col A**: Business line name (spans the input block for that line).
- **Input rows** (cols A–E): ASP, GM%, CAC/unit, growth rate, etc. — useful for understanding the model assumptions but not needed for the computation.
- **Output rows** (col F onward): The rows where col F = `Revenue`, `COGS`, or `CAC` are what you need. One set per business line.

### Steps

1. **Single read** — use `get_spreadsheet_info()` (cached, no extra API call) to get row and column counts, then read the entire sheet in one call:

```python
info = client.get_spreadsheet_info()
sheet = next(s for s in info["sheets"] if s["name"] == "Revenue Build")
last_col = client._col_index_to_letter(min(sheet["column_count"] - 1, 51))  # cap at AZ
last_row = min(sheet["row_count"], 200)
data = client.read_range("Revenue Build", f"A1:{last_col}{last_row}")
```

2. **Parse in one pass** from the data already in memory:
   - Find month columns: scan row 0 for date-like strings → record col indices and labels
   - Find output rows: scan col F (or the column just before the first month col) for `Revenue`, `COGS`, `CAC` → record row index and business line (from col A)
   - Build a dict: `model[line][metric] = [float values per month]`

3. Apply the override in memory — do NOT write to the sheet
4. Recompute monthly CAC-adjusted GM per line: `gm_adj = revenue - cogs - cac`
5. Sum across lines for total monthly CAC-adjusted GM
6. Find the crossing month for the threshold (before and after)
7. Show the comparison

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
