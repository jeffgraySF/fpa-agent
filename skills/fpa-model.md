# FP&A Model Builder

Build a complete SaaS FP&A model from input data. Reads source tabs from Google
Drive, proposes a schema mapping, gets confirmation, then builds a 9-tab model
with correct formula patterns and formatting.

## Usage

```
/fpa-model ARR is in "Revenue" tab, headcount in "Team" tab, expenses in "Budget" tab
```

Three inputs are required: ARR/revenue data, headcount data, and chart of
accounts or expense data. A balance sheet is optional (for starting cash). If
not provided, starting cash will be requested.

---

## Phase 1: Discovery & Mapping

### Read Input Data

Use the Google Drive connector to open each source tab. For each tab, read:
- Row 1 (column headers)
- A representative sample of data rows
- Note data types: dates, currency, percentages, text, numbers

### Map Each Input

**ARR / Revenue data — look for:**

| Source field | Maps to | Notes |
|---|---|---|
| Customer / account name | Customer | Required |
| Deal type | Type (New / Expansion) | Infer if missing; default "New" |
| Start / close date | Start Date | Must become a real date |
| ARR or ACV | ARR | Convert ACV ÷ contract months × 12 if needed |
| Churn / end date | Churn Date | Blank = still active |
| Contract length | Contract Length | Default 12 months if missing |

**Headcount data — look for:**

| Source field | Maps to | Notes |
|---|---|---|
| Name | Name | Required |
| Department / team | Department | Map to standard 6 (see below) |
| Title / role | Title | |
| Start date | Start Date | Required |
| End date | End Date | Blank = active |
| Base salary | Base Salary | Required |
| Bonus | Bonus | Default 0 |
| Commission | Commission | Default 0 |
| Benefits | Benefits | Default 20% of salary if not in data |

**Standard department names:** G&A, Sales, Marketing, Product, Engineering, CS

**Expense / COA data — look for:**
- Expense categories and line items
- Department allocation (if any)
- Monthly or annual amounts
- Whether each item is COGS or OpEx
- How each scales: Fixed, Per-headcount, % of revenue

**Balance sheet (optional):**
- Cash and cash equivalents (most recent period)
- Date of the balance sheet — used to anchor starting cash to the correct month

### Confirm Before Building

Present a mapping proposal and stop for user confirmation. Include:
- Column mappings for each source tab
- Department name translations (source name → standard name)
- COGS vs. OpEx classification for ambiguous line items
- Key assumptions: starting cash, payment terms (default 40/40/20 at 30/60/90
  days), hosting % of revenue (default 15%), CS-to-COGS split (default 40%),
  benefits rate if not in data
- Planning horizon (recommend 24 months from first full forecast month)
- Actuals vs. forecast boundary (which months have real P&L data)

**Do not begin building until the user explicitly confirms.**

---

## Phase 2: Build

Build in dependency order. Check for formula errors after each sheet before
moving to the next.

### Dependency Graph

```
Headcount Input ──► Headcount Summary ──► Costs by Department ──► Monthly Summary
                                                      ▲                    │
ARR ──► ARR Summary ──────────────────────────────────┘                    │
                                                                           ▼
OpEx Assumptions ──► Costs by Department                          Quarterly Summary
                                                                           ▲
Cash Flow ─────────────────────────────────────────────────────────────────┘
```

### Build Order and Key Formulas

#### Step 1: Monthly Summary — date row only

Build this first. Row 2 is the single source of truth for dates across all
sheets.

- Row 1 (quarter labels): `=IF(C2="","","Q"&ROUNDUP(MONTH(C2)/3,0)&"-"&RIGHT(YEAR(C2),2))`
- Row 2 (month headers): C2 = `=DATE(year,month,last_day)`, D2+ = `=EOMONTH(C2+1,0)`

All other sheets reference `='Monthly Summary'!{col}$2` for their date headers.
Never write standalone date values or text dates in other sheets.

#### Step 2: Headcount Input

Columns: Name | Dept | Title | Start Date | End Date | Base Salary | Bonus | Commission | Benefits | [Monthly cost cols J+]

