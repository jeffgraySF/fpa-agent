# FP&A Template Specification

## Overview

Financial Planning & Analysis template for a SaaS company. Projects revenue, expenses, and cash over 24 months with quarterly rollups.

## Sheet Structure (9 tabs)

### 1. Monthly Summary
Executive view with ARR waterfall, P&L, and cash metrics.

| Row | Label | Source |
|-----|-------|--------|
| 1 | Quarter | Dynamic: Q1-26, Q2-26... |
| 2 | Month headers | End-of-month dates |
| 3 | **ARR Waterfall** | |
| 4 | Starting ARR | Previous Ending ARR |
| 5 | New ARR | ARR Summary row 13 |
| 6 | Expansion ARR | ARR Summary row 14 |
| 7 | Churned ARR | ARR Summary row 15 |
| 8 | Ending ARR | Starting + New + Expansion - Churned |
| 9 | **Income Statement** | |
| 10 | Revenue (MRR) | ARR Summary row 4 |
| 11 | Cost of Revenue (COGS) | Costs by Dept row 46 (Total COGS) |
| 12 | Gross Profit | Revenue - COGS |
| 13 | Gross Margin % | GP / Revenue (~75% with CS split) |
| 15 | **Operating Expenses** | |
| 16-21 | G&A, Sales, Marketing, Product, Engineering, CS | Costs by Dept totals (CS = row 39, OpEx portion) |
| 22 | Total Operating Expenses | Costs by Dept row 41 |
| 24 | Operating Income (EBITDA) | Gross Profit - OpEx |
| 25 | Operating Margin % | EBITDA / Revenue |
| 28 | **SaaS Metrics** | |
| 29 | Magic Number | Net New ARR / Prior Period S&M Spend |
| 30 | Net New ARR / Burn | Net New ARR / Operating Cash Burn |
| 31 | NRR | (Starting ARR + Expansion - Churned) / Starting ARR |
| 33 | **Cash** | |
| 34 | Operating Cash Burn | Cash Flow row 7 |
| 35 | Ending Cash Balance | Cash Flow row 13 |

### 2. Quarterly Summary
Same structure as Monthly Summary, aggregated by quarter.

**Aggregation logic:**
- **SUM**: Revenue, COGS, OpEx, New ARR, Churned ARR, Cash Burn
- **First month**: Starting ARR
- **Last month**: Ending ARR, Ending Cash Balance
- **AVERAGE**: Margin percentages

**Formula pattern:**
```
=SUMIF('Monthly Summary'!$C$1:$Z$1,C$1,'Monthly Summary'!$C{row}:$Z{row})
```

### 3. Headcount Input
Master employee data with monthly cost calculations.

| Column | Field |
|--------|-------|
| A | Name |
| B | Department |
| C | Title |
| D | Start Date |
| E | End Date |
| F | Base Salary |
| G | Bonus |
| H | Commission |
| I | Benefits |
| J+ | Monthly cost (prorated Salary + Benefits) |

**Proration formula:**
```
=IF(OR($D2>J$1,AND($E2<>"",$E2<EOMONTH(J$1,-1)+1)),0,
  IF(AND($D2<=EOMONTH(J$1,-1)+1,OR($E2="",$E2>=J$1)),
    ($F2+$I2)/12,
    ($F2+$I2)/12*(MIN(IF($E2="",J$1,$E2),J$1)-MAX($D2,EOMONTH(J$1,-1)+1)+1)/DAY(J$1)))
```

### 4. Headcount Summary
Aggregates headcount costs by department.

| Section | Rows | Formula |
|---------|------|---------|
| Month-ending HC by Dept | 4-10 | SUMPRODUCT where monthly cost > 0 |
| Salary + Benefits by Dept | 13-19 | SUMIF on department |
| Bonus by Dept | 22-28 | SUMPRODUCT active × Bonus/12 |
| Commission by Dept | 31-37 | SUMPRODUCT active × Commission/12 |
| Total Compensation | 40-46 | Salary + Bonus + Commission |

**Key formulas (all reference $A for department):**
```
HC count:    =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A4)*('Headcount Input'!J$2:J$100>0))
Salary:      =SUMIF('Headcount Input'!$B$2:$B$100,$A13,'Headcount Input'!J$2:J$100)
Bonus:       =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A22)*('Headcount Input'!J$2:J$100>0)*('Headcount Input'!$G$2:$G$100/12))
Commission:  =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A31)*('Headcount Input'!J$2:J$100>0)*('Headcount Input'!$H$2:$H$100/12))
```

### 5. ARR
Customer data with monthly ARR helper columns.

| Column | Field |
|--------|-------|
| A | Customer |
| B | Type (New / Expansion) |
| C | Start Date |
| D | ARR |
| E | Churn Date |
| F | Contract Length |
| G+ | Monthly ARR (full amount if active, else 0) |

**Type values:**
- **New**: First booking for this customer
- **Expansion**: Additional ARR for existing customer (upsell/cross-sell)

**Monthly ARR formula:**
```
=IF(AND($C2<=G$1,OR($E2="",$E2>G$1)),$D2,0)
```

### 6. ARR Summary
Revenue and customer metrics.

