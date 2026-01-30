# FP&A Agent

Google Sheets automation for financial planning using Claude Code. Designed for early-stage SaaS companies.

## What It Does

An AI agent that can build, read, analyze, and modify financial planning spreadsheets. Built for FP&A workflows like:

- **Creating** a full FP&A model from raw data (ARR, headcount, P&L, balance sheet)
- **Inspecting** sheet structure and formula patterns
- **Auditing** for errors and FP&A best practices
- **Explaining** how complex formulas work
- **Modifying** sheets with proper validation

## Available Commands

| Command | Description |
|---------|-------------|
| `/connect` | Connect to a Google Spreadsheet |
| `/create` | Build a full FP&A model from input data |
| `/inspect` | Analyze sheet structure (formulas, refs, errors) |
| `/audit` | Check for errors and FP&A best practices |
| `/explain` | Trace and explain how a cell's value is calculated |
| `/modify` | Make changes to sheets with validation |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Cloud project with Sheets API enabled

### 1. Clone the repo

```bash
git clone https://github.com/jeffgraySF/fpa-agent.git
cd fpa-agent
```

### 2. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### 3. Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Set up Google Sheets credentials

You need OAuth credentials to access Google Sheets.

#### Create credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable the **Google Sheets API**:
   - Go to APIs & Services > Library
   - Search for "Google Sheets API"
   - Click Enable
4. Create OAuth credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app"
   - Download the JSON file
5. Save as `credentials.json` in the repo root

#### First-time authentication:

When you first run a command that accesses Sheets, you'll be prompted to authenticate in your browser. The token is saved to `~/.fpa-agent/token.json`.

### 5. Run Claude Code

```bash
claude
```

You'll see the welcome message with available commands.

## Usage Examples

```
# Connect to a spreadsheet
/connect https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID

# Inspect a sheet's structure
/inspect Monthly Summary

# Audit for errors and best practices
/audit Quarterly Summary

# Explain a formula
/explain Monthly!B15

# Build a model from raw data
/create ARR in "Deals" sheet, headcount in "Team" sheet, expenses in "Budget" sheet

# Modify a sheet
/modify add a new department row for "Product" below Engineering
```

## Project Structure

```
fpa-agent/
├── CLAUDE.md              # Agent instructions (read by Claude Code)
├── credentials.json       # Google OAuth client ID (you create this)
├── requirements.txt       # Python dependencies
├── src/
│   └── sheets/
│       ├── client.py      # Google Sheets API wrapper
│       ├── auth.py        # OAuth handling
│       └── url.py         # URL parsing utilities
└── .claude/
    └── commands/          # Slash command definitions
        ├── audit.md
        ├── connect.md
        ├── create.md
        ├── explain.md
        ├── inspect.md
        └── modify.md
```

## Configuration

### Local settings (not committed)

Create `.claude/settings.local.json` to auto-approve common tools:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Read",
      "Write",
      "Edit",
      "Glob",
      "Grep"
    ]
  }
}
```

Note: `git push` is intentionally not auto-approved.

## Troubleshooting

### "Unable to parse range" error
The sheet name may have changed or doesn't exist. Use `/connect` to see available sheets.

### Authentication issues
Delete `~/.fpa-agent/token.json` and re-authenticate.

### "No spreadsheet connected" error
Run `/connect <url>` first, or set the `SPREADSHEET_ID` environment variable.

## License

Apache 2.0 - See [LICENSE](LICENSE)