Monthly cost uses a proration formula that handles mid-month starts and
terminations:
```
=IF(OR($D2>J$1,AND($E2<>"",$E2<EOMONTH(J$1,-1)+1)),0,
  IF(AND($D2<=EOMONTH(J$1,-1)+1,OR($E2="",$E2>=J$1)),
    ($F2+$I2)/12,
    ($F2+$I2)/12*(MIN(IF($E2="",J$1,$E2),J$1)-MAX($D2,EOMONTH(J$1,-1)+1)+1)/DAY(J$1)))
```

Write employee data (name, dept, salary) as values. Write proration formulas
for the monthly cost columns.

#### Step 3: ARR Sheet

Columns: Customer | Type | Start Date | ARR | Churn Date | Contract Length | [Monthly ARR cols G+]

Monthly ARR (full contract amount if active in period, else 0):
```
=IF(AND($C2<=G$1,OR($E2="",$E2>G$1)),$D2,0)
```

#### Step 4: Headcount Summary

Aggregates headcount counts and costs by department. Rows repeat across all 6
departments. Use `$A{row}` to reference the department label — never hardcode
"G&A" or "Sales" in formulas.

```
HC count:   =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A4)*('Headcount Input'!J$2:J$100>0))
Salary:     =SUMIF('Headcount Input'!$B$2:$B$100,$A13,'Headcount Input'!J$2:J$100)
Bonus:      =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A22)*('Headcount Input'!J$2:J$100>0)*('Headcount Input'!$G$2:$G$100/12))
Commission: =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A31)*('Headcount Input'!J$2:J$100>0)*('Headcount Input'!$H$2:$H$100/12))
```

#### Step 5: ARR Summary

Key rows:
- MRR: `=SUM('ARR'!G$2:G$100)/12`
- ARR: `=C4*12`
- Active Customers: `=COUNTIF('ARR'!G$2:G$100,">0")`
- New ARR: `=SUMPRODUCT(('ARR'!$B$2:$B$100="New")*(MONTH('ARR'!$C$2:$C$100)=MONTH(C$2))*(YEAR('ARR'!$C$2:$C$100)=YEAR(C$2))*('ARR'!$D$2:$D$100))`
- Churned ARR: SUMPRODUCT where churn date falls within the period month
- Net New ARR: New + Expansion - Churned

#### Step 6: OpEx Assumptions

Columns: Scope | Category | Subcategory | Scaling Type | Rate/Amount | [Monthly cost cols F+]

Scaling formulas by type:
- Fixed: `=$E{row}`
- Per HC: `=$E{row}*'Headcount Summary'!{col}10` (total HC row)
- % of Revenue: `=$E{row}*'ARR Summary'!{col}4` (MRR row)

Key COGS rows: Hosting (% of revenue), CS allocation (% of CS subtotal, stored
in a dedicated assumption cell).

#### Step 7: Costs by Department

Six department sections + a COGS section. Each department:
- Salary + Benefits: from Headcount Summary
- Bonus + Commission: from Headcount Summary
- Allocated OpEx: `=(DeptHC/TotalHC)*SUMIF('OpEx Assumptions'!$A$2:$A$100,"Overall",'OpEx Assumptions'!F$2:F$100)`

CS section has a COGS split:
- CS Subtotal: sum of salary + bonus + allocated OpEx
- Less CS to COGS: `=-CS_Subtotal * 'OpEx Assumptions'!$E$4` (the split rate cell)
- CS OpEx: CS Subtotal + Less CS to COGS

COGS section: Hosting + CS(COGS) = Total COGS

#### Step 8: Cash Flow

Key rows:
- Beginning Cash: prior month Ending Cash. First forecast month = provided
  starting cash. **Anchor to the correct date.** Cash provided "as of 12/31/25"
  = Beginning Cash for January 2026, not December 2025.
- Collections: `=MRR_current*0.4 + MRR_prior*0.4 + MRR_2prior*0.2`
  (adjust percentages and lag to match confirmed payment terms)
- Operating Cash Out: Total Expenses from Costs by Department
- Operating Cash Burn: Cash Out - Collections
- Ending Cash: Beginning + Total Cash Change

