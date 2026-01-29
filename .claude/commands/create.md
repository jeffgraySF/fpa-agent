---
model: sonnet
---
# Create FP&A Model

Build a complete FP&A model from user-provided input data (ARR, headcount, COA/P&L). Input formats will vary — discover the structure, propose a mapping, and get user confirmation before building.

## Arguments

$ARGUMENTS - Natural language describing the 3 input sources (sheet names, URLs, or file paths for ARR data, headcount data, and chart of accounts/P&L data)

Examples:
- `/create ARR is in "Revenue" sheet, headcount in "Team" sheet, expenses in "Budget" sheet`
- `/create revenue data in Sheet1, employees in Sheet2, P&L in Sheet3`
- `/create ARR from the "Deals" tab, HC from "Employees" tab, and COA from "GL Detail" tab`

## Instructions

This is a two-phase process. Phase 1 is read-only discovery. Phase 2 builds sheets only after user confirmation.

---

### Phase 1: Discovery & Mapping

#### 1.1 Parse Input Sources

From `$ARGUMENTS`, identify the 3 input sources:
- **ARR / Revenue data**: Customer bookings, deals, subscriptions
- **Headcount data**: Employees, team members, salaries
- **COA / P&L / Expense data**: Chart of accounts, budget, expense line items

If arguments are missing or unclear, ask the user to clarify. All 3 sources are required.

#### 1.2 Connect and Read

Connect to the spreadsheet from CLAUDE.md. For each input source:

```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id_or_url>')
_ = client.read_range('Sheet', 'A1:A1')  # init workaround
```

Use `inspect_sheet()` or `read_range()` to read headers and sample data from each source. Read enough rows to understand the full schema (at least 20 rows, more if the data is large).

#### 1.3 Analyze Each Source

For each input source, determine:

**ARR Data — look for:**
- Customer/account name
- Deal type (new vs expansion) — may not exist, may need to be inferred
- Start date / close date
- ARR or ACV amount
- Churn date / end date (may be blank for active)
- Contract length (may not exist — default to 12 months)

**Headcount Data — look for:**
- Employee name
- Department / team
- Title / role
- Start date
- End date (may be blank for active)
- Base salary
- Bonus (may not exist — default to 0)
- Commission (may not exist — default to 0)
- Benefits (may not exist — will need an assumption, e.g., 20% of salary)

**P&L / COA Data — look for:**
- Expense categories and line items
- Department allocation (may not exist)
- Monthly or annual amounts
- Which items are COGS vs OpEx
- Scaling type (fixed, per-HC, % of revenue)

#### 1.4 Present Mapping Proposal

Present a detailed mapping proposal to the user. Use this format:

```
## Input Analysis

### ARR Data (from "[source name]")
Found: [N] rows of subscription data
Column mapping:
  "[source col]" -> Customer
  "[source col]" -> Type (New/Expansion)
  "[source col]" -> Start Date
  "[source col]" -> ARR
  "[source col]" -> Churn Date
  [warnings for missing/ambiguous columns]

### Headcount Data (from "[source name]")
Found: [N] employees
Column mapping:
  "[source col]" -> Name
  "[source col]" -> Department
  ...
  [If department names don't match standard 6, show proposed mapping:]
  Department mapping:
    [source value] -> [standard dept: G&A, Sales, Marketing, Product, Engineering, CS]
    ...

### P&L / Chart of Accounts (from "[source name]")
Found: [N] expense line items
  ...
  [Flag items that need classification as COGS vs OpEx]
  [Flag items that need a scaling type assumption]

## Planning Horizon
Proposed: [start month] - [end month] (24 months)

## Information Needed
- Starting cash balance: [ask user]
- Payment terms: 40/40/20 at 30/60/90 days [confirm or adjust]
- Hosting % of revenue: 15% [confirm or adjust]
- CS COGS split %: 40% [confirm or adjust]
- Benefits % of salary: 20% [confirm or adjust, if not in data]
- [Any other missing data]

Proceed with this mapping?
```

**STOP HERE** and wait for the user to confirm or adjust the mappings. Do NOT proceed to Phase 2 until the user explicitly confirms.

---

### Phase 2: Build

