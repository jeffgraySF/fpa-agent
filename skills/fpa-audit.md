# FP&A Sheet Audit

Audit a Google Sheet for formula errors, FP&A best practices, and SaaS metrics
completeness. Also explains individual formulas in full financial context.

## Usage

Share a Google Sheets link or name a tab to audit.

To explain a specific formula: share the cell reference (e.g., "explain C12 on
Monthly Summary").

---

## Audit Instructions

### 1. Read the Sheet

Use the Google Drive connector to open the sheet. Read:
- Column A (all row labels — establishes the full vertical structure)
- All formula cells
- Header rows (rows 1–2) and all values

### 2. Identify Sheet Purpose

Determine:
- **Type**: P&L, ARR waterfall, balance sheet, assumptions, headcount input,
  cash flow, executive summary, raw input data
- **Time granularity**: monthly, quarterly, annual
- **What it calculates**: revenue, expenses, headcount, ARR, cash
- **Cross-sheet dependencies**: which other tabs does it reference?

### 3. Check Formula Issues

**Errors**: Scan all cells for `#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`,
`#ERROR!`, `#N/A`

**Hardcoded labels**: Quoted department or category strings inside formulas —
e.g., `"G&A"`, `"Sales"`, `"Engineering"` — should reference the label cell
(`$A{row}`) so formulas stay valid if labels change.
- Bad:  `=SUMIF($B:$B,"G&A",$J:$J)`
- Good: `=SUMIF($B$2:$B$100,$A4,$J$2:$J$100)`

**Hardcoded column refs**: Formulas like `=Monthly!Q5` break when columns
shift. Use SUMIFS with date matching instead.

**Whole-column refs**: `$B:$B` instead of `$B$2:$B$100`. Including header rows
in ranges pulls date serial numbers (~46,000) into sums, silently skewing
totals.

**Text dates**: Date headers stored as text ("Jan 2026", "1/31/26") instead of
real dates — breaks all date comparisons downstream.

**Hardcoded values**: Literal numbers in cells that should reference source data
or assumption inputs.

**Missing formulas**: Rows that appear calculated but contain static values
(e.g., a Churn row showing a fixed number when it should derive from an ARR
waterfall).

### 4. FP&A Assessment

**Accuracy** — Are the calculations correct?
- ARR waterfall: `Ending = Starting + New + Expansion - Churn`
- Gross margin: `(Revenue - COGS) / Revenue`
- Net income: `Revenue - COGS - OpEx`
- Cash burn reconciles with balance sheet changes
- Flag any formulas that don't match standard definitions

**Clarity** — Would a CFO/board/investor understand without explanation?
- Labels clear and standard?
- Layout flows logically (revenue → margin → expenses → profit)?
- Actuals vs. forecast periods labeled?
- Percentage rows alongside dollar rows?

**Industry Standard** — Does it follow SaaS/FP&A conventions?

For executive summaries and metrics sheets, check for:

| Metric | Definition |
|--------|------------|
| Rule of 40 | ARR growth % + EBITDA margin % |
| Net Dollar Retention (NRR) | (Starting ARR + Expansion - Churn) / Starting ARR |
| Gross Retention | (Starting ARR - Churn) / Starting ARR |
| CAC Payback | CAC / monthly gross margin per new customer (months) |
| Magic Number | Net new ARR / prior quarter S&M spend |
| Burn Multiple | Net burn / net new ARR |
| Runway | Ending cash / monthly burn rate |

For P&L sheets, check for:
- EBITDA or Adjusted EBITDA (more relevant than Net Income for SaaS)
- Gross margin % row (not just gross profit in dollars)
- OpEx breakdown by department (R&D, S&M, G&A)
- YoY and/or QoQ growth rates

For cash/balance sheets, check for:
- Runway calculation
- Burn rate trend
- Working capital metrics

**Completeness** — What's missing that a CFO would ask about?
- Growth rates (QoQ, YoY)
- Margin percentages alongside dollar rows
- Comparative periods (prior year, budget vs. actuals)
- Metrics appropriate to the sheet's audience

### 5. Output Format

```
## AUDIT: [Sheet Name]

### Purpose
[1–3 sentences: type, what it covers, role in the model]

---

### Issues

**Formula Errors:** [List with cell, formula, likely cause — or "None found ✓"]

**Standard Violations:**
1. [Cell or range]: [Description]
   - Fix: [Exact corrected formula or approach]

---

### FP&A Assessment

**Accuracy**: [✓ or ⚠️] [Verdict]
- [Specific observations]

**Clarity**: [✓ or ⚠️] [Verdict]
- [What works / what's missing]

**Industry Standard**: [✓ or ⚠️] [Verdict]
- [Conventions followed / metrics missing]

**Completeness**: [✓ or ⚠️] [Verdict]

**Suggestions**:
1. [Prioritized, actionable]

**Bottom line**: [One sentence overall assessment]

---

### Quick Fixes
1. [Cell/range]: [corrected formula]
2. ...
```

---

## Formula Explain Mode

When asked to explain a specific cell or formula:

1. Read the cell's formula and current calculated value
2. Read the column header (row 1 or 2) and row label (column A) for context
3. Read all referenced cells — show their values and what they represent
4. Build a dependency tree from source data to final result
5. Interpret through the FP&A lens using the actual labels, not generic cell IDs

**Common SaaS formula patterns to recognize:**

| Pattern | Meaning |
|---------|---------|
| `Date + N` | Adding payment terms or ramp days |
| `EOMONTH(date, n)` | End-of-month offset (period headers) |
| `IF(AND(start<=period, OR(end="",end>period)), amount, 0)` | ARR or headcount active-in-period check |
| `SUMIF(dates, period, amounts)` | Aggregating by time period |
| `SUMPRODUCT(flag_array * amount_array)` | Conditional sum (avoids helper column) |
| `amount / (MRR * gross_margin)` | CAC payback calculation |
| `SUMIF($A:$A, "Overall", month_col) * (deptHC / totalHC)` | OpEx allocated by headcount ratio |

**Output format:**

```
## EXPLAIN: [Sheet]![Cell]

**Value:** [current value]
**Formula:** `[formula]`

### Inputs
| Cell | Label | Value | Meaning |
|------|-------|-------|---------|

### Dependency Tree
[Source data → intermediate calc → final result]

### Business Logic
[Plain English using actual row/column labels, not generic cell references]

### FP&A Context
[What type of calculation, where it fits in the model, how it's used]
```
