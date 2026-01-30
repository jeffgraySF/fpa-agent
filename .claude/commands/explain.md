---
model: sonnet
---
# Explain Formula

Trace and explain how a cell's value is calculated, with full FP&A context.

## Arguments

$ARGUMENTS - Cell reference like "Monthly Summary!C12" or a Google Sheets URL with cell selected

## Instructions

### 1. Gather Context with /inspect

Start by using `/inspect` to get structural context and trace the dependency tree:

1. Run `/inspect [sheet] trace [cell]` on the target cell to get its precedent tree (upstream dependencies)
2. Run `/inspect [sheet] rows [row]` on the target row to see all formulas and values across columns

This gives you the dependency tree, cross-sheet references, and formula patterns without reimplementing that logic.

### 2. Read Additional Context

Supplement the `/inspect` results with FP&A-specific context:
- **Column headers** for all referenced columns (row 1 or 2) to understand what each input represents
- **Row label** (column A) for the cell's row to understand what's being calculated
- **Sample values** in referenced cells to see real data

This context is critical. A formula like `=C55 + D55` means completely different things depending on headers:
- If C = "Invoice Date" and D = "Payment Terms (Days)" → Collection date calculation
- If C = "Base Salary" and D = "Bonus" → Total compensation
- If C = "Q1" and D = "Q2" → Summing quarters

### 3. Use the Dependency Tree

The `/inspect trace` output provides the dependency tree. Build on it:

For INDEX/MATCH, VLOOKUP, SUMIF patterns:
- Identify what's being looked up and from where
- Note the source sheet and what data it contains

If the trace wasn't deep enough (more than 3 levels needed), follow additional references manually.

### 4. Interpret with FP&A Context

Common FP&A patterns to recognize:

**Date calculations:**
- `Date + Number` = Adding days (payment terms, duration)
- `EOMONTH(date, n)` = End of month offset
- `TEXT(date, "YYYY-MM")` = Period matching

**Cash flow:**
- Invoice Date + Payment Terms = Expected Collection Date
- Booking Date + Ramp Period = Revenue Start Date

**Period allocation:**
- `IF(period matches, amount, "")` = Allocating amounts to time periods
- `SUMIF(dates, period, amounts)` = Aggregating by period

**Lookups:**
- INDEX/MATCH from another sheet = Pulling master data
- VLOOKUP to assumptions = Applying rates or parameters

### 5. Output Format

```
## EXPLAIN: [Sheet]![Cell]

**Value:** [current value]

**Formula:**
\`\`\`
[formula]
\`\`\`

### What Each Input Means
| Cell | Header | Value | Meaning |
|------|--------|-------|---------|
| C55  | Invoice Date | 2025-10-15 | When invoice was issued |
| D55  | Payment Terms | 90 | Days until payment expected |
| AC3  | Jan 2026 | (column header) | Target month for matching |

### Dependency Tree
[Show the flow from source data to final result]

### Business Logic
[Plain English explanation of what this calculates and why, using the actual column meanings]

### FP&A Context
[What type of calculation is this? Where would it be used? (e.g., "This is a cash collections forecast that predicts when invoices will be paid based on payment terms.")]
```
