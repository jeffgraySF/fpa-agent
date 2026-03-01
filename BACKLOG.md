# Backlog

Improvements not yet implemented. Ordered roughly by value / effort ratio.

---

## Performance

### Emit row map after discovery
**Effort**: ~30 min
**Saves**: Full discovery pass on every subsequent `/scenario`, `/breakeven`, `/snapshot` call in the same session

After a skill parses the Revenue Build structure (month columns, output row indices per business line), it should print the row map explicitly in its output so the context check in later calls can actually use it:

```
Structure (Revenue Build): months G–AE (Jan'26–Dec'27) | Revenue rows: Enterprise=12, SMB=24, ... | COGS: 9, 21, ... | CAC: 10, 22, ...
```

Right now the context check says "skip re-discovery if structure is known" but nothing saves the structure to context in a reusable format.

---

### Fix init workaround in `SheetsClient`
**Effort**: ~1 hr
**Saves**: 1 API call per skill invocation (currently every skill does `client.read_range('Sheet', 'A1:A1')` as a no-op init)

Root cause: something in `SheetsClient.__init__` or `set_spreadsheet()` requires a read before subsequent reads work correctly. Investigate and fix at the source so skills don't need the workaround.

---

## Features

### Conditional formatting support
**Effort**: 2–3 hrs
**Enables**: Apply traffic-light colors, variance highlighting, and heat maps via `/modify` and `/create`

The Sheets API supports `addConditionalFormatRule` in `batch_update`. Common FP&A use cases:
- **Variance columns**: Green/red based on actual vs. plan (e.g., `>0` = green, `<0` = red)
- **Actuals vs. forecast**: Shade past months differently from projected months
- **Heat maps**: CAC payback by cohort, burn rate trends
- **Error highlighting**: Auto-flag #REF!, #DIV/0! cells in red

Implementation notes:
- Rules take a `BooleanCondition` (e.g., `NUMBER_GREATER`, `NUMBER_LESS`) or `GradientRule`
- Color is set via `color` object (RGB 0–1 scale)
- Rules are ordered — first match wins
- Should be exposed as natural language in `/modify`: "highlight variances in column D red/green"

---

## Accuracy / Robustness

### Build `src/analysis/revenue_model.py`
**Effort**: 2–3 hrs
**Enables**: Correct scenario modeling for non-ASP parameters (unit count, growth rate, churn, CAC changes)

The current scenario approach reads computed Revenue/COGS rows and scales them. This works for ASP changes (revenue = subscribers × ASP, so scaling is correct) but breaks for:
- **Initial unit changes**: affects the compounding base, not just one month
- **Growth rate changes**: changes every downstream month differently
- **Churn changes**: affects the subscriber retention curve
- **CAC changes**: already in the output rows, but the relationship to new units is non-trivial

A `RevenueModel` class should:
- Parse input assumptions (ASP, GM%, CAC/unit, growth rate, churn, start date, initial units) from the inputs section of Revenue Build
- Simulate the subscription model from first principles for any parameter override
- Return monthly Revenue, COGS, CAC arrays per business line

This also enables the skill to validate scenarios before applying them (e.g., "growth rate must be between 0–100%").
