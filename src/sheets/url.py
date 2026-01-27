"""Google Sheets URL parsing utilities."""

import re


def extract_spreadsheet_id(url_or_id: str) -> str:
    """Extract the spreadsheet ID from a Google Sheets URL or return as-is if already an ID.

    Accepts:
        - Full URL: https://docs.google.com/spreadsheets/d/1ABC.../edit#gid=0
        - Short URL: https://docs.google.com/spreadsheets/d/1ABC...
        - Just the ID: 1ABC...

    Args:
        url_or_id: A Google Sheets URL or spreadsheet ID.

    Returns:
        The spreadsheet ID.

    Raises:
        ValueError: If the URL format is not recognized.
    """
    # If it doesn't look like a URL, assume it's already an ID
    if not url_or_id.startswith("http"):
        # Basic validation - IDs are typically 44 chars, alphanumeric with - and _
        if re.match(r"^[a-zA-Z0-9_-]+$", url_or_id):
            return url_or_id
        raise ValueError(f"Invalid spreadsheet ID format: {url_or_id}")

    # Try to extract ID from URL
    # Format: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/...
    patterns = [
        r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(
        f"Could not extract spreadsheet ID from URL: {url_or_id}\n"
        "Expected format: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/..."
    )