Only proceed after user confirmation of the mapping.

#### 2.1 Create New Spreadsheet or Sheets

If building in the same spreadsheet, create new sheets. If the user wants a new spreadsheet, ask for the URL.

Create sheets using `batch_update`:
```python
client.batch_update([{"addSheet": {"properties": {"title": "Sheet Name"}}}])
```

#### 2.2 Build Order (dependency order)

Build sheets in this order — each depends on the ones before it:

**Step 1: Headcount Input**
- Create the sheet with columns: Name, Department, Title, Start Date, End Date, Base Salary, Bonus, Commission, Benefits
- Transform user's headcount data to match this schema using the confirmed mapping
- Map department names to the standard 6 (G&A, Sales, Marketing, Product, Engineering, CS)
- Add monthly cost columns (J+) with dates from the planning horizon
- Monthly headers: end-of-month dates (1/31/2026, 2/28/2026, etc.)
- Apply proration formula from template_specs:
  ```
  =IF(OR($D2>J$1,AND($E2<>"",$E2<EOMONTH(J$1,-1)+1)),0,
    IF(AND($D2<=EOMONTH(J$1,-1)+1,OR($E2="",$E2>=J$1)),
      ($F2+$I2)/12,
      ($F2+$I2)/12*(MIN(IF($E2="",J$1,$E2),J$1)-MAX($D2,EOMONTH(J$1,-1)+1)+1)/DAY(J$1)))
  ```
- Write static data (names, departments, salaries) as values, not formulas

**Step 2: ARR**
- Create the sheet with columns: Customer, Type, Start Date, ARR, Churn Date, Contract Length
- Transform user's ARR data using the confirmed mapping
- Default contract length to 12 if not in source data
- Default type to "New" if not distinguishable
- Add monthly ARR helper columns (G+) with same date headers as Headcount Input
- Apply ARR formula: `=IF(AND($C2<=G$1,OR($E2="",$E2>G$1)),$D2,0)`

**Step 3: OpEx Assumptions**
- Columns: Scope, Category, Subcategory, Scaling Type, Rate/Amount, then monthly cost columns
- Build from confirmed P&L/COA mapping:
  - Row for Hosting (COGS, % of Revenue, confirmed rate)
  - Row for CS COGS split (COGS, % of CS, confirmed rate)
  - Rows for department-specific expenses (Dept scope)
  - Rows for company-wide expenses (Overall scope, allocated by HC ratio)
- Apply scaling formulas per template_specs:
  - Fixed: `=$E{row}`
  - Per HC: `=$E{row}*'Headcount Summary'!{col}10`
  - % of Revenue: `=$E{row}*'ARR Summary'!{col}4`
  - % of CS: References CS Subtotal in Costs by Department

**Step 4: Headcount Summary**
- Row structure from template_specs (sections for HC count, Salary+Benefits, Bonus, Commission, Total Compensation)
- Standard 6 departments in column A for each section
- Row 1: Quarter labels referencing Monthly Summary
- Row 2: Date headers referencing Monthly Summary
- Apply formulas from template_specs:
  ```
  HC count:    =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A4)*('Headcount Input'!J$2:J$100>0))
  Salary:      =SUMIF('Headcount Input'!$B$2:$B$100,$A13,'Headcount Input'!J$2:J$100)
  Bonus:       =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A22)*('Headcount Input'!J$2:J$100>0)*('Headcount Input'!$G$2:$G$100/12))
  Commission:  =SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A31)*('Headcount Input'!J$2:J$100>0)*('Headcount Input'!$H$2:$H$100/12))
  Total:       Salary + Bonus + Commission per dept
  ```

**Step 5: ARR Summary**
- Row structure from template_specs (MRR, ARR, Active Customers, New/Churned Customers, New/Expansion/Churned ARR, Net New ARR)
- Apply formulas:
  ```
  MRR:              =SUM('ARR'!G2:G100)/12
  ARR:              =MRR*12
  Active Customers: =COUNTIF('ARR'!G2:G100,">0")
  New Customers:    SUMPRODUCT with start date in month
  Churned:          SUMPRODUCT with churn date in month
  New ARR:          SUMPRODUCT Type="New" x start in month x ARR
  Expansion ARR:    SUMPRODUCT Type="Expansion" x start in month x ARR
  Churned ARR:      SUMPRODUCT churn date in month x ARR
  Net New ARR:      New + Expansion - Churned
  ```

