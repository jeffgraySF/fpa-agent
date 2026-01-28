---
model: sonnet
---
# Explain Formula

Trace and explain how a cell's value is calculated, with full FP&A context.

## Arguments

$ARGUMENTS - Cell reference like "Monthly Summary!C12" or a Google Sheets URL with cell selected

## Instructions

### 1. Gather Context First

Before interpreting the formula, read:
- **Column headers** for all referenced columns (row 1 or 2) to understand what each input represents
- **Row label** (column A) for the cell's row to understand what's being calculated
- **Sheet name** for context on the sheet's purpose
- **Sample values** in referenced cells to see real data

This context is critical. A formula like `=C55 + D55` means completely different things depending on headers:
- If C = "Invoice Date" and D = "Payment Terms (Days)" → Collection date calculation
- If C = "Base Salary" and D = "Bonus" → Total compensation
- If C = "Q1" and D = "Q2" → Summing quarters

### 2. Read the Formula

Get the formula and its current calculated value.

### 3. Trace Dependencies

For each referenced cell:
- Read its value AND its formula (if any)
- Read its column header to understand what it represents
- If it references other sheets, follow those references
- Build a dependency tree (3 levels max unless deeper is needed)

For INDEX/MATCH, VLOOKUP, SUMIF patterns:
- Identify what's being looked up and from where
- Note the source sheet and what data it contains

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
