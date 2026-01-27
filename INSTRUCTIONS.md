# FP&A Agent Instructions

Preferences and standards for the FP&A Google Sheets agent.

## Formula Standards

### References
- **Never hardcode** department names, categories, or dates in formulas
- Department/label: reference row label `$A{row}`
- Month: reference column header `{col}$1`
- Formulas must be copy/paste-able across rows and columns

**Bad** (hardcoded):
```
=SUMIF('Headcount Input'!$B:$B,"G&A",'Headcount Input'!J:J)
=SUMPRODUCT(('Headcount Input'!$B$2:$B$100="Sales")*(...))
```

**Good** (dynamic):
```
=SUMIF('Headcount Input'!$B:$B,$A4,'Headcount Input'!J:J)
=SUMPRODUCT(('Headcount Input'!$B$2:$B$100=$A5)*(...))
```

### Identifying Non-Robust Formulas
Look for quoted strings that match row labels:
- `"G&A"`, `"Sales"`, `"Marketing"`, `"Engineering"`, `"Product"`, `"CS"`
- `"COGS"`, `"Dept"`, `"Overall"`
- Any category or label that appears in column A

These should be replaced with `$A{row}` references.

### Ranges
- **Skip headers**: Use `$B$2:$B$100` not `$B:$B`
- Whole-column refs include headers (date serials add ~46000 to sums)

### Dates
- Store as real dates (MM/DD/YYYY), not text strings
- Headers are end-of-month dates (1/31/2026, 2/28/2026)
- Monthly Summary row 2 is the source of truth:
  - C2: `=DATE(2026,1,31)` (starting date)
  - D2+: `=EOMONTH(C2+1,0)` (relative, can be copied)
- Other sheets reference Monthly Summary: `='Monthly Summary'!C$2`

## Spreadsheet Layout

- **Row 1**: Quarter labels (Q1-26, Q2-26...)
- **Row 2**: Month headers (end-of-month dates)
- **Column A**: Row labels
- **Column B**: Reserved spacer
- **Data**: Starts in Column C

## Formatting Standards

| Element | Standard |
|---------|----------|
| Font | Roboto 10 |
| Currency | $#,##0 |
| Percentage | 0.0% |
| Headers | Bold |
| Section labels | Bold |

### Freeze Panes
| Sheet | Frozen Rows | Frozen Cols |
|-------|-------------|-------------|
| Monthly/Quarterly Summary | 2 | 2 |
| Headcount Input | 1 | 3 (Name, Dept, Title) |
| ARR | 1 | 5 (Customer through Contract) |
| Other projection sheets | 2 | 2 |

## Sheet Dependencies

```
Headcount Input ──► Headcount Summary ──► Costs by Department ──► Monthly Summary
                                                      ▲                    │
ARR ──► ARR Summary ──────────────────────────────────┘                    │
                                                                           ▼
OpEx Assumptions ──► Costs by Department                          Quarterly Summary
                                                                           ▲
Cash Flow ─────────────────────────────────────────────────────────────────┘
```

## Key Formulas

### Quarter label (row 1)
```
=IF(C2="","","Q"&ROUNDUP(MONTH(C2)/3,0)&"-"&RIGHT(YEAR(C2),2))
```

### ARR helper (full amount if active)
```
=IF(AND($B2<=F$1,OR($D2="",$D2>F$1)),$C2,0)
```

### Allocated OpEx (by headcount ratio)
```
=(Dept HC / Total HC) × SUMIF('OpEx Assumptions'!$A:$A,"Overall",month_col)
```

### CS COGS Split
CS costs are split between OpEx and COGS using `'OpEx Assumptions'!$E$4` (currently 40%):
```
CS to COGS:    =CS_Subtotal × 'OpEx Assumptions'!$E$4
CS OpEx:       =CS_Subtotal × (1 - 'OpEx Assumptions'!$E$4)
```

### Quarterly aggregation
- **SUM** for flow metrics: `=SUMIF('Monthly Summary'!$C$1:$Z$1,C$1,'Monthly Summary'!$C{row}:$Z{row})`
- **First month** for opening balances: `='Monthly Summary'!{first_col}{row}`
- **Last month** for closing balances: `='Monthly Summary'!{last_col}{row}`
- **AVERAGE** for percentages: `=AVERAGEIF(...)`

## Working Style

- After changes, scan for #REF!, #VALUE!, #ERROR! and fix immediately
- Apply standard formatting (Roboto 10, currency, percentages, bold headers)
- Update documentation after structural changes
- Be autonomous - do the work and report results

## Formula Audit Checklist

When reviewing or building formulas:
1. **No hardcoded labels** - Search for quoted department/category names
2. **Ranges skip headers** - Should be `$B$2:$B$100` not `$B:$B`
3. **Copy/paste test** - Formula works when copied to adjacent cells
4. **Cross-sheet refs** - Correct sheet name and row/column anchoring
5. **Date comparisons** - Using real dates, not text strings

## API Notes

- Google Sheets API: 60 writes/minute limit
- Use batchUpdate for bulk changes
- Insert row at index 0 auto-updates formula references
