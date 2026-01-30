---
model: sonnet
---
# Audit Sheet

Check a sheet for errors, formula violations, and FP&A best practices.

## Arguments

$ARGUMENTS - Sheet name to audit, or "all" for entire spreadsheet

## Instructions

### 1. Connect and Read Structure
- Connect to the spreadsheet
- Read all values and formulas from the sheet
- Identify: row labels (column A), headers, time periods covered

### 2. Determine Sheet Purpose
Analyze and summarize:
- Sheet type: P&L, balance sheet, summary, data input, assumptions, ARR waterfall, etc.
- Time granularity: monthly, quarterly, annual
- What it calculates: revenue, expenses, headcount, ARR, cash, etc.
- Source sheets it pulls from
- One-sentence summary of its role in the model

### 3. Check for Formula Issues

**Errors**: Scan all cells for #REF!, #VALUE!, #NAME?, #DIV/0!, #ERROR!, #N/A

**Hardcoded values**: Look for literal numbers in formula cells that should reference source data
- Example: `=1572600` instead of pulling from a data sheet

**Hardcoded labels**: Quoted strings like "G&A", "Sales" that should be $A references

**Fragile references**: Hardcoded column refs like `=Monthly!Q5` that break if columns shift
- Should use SUMIFS/SUMIF with date matching instead

**Whole-column refs**: `$B:$B` instead of `$B$2:$B$100` (includes headers in calculations)

**Missing calculations**: Rows that should have formulas but are empty/static
- Example: Churn row with no formula when it should = Starting ARR + Bookings - Ending ARR

### 4. FP&A Assessment

Evaluate based on the sheet's purpose:

**Accuracy** - Are calculations correct for this purpose?
- ARR: Should follow `Ending = Starting + New - Churn` waterfall
- Gross margin: `(Revenue - COGS) / Revenue`
- Net Income: Revenue - COGS - OpEx (check the math)
- Cash burn: Should reconcile with balance sheet changes
- Flag any formulas that don't match standard definitions

**Clarity** - Would a CFO/board/investor understand without explanation?
- Are labels clear and standard?
- Is the layout logical (revenue → margin → expenses → profit)?
- Are time periods clearly marked (Act vs Fcst)?
- What context is missing that an executive would ask about?

**Industry Standard** - Does this follow SaaS/FP&A conventions?

For SaaS executive summaries, check for:
- **Rule of 40**: ARR growth % + EBITDA margin %
- **Net Dollar Retention**: (Starting ARR + Expansion - Churn) / Starting ARR
- **Gross Retention**: (Starting ARR - Churn) / Starting ARR
- **CAC Payback**: Months to recover customer acquisition cost
- **Magic Number**: Net new ARR / prior quarter S&M spend
- **Burn Multiple**: Net burn / Net new ARR
- **Runway**: Cash / monthly burn rate

For P&L sheets, check for:
- EBITDA or Adjusted EBITDA (more common than Net Income for SaaS)
- Gross margin % row (not just $ amount)
- OpEx breakdown by department (R&D, S&M, G&A)
- YoY and QoQ growth rates

For cash/balance sheets, check for:
- Runway calculation
- Working capital metrics
- Burn rate trends

**Completeness** - Is anything missing you'd expect?
- Growth rates (QoQ, YoY)
- Key ratios and percentages
- Comparative periods
- Metrics appropriate for the sheet's audience

### 5. Output Format

```
## AUDIT REPORT: [Sheet Name]

### Purpose
[1-3 sentences: what type of sheet, what it covers, its role in the model]

---

### Issues

**Formula Errors:** [List or "None found ✓"]

**Standard Violations:**
1. [Cell]: [Issue description]
   - **Fix**: [Suggested fix]
   - **Command**: `/modify [description of the fix to apply]`

---

### FP&A Assessment

**Accuracy**: [✓ or ⚠️] **[Brief verdict]**
- [Specific observations]
- [Any calculation errors or gaps]

**Clarity**: [✓ or ⚠️] **[Brief verdict]**
- [What's clear]
- [What's missing or confusing]

**Industry Standard**: [✓ or ⚠️] **[Brief verdict]**
- [What follows convention]
- [What metrics are missing]

**Completeness**: [✓ or ⚠️] **[Brief verdict]**

**Suggestions**:
1. [Prioritized, actionable suggestions]
2. [...]

**Bottom line**: [One sentence overall assessment]
```

### 6. Actionable Fix Commands

For every issue found, include a ready-to-run `/modify` command that would fix it. This lets the user copy-paste the command directly to resolve issues.

Format each fix as:
```
/modify [natural language description of the exact fix]
```

Examples:
- `/modify fix B15 to use $A15 instead of hardcoded "G&A"`
- `/modify update SUMIF ranges in row 20 to use $B$2:$B$100 instead of $B:$B`
- `/modify replace hardcoded value 1572600 in C8 with reference to ARR!D2`

If multiple issues share the same root cause, group them into a single `/modify` command:
- `/modify update all SUMIF formulas in rows 10-18 to skip headers by using $B$2:$B$100 instead of $B:$B`

At the end of the report, collect all fix commands in a summary section:
```
### Quick Fixes

Run these commands to resolve the issues above:

1. `/modify [fix 1]`
2. `/modify [fix 2]`
```
