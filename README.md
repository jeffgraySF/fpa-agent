# FP&A Agent

Google Sheets automation for financial planning using Claude Code. Designed for early-stage SaaS companies.

## Interface

The primary interface is **Claude Code** with slash commands (e.g. `/modify`, `/inspect`). This is the recommended way to use the project.

A standalone CLI agent (`src/agent/`) is also included for reference — it exposes similar capabilities as a terminal chatbot using the Claude API directly, without Claude Code.

## What It Does

An AI agent that can build, read, analyze, and modify financial planning spreadsheets. Built for FP&A workflows like:

- **Creating** a full FP&A model from raw data (ARR, headcount, P&L, balance sheet)
- **Inspecting** sheet structure and formula patterns
- **Auditing** for errors and FP&A best practices
- **Explaining** how complex formulas work
- **Modifying** sheets with plan-mode approval before any writes
- **Scenario analysis** without touching the sheet
- **Breakeven analysis** across revenue lines
- **Snapshot & diff** to track model changes over time

## Available Commands

| Command | Description |
|---------|-------------|
| `/connect` | Connect to a Google Spreadsheet |
| `/create` | Build a full FP&A model from input data |
| `/inspect` | Analyze sheet structure (formulas, refs, errors) |
| `/audit` | Check for errors and FP&A best practices |
| `/scan` | Full formula scan — every cell, not just a sample |
| `/explain` | Trace and explain how a cell's value is calculated |
| `/modify` | Make changes to sheets with plan-mode approval |
| `/scenario` | Run a what-if analysis without modifying the sheet |
| `/breakeven` | Find the month CAC-adjusted GM crosses a threshold |
| `/snapshot` | Save current model outputs as a named snapshot |
| `/diff` | Compare two snapshots to see what changed |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic account (Claude Pro/Team subscription, or API key)
- A Google Cloud project with Sheets API enabled

### 1. Clone the repo

```bash
git clone https://github.com/jeffgraySF/fpa-agent.git
cd fpa-agent
```

### 2. Install and authenticate Claude Code

Follow the [Claude Code setup guide](https://docs.anthropic.com/en/docs/claude-code/setup) to install and authenticate. The short version:

```bash
npm install -g @anthropic-ai/claude-code
claude  # opens browser login if you have a Claude subscription, or set ANTHROPIC_API_KEY first
```

### 3. Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Set up Google Sheets credentials

You need OAuth credentials to allow the agent to read and write your spreadsheets. `credentials.json` is gitignored — it stays on your machine and is never committed.

#### 4a. Create a Google Cloud project and enable the API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Enable the **Google Sheets API**:
   - APIs & Services > Library > search "Google Sheets API" > Enable

#### 4b. Configure the OAuth consent screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** and click Create
3. Fill in the required fields (app name, support email) — the values don't matter for personal use
4. On the **Test users** step, add your own Google email address
5. Save and continue through the remaining steps

> This step is required. Without it, the browser auth will fail with an "access blocked" error.

#### 4c. Create OAuth credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Desktop app**, give it any name
4. Click Create, then **Download JSON**
5. Save the downloaded file as `credentials.json` in the repo root

#### 4d. First-time authentication

When you first run a command that accesses Sheets, a browser window will open asking you to sign in and grant access. After you approve, the token is saved to `~/.fpa-agent/token.json` — you won't be prompted again unless the token expires.

### 5. Run Claude Code

From the repo root:
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

# Full formula scan (every cell)
/scan Revenue Build

# Explain a formula
/explain Monthly!B15

# Build a model from raw data
/create ARR in "Deals" sheet, headcount in "Team" sheet, expenses in "Budget" sheet

# Modify a sheet (shows plan + asks for approval before writing)
/modify add a new department row for "Product" below Engineering

# What-if analysis without touching the sheet
/scenario Enterprise CAC halved, breakeven at $200k

# Find breakeven month(s)
/breakeven $100k $175k $250k

# Save a snapshot, then compare after changes
/snapshot base case
/diff
```

## Project Structure

```
fpa-agent/
├── CLAUDE.md              # Agent instructions (read by Claude Code)
├── pyproject.toml         # Python dependencies
├── credentials.json       # Google OAuth client ID (you create this)
├── src/
│   ├── sheets/
│   │   ├── client.py      # Google Sheets API wrapper (with caching + retry)
│   │   ├── auth.py        # OAuth handling
│   │   └── url.py         # URL parsing utilities
│   ├── analysis/
│   │   ├── scan.py        # Full formula scan and anomaly detection
│   │   └── snapshot.py    # Model snapshot and diff utilities
│   ├── agent/
│   │   └── core.py        # Standalone CLI agent (alternative interface)
│   └── tools/
│       └── ...            # Tool definitions used by the CLI agent
└── .claude/
    └── commands/          # Slash command definitions
        ├── audit.md
        ├── breakeven.md
        ├── connect.md
        ├── create.md
        ├── diff.md
        ├── explain.md
        ├── inspect.md
        ├── modify.md
        ├── scan.md
        ├── scenario.md
        └── snapshot.md
```

## Troubleshooting

### "Access blocked" during Google sign-in
You skipped the OAuth consent screen step. Go to Google Cloud Console > APIs & Services > OAuth consent screen, set up the screen, and add your email as a test user under "Test users".

### "Unable to parse range" error
The sheet name may have changed or doesn't exist. Use `/connect <url>` to see the available sheet tabs.

### Authentication token issues
Delete `~/.fpa-agent/token.json` and run any command again to re-authenticate.

### "No spreadsheet connected" error
Run `/connect <url>` at the start of each session. The connection doesn't persist between Claude Code sessions.

### `credentials.json` not found
Make sure you saved the downloaded OAuth JSON file as `credentials.json` in the repo root (next to `CLAUDE.md`).

### Claude Code not found
Make sure Node.js 18+ is installed and `npm install -g @anthropic-ai/claude-code` completed without errors. Try `claude --version` to confirm.

## License

Apache 2.0 - See [LICENSE](LICENSE)
