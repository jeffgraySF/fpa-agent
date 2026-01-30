---
model: sonnet
---
# Create FP&A Model

Build a complete FP&A model from user-provided input data (ARR, headcount, COA/P&L, and optionally a balance sheet for starting cash). Input formats will vary — discover the structure, propose a mapping, and get user confirmation before building.

## Arguments

$ARGUMENTS - Natural language describing input sources (sheet names, URLs, or file paths for ARR data, headcount data, chart of accounts/P&L data, and optionally balance sheet data)

Examples:
- `/create ARR is in "Revenue" sheet, headcount in "Team" sheet, expenses in "Budget" sheet`
- `/create revenue data in Sheet1, employees in Sheet2, P&L in Sheet3, balance sheet in Sheet4`
- `/create ARR from the "Deals" tab, HC from "Employees" tab, and COA from "GL Detail" tab`

## Instructions

This is a three-phase process. Phase 1 is read-only discovery. Phase 2 builds sheets with incremental verification after each step. Phase 3 is a full audit.

---

### Phase 1: Discovery & Mapping

#### 1.1 Parse Input Sources

From `$ARGUMENTS`, identify input sources:
- **ARR / Revenue data** (required): Customer bookings, deals, subscriptions
- **Headcount data** (required): Employees, team members, salaries
- **COA / P&L / Expense data** (required): Chart of accounts, budget, expense line items
- **Balance sheet data** (optional): Cash balances, assets, liabilities — used to extract starting cash

If the first 3 sources are missing or unclear, ask the user to clarify. All 3 are required.

If no balance sheet is provided, ask the user for starting cash during the mapping proposal (step 1.4). If a balance sheet IS provided, extract starting cash from it automatically.

#### 1.2 Connect and Inspect

Connect to the spreadsheet from CLAUDE.md, then use `/inspect` to analyze each input source:

```python
from src.sheets.client import SheetsClient
client = SheetsClient('<spreadsheet_id_or_url>')
_ = client.read_range('Sheet', 'A1:A1')  # init workaround
```

For each input source sheet, run these `/inspect` modes to understand its structure:
- `/inspect [sheet]` — Full structure analysis (row labels, formula patterns, data vs header rows)
- `/inspect [sheet] formulas` — Identify formula patterns (which rows are calculated vs static data)
- `/inspect [sheet] refs` — Find cross-sheet references (understand existing relationships)
- `/inspect [sheet] errors` — Pre-check for errors in source data

This reuses `/inspect`'s reading strategy (Column A fully, first data column fully, sample columns) and gives you structured metadata about each source rather than raw reads.

Supplement with `read_range()` for additional rows if `/inspect` doesn't cover enough data to determine the schema.

#### 1.3 Analyze Each Source

Using the `/inspect` output, determine for each input source.

**For every mapped column, note its data type** (date, currency, percentage, text, number). This is critical for Phase 2 — dates must be written as `=DATE()` formulas, not text strings. Currency must be numeric, not formatted strings like "$100,000".

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

**Balance Sheet Data (if provided) — look for:**
- Cash and cash equivalents (most recent period)
- Total assets / total liabilities (for context)
- Date of the balance sheet (to align with planning horizon start)
- Extract the cash balance to use as Starting Cash in the Cash Flow sheet

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

### Balance Sheet (from "[source name]") — if provided
  Cash & cash equivalents: $[X] as of [date]
  [Any other relevant context]

## Planning Horizon
Proposed: [start month] - [end month] (24 months)

## Actuals vs. Forecast Boundary
- **Actuals period**: [start] - [end] (months with real data in P&L)
- **Forecast period**: [start] - [end] (projected months)
- Cash balance anchors to [date]: $[X] (end of actuals period)

## Information Needed
- Starting cash balance: $[X] from balance sheet [or: ask user if no balance sheet provided]
- Payment terms: 40/40/20 at 30/60/90 days [confirm or adjust]
- Hosting % of revenue: 15% [confirm or adjust]
- CS COGS split %: 40% [confirm or adjust]
- Benefits % of salary: 20% [confirm or adjust, if not in data]
- [Any other missing data]

## After Build: Input Tabs
The original input tabs ([list names]) will remain in the spreadsheet. After confirming the model is correct, you can:
- **Hide** them (right-click tab → Hide sheet) to keep them as reference
- **Delete** them if no longer needed

