# Backlog

Future improvements for the FP&A Agent, inspired by Claude for Excel and user feedback.

## Quick Wins

- [ ] **Correct NRR formula in /audit** - Fix Net Revenue Retention calculation to use correct formula
- [ ] **Formula debugging command** - `/debug` to trace and fix broken formulas with suggested fixes
- [ ] **Better change tracking** - Show cell-by-cell before/after with explanations in `/modify`
- [ ] **More SaaS metrics in /audit** - Add Rule of 40, CAC Payback, LTV/CAC checks
- [ ] **Board deck formatting** - Format key metrics for presentation export

## Medium Effort

- [ ] **Actuals vs. Forecast boundary** - Explicit handling across all commands. `/create` should mark which months are actuals vs forecast (e.g., shading, "Act"/"Fcst" labels). `/audit` should not flag hardcoded values in actuals months. `/modify` should warn before overwriting actuals with formulas. `/inspect` should report the boundary. Consider storing the boundary date in a named range or dedicated cell so all sheets can reference it.
- [ ] **Scenario analysis** - Add sensitivity tables, scenario toggles to existing models
- [ ] **Variance analysis** - `/variance` command to compare actuals vs budget/forecast
- [ ] **Pre-built templates** - `/create dcf`, `/create comp-analysis`, `/create arr-waterfall`
- [ ] **Data import** - Pull from CSV, another sheet, or API into templates

## Larger Features

- [ ] **Template library** - Standard FP&A models (P&L, Balance Sheet, Cash Flow, 13-week cash)
- [ ] **External data connectors** - Market data APIs, accounting system integrations
- [ ] **Automated monthly close** - Workflow for pulling actuals, comparing to forecast, flagging variances
- [ ] **Multi-sheet operations** - Coordinated changes across related sheets

## Ideas from Claude for Excel

Reference: [Anthropic Financial Services Announcement](https://www.anthropic.com/news/advancing-claude-for-financial-services)

- DCF models with WACC calculations, scenario toggles, sensitivity tables
- Comparable company analysis with valuation multiples
- Due diligence data packs - process documents into spreadsheets
- Earnings analysis - extract metrics and guidance from transcripts
- Company teasers/profiles for pitch books

## Technical Improvements

- [ ] **Reduce confirmation prompts** - Expand auto-approve for common operations
- [ ] **Caching** - Cache sheet structure to reduce API calls
- [ ] **Batch operations** - Combine multiple writes into single API call
- [ ] **Error recovery** - Better handling of API failures mid-operation
