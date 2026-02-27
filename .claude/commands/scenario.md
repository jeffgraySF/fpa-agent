---
model: sonnet
---
# Scenario Analysis

Run a what-if analysis on the model without modifying the sheet.

## Arguments

$ARGUMENTS - Parameter change(s) and an optional comparison lens

Examples:
- `/scenario Enterprise CAC = $150`
- `/scenario Enterprise initial units = 3`
- `/scenario raise Consumer AI price to $10`
- `/scenario Professional Services adds a second deal in Nov-26`
- `/scenario Enterprise CAC halved, how does that affect breakeven?`
- `/scenario double SMB growth rate, what's the revenue impact by Dec-27?`

## Instructions

Parse the arguments to identify:
- **Parameter**: which business line and which assumption to change
- **New value or transformation**: absolute value, multiplier (halved, doubled), or delta
- **Comparison lens** (optional): what the user wants to measure — breakeven timing, total revenue at a date, GM at a date, cost savings, etc. If not specified, infer from context or show the full before/after monthly table and let the numbers speak.

### Sheet Resolution

Before reading anything, resolve the target sheet from the sheet list (cached, no extra API call):

```python
info = client.get_spreadsheet_info()
sheets = info["sheets"]
```

**If the user named a sheet explicitly** → use it. Skip the rest of this section. (If the name looks archived — contains OLD, ORIG, BACKUP, COPY, ARCHIVE — warn the user but proceed.)

**If the sheet must be inferred** (e.g., "the revenue model", no sheet specified):
1. Find candidates whose names match the request's intent (e.g., "Revenue" in name for a revenue scenario)
2. Exclude sheets that look archived — names containing `OLD`, `ORIG`, `BACKUP`, `COPY`, `ARCHIVE`, or a lower version number when a higher one exists (e.g., `v1` when `v2` is present)
3. Resolve:
   - **1 candidate** → use it, note it in output: `Using: Revenue Build`
   - **2+ candidates** → ask before reading:
     ```
     I see multiple candidate sheets — which should I use?
       Revenue Build      (996 rows × 35 cols)  ← likely current
       Summary v2         (1004 rows × 36 cols)
     ```
   - **0 candidates** → ask the user which sheet to use

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
4. Recompute the relevant metric(s) per line per month
5. Show the before/after comparison focused on what the user asked about

### Output Format

Always show the monthly delta table. What you show *after* it depends on the user's goal:

```
Scenario: [description]

Monthly CAC-Adjusted GM:
Month       Before        After         Delta
Apr-27     $98,400     $116,800      +$18,400
May-27    $143,200     $170,100      +$26,900
Jun-27    $184,500     $219,700      +$35,200
...

Driver: [which line changed and by how much]
```

**Then add the relevant summary based on the comparison lens:**

- If the user asked about **breakeven timing**: add a `Breakeven ($Xk): Base: [month] / Scenario: [month]` block. Use any threshold stated in the arguments; if none given, check the sheet for a stated target (see `/breakeven` threshold detection). Only include this block if breakeven is relevant to the question.
- If the user asked about **revenue or GM at a date**: add a one-line summary: `Revenue at Dec-27: $X → $Y (+$Z)`
- If the user asked about **cost impact**: add a one-line summary of total CAC savings or cost reduction
- If no specific lens was given: just show the monthly table and a one-line bottom line (e.g., "+$35k/month by end of model horizon")

Only show months where the delta is non-zero.
If the scenario makes an outcome unreachable within the model horizon, say so.