Proceed with this mapping?
```

**STOP HERE** and wait for the user to confirm or adjust the mappings. Do NOT proceed to Phase 2 until the user explicitly confirms.

---

### Phase 2: Build

Only proceed after user confirmation of the mapping.

#### 2.1 Create New Spreadsheet or Sheets

If building in the same spreadsheet, create new sheets. If the user wants a new spreadsheet, ask for the URL.

Check for sheet name collisions before creating. If an input tab has the same name as a planned output tab (e.g., "Services"), rename the output tab (e.g., "Services Summary") to avoid conflicts.

Create sheets using `batch_update`:
```python
client.batch_update([{"addSheet": {"properties": {"title": "Sheet Name"}}}])
```

#### 2.2 Build Monthly Summary Date Row First

Before building any other sheet, create Monthly Summary with row 1 (quarter labels) and row 2 (date headers). This is the **single source of truth** for dates:
- C2: `=DATE(2026,1,31)` (adjust to planning horizon start)
- D2+: `=EOMONTH(C2+1,0)`

All other sheets must reference `='Monthly Summary'!{col}$2` for their date headers. Never write standalone date values or date strings in other sheets.

#### 2.3 Build Order (dependency order)

Build sheets in this order — each depends on the ones before it. **After each step, run `/inspect [sheet] errors` to catch problems before they cascade.**

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
- **Beginning Cash must anchor to the correct date.** If the user provides a cash balance as of 12/31/2025, that balance corresponds to the *end* of December 2025, not the beginning of January 2025. Set the Beginning Cash for **January 2026** (or the first forecast month) to the provided balance. Do NOT set January 2025 to that value if the model includes 2025 actuals — the cash will be wrong for every month.
- For forecast months: Beginning Cash = previous month's Ending Cash
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

#### 2.4 Test Before Bulk Write

Follow the **Test Before Bulk Write** procedure from CLAUDE.md for every complex formula (proration, SUMPRODUCT, nested IF). If the test cell errors, debug and fix before proceeding.

#### 2.5 Verify After Each Sheet

After building each sheet, run `/inspect [sheet] errors` to scan for formula errors. If any errors are found:
- Fix them immediately before building the next sheet
- Re-scan after fixing to confirm zero errors

Also run a **sanity check** appropriate to the sheet:
- **Headcount Input**: Verify total HC count roughly matches number of input rows
- **ARR Model**: Verify ARR amounts match source data
- **Headcount Summary**: Verify total HC > 0 for months with active employees
- **OpEx Assumptions**: Verify fixed amounts match expected averages
- **Costs by Department**: Verify total expenses > 0 for active months
- **Cash Flow**: Verify ending cash is in a reasonable range (positive or expected negative)

#### 2.6 Formula Standards (apply everywhere)

Follow these rules from CLAUDE.md in ALL formulas:
- **No hardcoded labels**: Use `$A{row}` not `"G&A"` or `"Sales"`
- **Skip headers in ranges**: Use `$B$2:$B$100` not `$B:$B`
- **Dates**: Real dates, not text. Monthly Summary row 2 is source of truth
- **Department ref**: `$A{row}` (absolute col, relative row)
- **Month ref**: `{col}$1` (relative col, absolute row)

#### 2.7 Data Type Rules

Follow the **Data Type Rules** from CLAUDE.md. Dates must be `=DATE()` formulas, currency must be numeric, percentages as decimals.

#### 2.8 Number Formatting

After writing data and formulas to each sheet, apply formats per the **Number Formatting** standards in CLAUDE.md. Apply formatting after each sheet is built and verified, not as a separate pass at the end.

#### 2.9 Freeze Panes

After building each sheet, freeze the label columns and header rows:
```python
client.set_freeze('Sheet Name', rows=2, columns=2)  # Adjust per sheet
```

---

### Phase 3: Final Audit

By this point, each sheet should already be error-free (from step 2.5 incremental checks). The final audit catches cross-sheet issues and FP&A logic problems that only appear when the full model is wired together.

Run `/audit all` on the new spreadsheet to check:
- Formula errors (#REF!, #VALUE!, etc.) — should be zero if step 2.5 was followed
- Cross-sheet reference integrity (do all sheets agree on totals?)
- FP&A accuracy (ARR waterfall, P&L, margins, cash reconciliation)
- Formula standard violations (hardcoded labels, whole-column refs, etc.)

#### 3.1 Reconciliation Checks

Run the **Reconciliation Checks** from CLAUDE.md. These verify that cash, headcount, ARR, and revenue in the model tie to the known input values. Fix any mismatches before reporting completion.

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
