"""Tests to verify CLAUDE.md and skill files stay consistent with the codebase."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
COMMANDS_DIR = ROOT / ".claude" / "commands"
MODIFY_MD = COMMANDS_DIR / "modify.md"
CREATE_MD = COMMANDS_DIR / "create.md"


def _read(path: Path) -> str:
    return path.read_text()


# ── Welcome message matches available commands ──────────────────────────


def test_welcome_message_lists_all_commands():
    """Every .md file in .claude/commands/ should appear in the welcome message."""
    text = _read(CLAUDE_MD)

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
    text = _read(CLAUDE_MD)

    welcome_match = re.search(
        r"## Welcome Message.*?```\n(.*?)```", text, re.DOTALL
    )
    assert welcome_match
    welcome_block = welcome_match.group(1)

    listed_commands = re.findall(r"/(\w+)", welcome_block)
    command_files = {p.stem for p in COMMANDS_DIR.glob("*.md")}

    for cmd in listed_commands:
        assert (
            cmd in command_files
        ), f"/{cmd} is listed in welcome message but has no .claude/commands/{cmd}.md"


# ── Code examples reference real modules ─────────────────────────────────


def test_python_imports_in_skills_are_valid():
    """Python import paths in skill files should correspond to real modules."""
    for skill_file in COMMANDS_DIR.glob("*.md"):
        text = skill_file.read_text()
        imports = re.findall(r"from (src\.\S+) import", text)
        for dotted in imports:
            module_path = ROOT / dotted.replace(".", "/")
            assert (
                module_path.with_suffix(".py").exists()
                or (module_path / "__init__.py").exists()
            ), f"In {skill_file.name}: import '{dotted}' does not resolve to a real module"


# ── CLAUDE.md required sections ──────────────────────────────────────────


CLAUDE_MD_REQUIRED_SECTIONS = [
    "## Quick Reference",
    "## Formula Standards",
    "## Audit Checklist",
    "## Skill Design Principles",
]


def test_claude_md_required_sections():
    text = _read(CLAUDE_MD)
    for section in CLAUDE_MD_REQUIRED_SECTIONS:
        assert section in text, f"Missing required section in CLAUDE.md: {section}"


# ── Formula standards (CLAUDE.md) ─────────────────────────────────────────


def test_no_hardcoded_labels_rule():
    assert "No hardcoded labels" in _read(CLAUDE_MD)


def test_skip_headers_rule():
    assert "Skip headers" in _read(CLAUDE_MD)


def test_date_formula_rule():
    """Dates-as-real-dates rule must be in CLAUDE.md Formula Standards."""
    text = _read(CLAUDE_MD)
    assert "=DATE()" in text


# ── Audit checklist (CLAUDE.md) ───────────────────────────────────────────


def test_audit_checklist_has_items():
    text = _read(CLAUDE_MD)
    checklist_match = re.search(
        r"## Audit Checklist\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    assert checklist_match, "Could not find Audit Checklist section"
    items = re.findall(r"^\d+\.", checklist_match.group(1), re.MULTILINE)
    assert len(items) >= 3, f"Expected at least 3 audit checklist items, found {len(items)}"


# ── modify.md content ─────────────────────────────────────────────────────


def test_data_type_rules_in_modify():
    """Data type rules must be documented in modify.md."""
    text = _read(MODIFY_MD)
    assert "Data Type Rules" in text
    assert "=DATE(" in text


def test_number_format_patterns_in_modify():
    """Key number format patterns must be documented in modify.md."""
    text = _read(MODIFY_MD)
    assert "$#,##0" in text, "Currency format pattern missing from modify.md"
    assert "0.0%" in text, "Percentage format pattern missing from modify.md"


def test_reconciliation_tiers_in_modify():
    """All three reconciliation tiers must be documented in modify.md."""
    text = _read(MODIFY_MD)
    assert "Tier 1" in text
    assert "Tier 2" in text
    assert "Tier 3" in text


def test_test_before_bulk_write_in_modify():
    """Test Before Bulk Write guidance must be in modify.md."""
    assert "Test Before Bulk Write" in _read(MODIFY_MD)


# ── create.md content ─────────────────────────────────────────────────────


def test_model_structure_in_create():
    """Sheet dependency diagram must be in create.md."""
    text = _read(CREATE_MD)
    assert "Headcount Input" in text
    assert "Monthly Summary" in text


def test_number_format_patterns_in_create():
    """Number format patterns must also be in create.md."""
    text = _read(CREATE_MD)
    assert "$#,##0" in text, "Currency format pattern missing from create.md"
    assert "0.0%" in text, "Percentage format pattern missing from create.md"