| Row | Metric | Formula |
|-----|--------|---------|
| 4 | MRR | `=SUM('ARR'!G2:G100)/12` |
| 5 | ARR | MRR × 12 |
| 8 | Active Customers | `=COUNTIF('ARR'!G2:G100,">0")` |
| 9 | New Customers | SUMPRODUCT start date in month |
| 10 | Churned Customers | SUMPRODUCT churn date in month |
| 13 | New ARR | SUMPRODUCT Type="New" × start in month × ARR |
| 14 | Expansion ARR | SUMPRODUCT Type="Expansion" × start in month × ARR |
| 15 | Churned ARR | SUMPRODUCT churn date in month × ARR |
| 16 | Net New ARR | New + Expansion - Churned |

### 7. OpEx Assumptions
Non-headcount operating expenses with scaling rules.

| Column | Field |
|--------|-------|
| A | Scope (COGS, Dept, Overall) |
| B | Category |
| C | Subcategory |
| D | Scaling Type |
| E | Rate/Amount |
| F+ | Monthly cost |

**Key rows:**
| Row | Scope | Category | Description |
|-----|-------|----------|-------------|
| 3 | COGS | Hosting | AWS/Cloud (15% of revenue) |
| 4 | COGS | CS | Allocation to COGS (40% of CS costs) |
| 5+ | Dept/Overall | Various | Marketing, Professional Services, etc. |

**Scope values:**
- **COGS**: Cost of revenue items (Hosting, CS allocation)
- **Dept**: Direct to department (Marketing spend)
- **Overall**: Allocated by headcount ratio

**Scaling formulas:**
- Fixed: `=$E{row}`
- Per HC: `=$E{row}*'Headcount Summary'!{col}10`
- % of Revenue: `=$E{row}*'ARR Summary'!{col}4`
- % of CS: References CS Subtotal in Costs by Department

### 8. Costs by Department
Consolidated expenses by department, split between OpEx and COGS.

| Section | Rows |
|---------|------|
| G&A | 3-7 |
| Sales | 9-13 |
| Marketing | 15-19 |
| Product | 21-25 |
| Engineering | 27-31 |
| CS | 33-39 |
| Total Operating Expenses | 41 |
| COGS | 43-46 |
| Total Expenses | 47 |

**CS section structure:**
| Row | Label | Formula |
|-----|-------|---------|
| 34-36 | Salary, Bonus, Allocated | From Headcount Summary |
| 37 | CS Subtotal | Sum of above |
| 38 | Less: CS to COGS | `-CS Subtotal × 'OpEx Assumptions'!$E$4` |
| 39 | CS Total (OpEx) | CS Subtotal + Less CS to COGS |

**COGS section structure:**
| Row | Label | Formula |
|-----|-------|---------|
| 43 | COGS | Section header |
| 44 | Hosting | From OpEx Assumptions (15% of revenue) |
| 45 | CS (COGS) | `CS Subtotal × 'OpEx Assumptions'!$E$4` |
| 46 | Total COGS | Hosting + CS (COGS) |

**Per department:**
- Salary + Benefits: from Headcount Summary
- Bonus + Commission: from Headcount Summary
- Allocated OpEx: `(Dept HC / Total HC) × SUMIF(Scope="Overall")`

### 9. Cash Flow
Cash collections and payments with payment terms lag.

| Row | Metric |
|-----|--------|
| 3 | Beginning Cash Balance |
| 5 | Cash Collections |
| 6 | Operating Cash Out |
| 7 | Operating Cash Burn |
| 8-10 | Interest Income/Expense, Other |
| 11 | Total Cash Change |
| 13 | Ending Cash Balance |

**Payment terms:** 40% @ 30 days, 40% @ 60 days, 20% @ 90 days

**Collections formula:**
```
=MRR[month]*0.4 + MRR[month-1]*0.4 + MRR[month-2]*0.2
```

## Quarter Labels

All sheets have row 1 with dynamic quarter labels:
```
=IF(C2="","","Q"&ROUNDUP(MONTH(C2)/3,0)&"-"&RIGHT(YEAR(C2),2))
```

## Key Formula Patterns

### Reference conventions
- Department: `$A{row}` (absolute column, relative row)
- Month: `{col}$1` (relative column, absolute row)
- Skip headers: Use `$B$2:$B$100` not `$B:$B`

### Date handling
- Store as real dates (MM/DD/YYYY), not text
- Headers are end-of-month dates (1/31/2026)
- Monthly Summary row 2 is the source of truth for dates
  - C2: `=DATE(2026,1,31)` (starting date)
  - D2+: `=EOMONTH(C2+1,0)` (relative to previous cell)
- All other sheets reference Monthly Summary: `='Monthly Summary'!C$2`

### Cross-sheet references
```
='Headcount Summary'!C13        (same column, specific row)
='ARR Summary'!$C$4             (specific cell)
=SUMIF('OpEx Assumptions'!$A:$A,"Overall",'OpEx Assumptions'!F:F)
```

## Test Data

- **Headcount**: 50 employees across 6 departments
- **ARR**: 44 customers (~$6M ARR), including 10 with churn dates
- **Starting Cash**: $5M
- **Gross Margin**: ~75% (with 40% of CS allocated to COGS)