#### Step 9: Monthly Summary — complete remaining rows

Wire up the rest of the summary using already-built sheets:

| Row | Metric | Source |
|-----|--------|--------|
| Starting ARR | Prior Ending ARR | |
| New / Expansion / Churned ARR | ARR Summary | |
| Ending ARR | Starting + Net New | |
| Revenue (MRR) | ARR Summary MRR row | |
| COGS | Costs by Department Total COGS | |
| Gross Profit | Revenue - COGS | |
| Gross Margin % | GP / Revenue | |
| OpEx by dept | Costs by Department dept totals | |
| Total OpEx | Costs by Department total | |
| EBITDA | Gross Profit - Total OpEx | |
| EBITDA Margin % | EBITDA / Revenue | |
| Rule of 40 | ARR growth % + EBITDA margin % | |
| NRR | (Starting + Expansion - Churn) / Starting ARR | Use cells already on this sheet |
| Magic Number | Net New ARR / prior period S&M | |
| Burn Multiple | Net burn / Net new ARR | |
| Operating Cash Burn | Cash Flow | |
| Ending Cash | Cash Flow | |

On summary sheets, reference cells already on that sheet rather than reaching
back to detail tabs whenever the data is available.

#### Step 10: Quarterly Summary

Same row structure as Monthly Summary. One column per quarter.

Aggregation logic:
- **SUM** for flow metrics (revenue, expenses, new ARR, cash burn):
  `=SUMIF('Monthly Summary'!$C$1:$Z$1,C$1,'Monthly Summary'!$C{row}:$Z{row})`
- **First month** for opening balances (Starting ARR, Beginning Cash)
- **Last month** for closing balances (Ending ARR, Ending Cash)
- **AVERAGE** for margin percentages

---

## Formula Standards

Apply these rules in every formula across all sheets:

| Rule | Bad | Good |
|------|-----|------|
| No hardcoded labels | `"G&A"` in formula | `$A{row}` (absolute col, relative row) |
| Skip header rows in ranges | `$B:$B` | `$B$2:$B$100` |
| Real dates only | `"Jan 2026"` (text) | `=DATE()` or `=EOMONTH()` |
| Month references | hardcoded column letter | `{col}$2` (relative col, absolute row) |
| Copy/paste validity | formula breaks when dragged | works correctly across rows and columns |

**Data types:**
- Dates: always `=DATE(year,month,day)` formulas — never text strings
- Currency: numeric values (175000, not "$175,000")
- Percentages: decimals (0.15, not "15%")

**Number formats to apply:**
- Currency rows (revenue, expenses, ARR, cash): `$#,##0`
- Percentage rows (margins, growth rates, NRR): `0.0%`
- Date headers: `M/D/YYYY`
- Headcount / customer counts: `#,##0`
- Header rows: Bold

**Test before bulk write:** For any complex formula (proration, SUMPRODUCT,
nested IF), write it to a single cell first, verify the value is correct and
not an error, then fill to all remaining rows and columns.

---

## Phase 3: Verification

After all sheets are built:

1. Scan every sheet for formula errors (#REF!, #VALUE!, #NAME?, #DIV/0!, #N/A)
2. Verify key outputs tie to input data:
   - **Headcount**: model HC count = count of employees with start date ≤ period
     end and no end date (or end date > period start)
   - **ARR**: model total ARR = sum of active ARR records for the same month
   - **Cash**: ending cash is reasonable; starting cash is anchored to the
     correct month
3. Check cross-sheet wiring: ARR Summary, Headcount Summary, and OpEx
   Assumptions all feed Costs by Department correctly

### Report Format

```
## Model Created

Sheets built: [list of 9 tabs]
Data loaded:
  - [N] employees across [N] departments
  - [N] ARR records (~$[X]M ARR)
  - [N] expense line items

Planning horizon: [start] - [end]
Starting cash: $[X]M as of [date]

Verification:
- Headcount ([month]): Model [N] vs. Input [N] — MATCH ✓
- ARR ([month]): Model $[X]M vs. Input $[X]M — MATCH ✓
- Ending Cash ([month]): $[X]M — reasonable ✓

[Any assumptions made or items to review]
```