**Step 6: Costs by Department**
- Row structure from template_specs (6 department sections + COGS)
- Each department: Salary+Benefits, Bonus+Commission, Allocated OpEx, Department Total
- CS section: includes CS Subtotal, Less CS to COGS, CS Total (OpEx)
- COGS section: Hosting + CS (COGS) + Total COGS
- Formulas reference Headcount Summary and OpEx Assumptions per template_specs

**Step 7: Cash Flow**
- Rows: Beginning Cash, Cash Collections, Operating Cash Out, Operating Cash Burn, Interest, Other, Total Cash Change, Ending Cash
- Beginning Cash: user-provided starting cash for first month, then previous Ending Cash
- Collections: `=MRR[month]*0.4 + MRR[month-1]*0.4 + MRR[month-2]*0.2` (using confirmed payment terms)
- Operating Cash Out: Total Expenses from Costs by Department
- Ending Cash: Beginning + Total Cash Change

**Step 8: Monthly Summary**
- Row structure from template_specs (ARR Waterfall, Income Statement, Operating Expenses, SaaS Metrics, Cash)
- Row 1: Quarter labels `=IF(C2="","","Q"&ROUNDUP(MONTH(C2)/3,0)&"-"&RIGHT(YEAR(C2),2))`
- Row 2: Date headers — C2: `=DATE(2026,1,31)`, D2+: `=EOMONTH(C2+1,0)` (adjust start date to match planning horizon)
- All other rows: formulas referencing ARR Summary, Costs by Department, Cash Flow per template_specs
- This is the source-of-truth for dates — all other sheets reference Monthly Summary row 2

**Step 9: Quarterly Summary**
- Same row structure as Monthly Summary
- Quarter columns (one per quarter in the planning horizon)
- Aggregation formulas:
  - SUM rows: `=SUMIF('Monthly Summary'!$C$1:$Z$1,C$1,'Monthly Summary'!$C{row}:$Z{row})`
  - First-month rows (Starting ARR, Beginning Cash): first month of quarter
  - Last-month rows (Ending ARR, Ending Cash): last month of quarter
  - Average rows (margins): `=AVERAGE(...)` of months in quarter

#### 2.3 Formula Standards (apply everywhere)

Follow these rules from CLAUDE.md in ALL formulas:
- **No hardcoded labels**: Use `$A{row}` not `"G&A"` or `"Sales"`
- **Skip headers in ranges**: Use `$B$2:$B$100` not `$B:$B`
- **Dates**: Real dates, not text. Monthly Summary row 2 is source of truth
- **Department ref**: `$A{row}` (absolute col, relative row)
- **Month ref**: `{col}$1` (relative col, absolute row)

#### 2.4 Date Headers

Monthly Summary row 2 is the master date row. All other sheets reference it:
```
='Monthly Summary'!C$2
```

Adjust the starting date based on the user's data or confirmed planning horizon.

#### 2.5 Freeze Panes

After building each sheet, freeze the label columns and header rows:
```python
client.set_freeze('Sheet Name', rows=2, columns=2)  # Adjust per sheet
```

---

### Phase 3: Verify

After building all sheets, run `/audit all` on the new spreadsheet to check the work.

This will:
- Identify any formula errors (#REF!, #VALUE!, etc.)
- Assess FP&A accuracy (ARR waterfall, P&L, margins)
- Flag anything that doesn't follow best practices
- Provide specific suggestions for fixes

Fix any issues `/audit` finds before reporting completion to the user.

Report the final result:
```
## Model Created

**Sheets built**: [list of 9 sheets]
**Data loaded**:
  - [N] employees across [N] departments
  - [N] ARR records (~$[X]M ARR)
  - [N] expense line items

**Planning horizon**: [start] - [end]
**Starting cash**: $[X]M

**Audit result**: [summary of audit findings, or "All checks passed"]

[Any notes about assumptions made or items to review]
```
