---
model: sonnet
---
# Breakeven Analysis

Find the month(s) where CAC-adjusted gross margin crosses one or more thresholds.

## Arguments

$ARGUMENTS - Optional threshold(s) in dollars. Default: $175k

Examples:
- `/breakeven` — default $175k
- `/breakeven $100k $175k $250k` — multiple thresholds
- `/breakeven $200k` — custom threshold

## Instructions

### Context Check

Before reading the sheet, assess whether the revenue model structure is already known from this session:

- **Known** (e.g., `/inspect` or `/scenario` was just run): the row positions for Revenue, COGS, and CAC per business line are in context — proceed directly to the extraction step, skipping re-discovery.
- **Unknown** (cold start or new sheet): a discovery pass is needed to identify which rows are Revenue, COGS, and CAC for each line. This adds ~5–10s. Proceed automatically — no need to ask — but note it in output.

If the sheet name is ambiguous or not previously seen in this session, check `get_spreadsheet_info()` to confirm it exists before reading.

1. Read the revenue model sheet (Revenue Build or equivalent)
2. For each business line, extract monthly: Revenue, COGS, CAC
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
