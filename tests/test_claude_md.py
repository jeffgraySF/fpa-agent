"""Structural consistency checks for CLAUDE.md and skill files."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
COMMANDS_DIR = ROOT / ".claude" / "commands"


def _read(path: Path) -> str:
    return path.read_text()


# ── Welcome message matches available commands ────────────────────────────


def test_welcome_message_lists_all_commands():
    """Every .md file in .claude/commands/ should appear in the welcome message."""
    text = _read(CLAUDE_MD)
    welcome_match = re.search(r"## Welcome Message.*?```\n(.*?)```", text, re.DOTALL)
    assert welcome_match, "Could not find Welcome Message code block in CLAUDE.md"
    welcome_block = welcome_match.group(1)

    command_files = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))
    assert command_files, "No command files found in .claude/commands/"

    for cmd in command_files:
        assert f"/{cmd}" in welcome_block, (
            f"Command /{cmd} exists in .claude/commands/ but is missing from welcome message"
        )


def test_no_phantom_commands_in_welcome():
    """Welcome message should not list commands that don't have a command file."""
    text = _read(CLAUDE_MD)
    welcome_match = re.search(r"## Welcome Message.*?```\n(.*?)```", text, re.DOTALL)
    assert welcome_match
    welcome_block = welcome_match.group(1)

    listed_commands = re.findall(r"/(\w+)", welcome_block)
    command_files = {p.stem for p in COMMANDS_DIR.glob("*.md")}

    for cmd in listed_commands:
        assert cmd in command_files, (
            f"/{cmd} is listed in welcome message but has no .claude/commands/{cmd}.md"
        )


# ── Code examples reference real modules ──────────────────────────────────


def test_python_imports_in_skills_are_valid():
    """Python import paths in skill files should correspond to real modules."""
    for skill_file in COMMANDS_DIR.glob("*.md"):
        text = skill_file.read_text()
        for dotted in re.findall(r"from (src\.\S+) import", text):
            module_path = ROOT / dotted.replace(".", "/")
            assert (
                module_path.with_suffix(".py").exists()
                or (module_path / "__init__.py").exists()
            ), f"In {skill_file.name}: '{dotted}' does not resolve to a real module"
