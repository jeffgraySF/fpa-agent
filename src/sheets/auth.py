"""Google Sheets authentication handling.

OAuth Flow Overview:
───────────────────
1. Your app needs a "credentials.json" file (OAuth Client ID from Google Cloud Console)
   - This identifies YOUR APPLICATION, not the user
   - Create at: https://console.cloud.google.com/apis/credentials
   - Choose "Desktop app" as the application type

2. When a user runs the agent for the first time:
   - Browser opens to Google login
   - User logs in with ANY Google account (personal or corporate/Workspace)
   - User approves the permissions your app requests
   - A token is saved locally (token.pickle) - this IS sensitive

3. Subsequent runs use the saved token (auto-refreshes when expired)

For Corporate/Google Workspace Users:
────────────────────────────────────
- The OAuth flow works the same way
- BUT: the organization admin may need to approve your app
- Configure your OAuth consent screen as "Internal" for org-only apps
- Or submit for verification if you want external users
"""

import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes determine what the app can access
# spreadsheets = read/write sheets (not other Drive files)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Default paths - tokens go in user's home directory for safety
DEFAULT_TOKEN_DIR = Path.home() / ".fpa-agent"
DEFAULT_TOKEN_PATH = DEFAULT_TOKEN_DIR / "token.json"


def get_token_path() -> Path:
    """Get the path where the user's token should be stored.

    Stores in ~/.fpa-agent/token.json by default (user's home directory).
    Can be overridden with GOOGLE_TOKEN_PATH env var.
    """
    custom_path = os.getenv("GOOGLE_TOKEN_PATH")
    if custom_path:
        return Path(custom_path)
    return DEFAULT_TOKEN_PATH


def get_credentials_path() -> Path:
    """Get the path to the OAuth client credentials file.

    Looks for credentials.json in current directory by default.
    Can be overridden with GOOGLE_CREDENTIALS_PATH env var.
    """
    custom_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    if custom_path:
        return Path(custom_path)
    return Path("credentials.json")


def get_credentials() -> Credentials:
    """Load or create Google OAuth credentials.

    First-time users will see a browser window to authorize the app.
    The token is then saved locally for future use.

    Returns:
        Valid Google OAuth credentials.

    Raises:
        FileNotFoundError: If credentials.json doesn't exist and no valid token exists.
    """
    token_path = get_token_path()
    credentials_path = get_credentials_path()

    # Also check for legacy pickle format in current directory
    legacy_pickle_path = Path("token.pickle")

    creds = None

    # Load existing token if available (try JSON first, then legacy pickle)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    elif legacy_pickle_path.exists():
        # Support legacy pickle format for backward compatibility
        import pickle
        with open(legacy_pickle_path, "rb") as f:
            creds = pickle.load(f)
        # Migrate to new JSON format
        print(f"Migrating credentials from {legacy_pickle_path} to {token_path}...")
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        try:
            os.chmod(token_path, 0o600)
        except (OSError, AttributeError):
            pass

    # If no valid credentials, we need to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expired but we can refresh it
            from google.auth.transport.requests import Request
            try:
                creds.refresh(Request())
            except Exception:
                # Refresh failed, need to re-authenticate
                creds = None

        if not creds:
            # Need to run the OAuth flow
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"\nOAuth credentials file not found at: {credentials_path}\n\n"
                    "To set up Google Sheets access:\n"
                    "1. Go to https://console.cloud.google.com/apis/credentials\n"
                    "2. Create an OAuth 2.0 Client ID (Desktop app)\n"
                    "3. Download the JSON file\n"
                    "4. Save it as 'credentials.json' in the project directory\n"
                )

            print("\n" + "=" * 50)
            print("Google Sheets Authorization Required")
            print("=" * 50)
            print("A browser window will open for you to log in.")
            print("You can use any Google account (personal or work).")
            print("=" * 50 + "\n")

            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for next run
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

        # Set restrictive permissions on the token file (Unix only)
        try:
            os.chmod(token_path, 0o600)
        except (OSError, AttributeError):
            pass  # Windows or permission error, skip

    return creds


def clear_credentials():
    """Remove stored credentials, forcing re-authentication on next use."""
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()
        print(f"Credentials cleared from {token_path}")
    else:
        print("No stored credentials found.")


def show_auth_status():
    """Show the current authentication status."""
    token_path = get_token_path()
    credentials_path = get_credentials_path()

    print("\nAuthentication Status")
    print("=" * 40)

    print(f"\nOAuth Client (credentials.json):")
    if credentials_path.exists():
        print(f"  ✓ Found at: {credentials_path}")
    else:
        print(f"  ✗ Not found at: {credentials_path}")

    print(f"\nUser Token:")
    if token_path.exists():
        print(f"  ✓ Found at: {token_path}")
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds.valid:
                print("  ✓ Token is valid")
            elif creds.expired:
                print("  ⚠ Token is expired (will auto-refresh)")
            else:
                print("  ⚠ Token state unknown")
        except Exception as e:
            print(f"  ✗ Error reading token: {e}")
    else:
        print(f"  ✗ Not found (will authenticate on first use)")
        print(f"     Will be saved to: {token_path}")

    print()
