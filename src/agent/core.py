"""Core agent loop using Anthropic's Claude API."""

import json
import os
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

from googleapiclient.discovery import build

from src.sheets import SheetsClient
from src.sheets.auth import clear_credentials, get_credentials, show_auth_status
from src.tools import TOOLS, execute_tool

# Load environment variables from .env file
load_dotenv()

# Load the instructions and specs to include in the system prompt
REPO_ROOT = Path(__file__).parent.parent.parent
INSTRUCTIONS = (REPO_ROOT / "INSTRUCTIONS.md").read_text()
TEMPLATE_SPECS = (REPO_ROOT / "template_specs.md").read_text()

SYSTEM_PROMPT = f"""You are an FP&A (Financial Planning & Analysis) assistant that helps users work with their Google Sheets financial models.

## Your Capabilities
- Connect to any Google Sheets spreadsheet the user shares with you
- Read cell values and formulas
- Write values and formulas to cells
- Append new rows (for adding employees, customers, etc.)
- Clear cell ranges
- Apply formatting (number formats, fonts, bold)
- Freeze rows/columns

## Workflow: Understanding a New Spreadsheet

When a user shares a Google Sheets link with you, follow this process:

### 1. Connect and Explore Structure
- Use `connect_to_spreadsheet` with the URL they provide
- Use `get_spreadsheet_info` to see all sheets
- Use `inspect_sheet` on key sheets to understand their layout

### 2. Understand the Model Logic
Trace through the formulas to understand how the model works. Focus on:
- **What drives revenue/ARR?** (customer data, pricing, contracts, etc.)
- **What drives costs/burn?** (headcount, salaries, other expenses)
- **How do sheets connect?** (which sheets feed into which summaries)

### 3. Verify Your Understanding
Before making any modifications, articulate your understanding back to the user:
- "Here's how I understand your model works..."
- "ARR appears to be driven by..."
- "Cash burn appears to be driven by..."
- "Does this match your understanding?"

Only proceed with modifications once the user confirms you understand the model correctly.

## Reference: Ideal FP&A Model Structure

The following describes an ideal FP&A model structure. User models may differ - your job is to understand THEIR model, not force it to match this template. Use this as context for what good FP&A models typically contain.

### Formula Best Practices
{INSTRUCTIONS}

### Example Template Structure
{TEMPLATE_SPECS}

## Working with the User
- Before making changes, read the relevant cells to understand the current state
- Explain what you're about to do before making modifications
- After writing, confirm what was changed
- If a request is ambiguous, ask for clarification
- When adding formulas, follow dynamic reference patterns (never hardcode names, use cell references)
- If the user's model differs significantly from the template, adapt to THEIR structure
"""


class Agent:
    """Conversational agent for FP&A Google Sheets operations."""

    def __init__(self, spreadsheet_id: str | None = None):
        """Initialize the agent.

        Args:
            spreadsheet_id: Optional Google Sheets spreadsheet ID or URL.
                           If not provided, user can connect via chat.
        """
        self.client = anthropic.Anthropic()
        # Allow starting without a spreadsheet - user can connect via chat
        try:
            self.sheets = SheetsClient(spreadsheet_id)
        except ValueError:
            # No spreadsheet configured - that's OK, user will provide one
            self.sheets = SheetsClient.__new__(SheetsClient)
            self.sheets.spreadsheet_id = None
            creds = get_credentials()
            self.sheets._service = build("sheets", "v4", credentials=creds)

        self.messages: list[dict[str, Any]] = []
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    def chat(self, user_message: str) -> str:
        """Send a message and get a response, handling any tool calls.

        Args:
            user_message: The user's message.

        Returns:
            The assistant's final text response.
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})

        # Run the agent loop
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.messages,
            )

            # Collect the assistant's response content
            assistant_content = response.content
            self.messages.append({"role": "assistant", "content": assistant_content})

            # Check if we need to handle tool calls
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in assistant_content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        print(f"  [Tool: {tool_name}]")

                        try:
                            result = execute_tool(self.sheets, tool_name, tool_input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, default=str),
                            })
                        except Exception as e:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {e}",
                                "is_error": True,
                            })

                # Add tool results and continue the loop
                self.messages.append({"role": "user", "content": tool_results})

            else:
                # No more tool calls, extract and return the text response
                text_parts = [
                    block.text for block in assistant_content if hasattr(block, "text")
                ]
                return "\n".join(text_parts)

    def reset(self):
        """Clear conversation history."""
        self.messages = []


def run_agent(spreadsheet_id: str | None = None):
    """Run the agent in an interactive CLI loop.

    Args:
        spreadsheet_id: Optional spreadsheet ID override.
    """
    print("FP&A Agent")
    print("=" * 50)
    print("Commands:")
    print("  quit, exit  - End the session")
    print("  reset       - Clear conversation history")
    print("  auth        - Show Google authentication status")
    print("  logout      - Clear stored Google credentials")
    print("=" * 50)
    print()

    # Initialize agent (will trigger OAuth if needed)
    try:
        agent = Agent(spreadsheet_id)
    except FileNotFoundError as e:
        print(f"Setup required: {e}")
        return
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return

    # Show connection status on startup
    if agent.sheets.spreadsheet_id:
        try:
            info = agent.sheets.get_spreadsheet_info()
            print(f"Connected to: {info['title']}")
            print(f"Sheets: {', '.join(s['name'] for s in info['sheets'])}")
        except Exception as e:
            print(f"Warning: Could not connect to spreadsheet: {e}")
    else:
        print("No spreadsheet connected yet.")
        print("Share a Google Sheets URL to get started.")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "reset":
            agent.reset()
            print("Conversation history cleared.\n")
            continue

        if user_input.lower() == "auth":
            show_auth_status()
            continue

        if user_input.lower() == "logout":
            clear_credentials()
            print("You'll need to re-authenticate on next run.\n")
            continue

        try:
            response = agent.chat(user_input)
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Entry point for the CLI."""
    run_agent()


if __name__ == "__main__":
    main()
