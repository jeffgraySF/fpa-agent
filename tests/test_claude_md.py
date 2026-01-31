"""Tests to verify CLAUDE.md stays consistent with the codebase."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
COMMANDS_DIR = ROOT / ".claude" / "commands"
SRC_DIR = ROOT / "src"


def _read_claude_md() -> str:
    return CLAUDE_MD.read_text()


# ── Welcome message matches available commands ──────────────────────────


def test_welcome_message_lists_all_commands():
    """Every .md file in .claude/commands/ should appear in the welcome message."""
    text = _read_claude_md()

    # Extract the welcome message block (between the ``` fences under ## Welcome Message)
    welcome_match = re.search(
        r"## Welcome Message.*?```\n(.*?)```", text, re.DOTALL
    )
    assert welcome_match, "Could not find Welcome Message code block in CLAUDE.md"
    welcome_block = welcome_match.group(1)

    command_files = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))
    assert command_files, "No command files found in .claude/commands/"

    for cmd in command_files:
        assert (
            f"/{cmd}" in welcome_block
        ), f"Command /{cmd} exists in .claude/commands/ but is missing from welcome message"


def test_no_phantom_commands_in_welcome():
    """Welcome message should not list commands that don't have a command file."""
    text = _read_claude_md()

    welcome_match = re.search(
        r"## Welcome Message.*?```\n(.*?)```", text, re.DOTALL
    )
    assert welcome_match
    welcome_block = welcome_match.group(1)

    # Extract /command names from welcome message
    listed_commands = re.findall(r"/(\w+)", welcome_block)
    command_files = {p.stem for p in COMMANDS_DIR.glob("*.md")}

    for cmd in listed_commands:
        assert (
            cmd in command_files
        ), f"/{cmd} is listed in welcome message but has no .claude/commands/{cmd}.md"


# ── Code examples reference real modules ─────────────────────────────────


def test_python_imports_are_valid():
    """Python import paths in CLAUDE.md should correspond to real modules."""
    text = _read_claude_md()

    # Find all `from src.x.y import Z` patterns
    imports = re.findall(r"from (src\.\S+) import", text)
    assert imports, "Expected at least one src import example in CLAUDE.md"

    for dotted in imports:
        # Convert dotted path to filesystem path
        module_path = ROOT / dotted.replace(".", "/")
        # Could be a package (directory with __init__.py) or a module (.py file)
        assert (
            module_path.with_suffix(".py").exists()
            or (module_path / "__init__.py").exists()
        ), f"Import path '{dotted}' does not resolve to a real module"


# ── Formula standards are documented ─────────────────────────────────────


def test_formula_standards_section_exists():
    """CLAUDE.md must have a Formula Standards section."""
    text = _read_claude_md()
    assert "## Formula Standards" in text


def test_no_hardcoded_labels_rule():
    """The 'no hardcoded labels' rule must be documented."""
    text = _read_claude_md()
    assert "No hardcoded labels" in text


def test_skip_headers_rule():
    """The 'skip headers in ranges' rule must be documented."""
    text = _read_claude_md()
    assert "Skip headers" in text


# ── Data type rules ──────────────────────────────────────────────────────


def test_data_type_rules_section_exists():
    text = _read_claude_md()
    assert "## Data Type Rules" in text


def test_date_formula_rule():
    """Dates must use =DATE() formulas, not text strings."""
    text = _read_claude_md()
    assert "=DATE(" in text
    assert "Never write text" in text or "never text strings" in text


# ── Required sections exist ──────────────────────────────────────────────


REQUIRED_SECTIONS = [
    "## Quick Reference",
    "## Reading Sheets",
    "## Formula Standards",
    "## Data Type Rules",
    "## Number Formatting",
    "## Model Structure",
    "## Test Before Bulk Write",
    "## Audit Checklist",
    "## Reconciliation Checks",
]


def test_required_sections_present():
    text = _read_claude_md()
    for section in REQUIRED_SECTIONS:
        assert section in text, f"Missing required section: {section}"


# ── Reconciliation tiers ─────────────────────────────────────────────────


def test_reconciliation_tiers():
    """All three reconciliation tiers must be documented."""
    text = _read_claude_md()
    assert "Tier 1" in text
    assert "Tier 2" in text
    assert "Tier 3" in text


# ── Audit checklist items ────────────────────────────────────────────────


def test_audit_checklist_has_items():
    """Audit checklist should have numbered items."""
    text = _read_claude_md()
    checklist_match = re.search(
        r"## Audit Checklist\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    assert checklist_match, "Could not find Audit Checklist section"
    items = re.findall(r"^\d+\.", checklist_match.group(1), re.MULTILINE)
    assert len(items) >= 3, f"Expected at least 3 audit checklist items, found {len(items)}"


# ── Number format patterns ───────────────────────────────────────────────


def test_number_format_patterns():
    """Key number format patterns must be documented."""
    text = _read_claude_md()
    assert "$#,##0" in text, "Currency format pattern missing"
    assert "0.0%" in text, "Percentage format pattern missing"
