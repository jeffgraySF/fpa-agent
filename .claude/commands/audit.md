---
model: sonnet
---
# Audit Sheet

Check a sheet for errors and formula standard violations.

## Instructions

1. Connect to the spreadsheet
2. Read all formulas from the specified sheet
3. Check for:
   - **Errors**: #REF!, #VALUE!, #NAME?, #DIV/0!, #ERROR!
   - **Hardcoded labels**: Quoted strings like "G&A", "Sales", "COGS" that should be $A references
   - **Whole-column refs**: $B:$B instead of $B$2:$B$100 (includes headers)
   - **Broken cross-sheet refs**: References to sheets/ranges that don't exist
4. Report issues with cell locations and suggested fixes
5. If no issues found, confirm the sheet passes audit

## Arguments

$ARGUMENTS - Sheet name to audit, or "all" for entire spreadsheet
