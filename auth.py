import os
import sys
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.appendonly"
]

CONFIG_DIR = Path.home() / ".config" / "gphotos-uploader"
TOKEN_PATH = CONFIG_DIR / "token.json"
CREDENTIALS_PATHS = [
    CONFIG_DIR / "credentials.json",
    Path(__file__).parent / "credentials.json",
    Path.cwd() / "credentials.json"
]

class CredentialsNotFoundError(FileNotFoundError):
    pass

def find_credentials_file() -> Path:
    for path in CREDENTIALS_PATHS:
        if path.is_file():
            return path
    raise CredentialsNotFoundError(
        "OAuth client configuration file (credentials.json) was not found.\n"
        f"Please place credentials.json in one of the following locations:\n"
        f"  1. {CONFIG_DIR / 'credentials.json'}\n"
        f"  2. {Path(__file__).parent / 'credentials.json'}\n\n"
        "Quick setup instructions:\n"
        "1. Open Google Cloud Console (https://console.cloud.google.com/) and create a project\n"
        "2. Enable 'Photos Library API'\n"
        "3. Configure OAuth consent screen (External, add your Google account as a Test user)\n"
        "4. Go to Credentials > Create Credentials > OAuth client ID (Type: Desktop App)\n"
        "5. Download the client secret JSON file and save it to the path above."
    )

def get_credentials(interactive: bool = True) -> Credentials:
    """Load authorized user credentials or initiate local server OAuth flow."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            print(f"Warning: Failed to load existing token: {e}", file=sys.stderr)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Notice: Token refresh failed ({e}). Re-authenticating...", file=sys.stderr)
                creds = None

        if not creds:
            if not interactive:
                raise RuntimeError("Token missing or expired. Run interactive authentication first.")
            
            cred_file = find_credentials_file()
            print("Opening browser for Google account authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save token
            with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
            TOKEN_PATH.chmod(0o600)
            print("Authentication successful. Token saved securely.")

    return creds

def check_status():
    """Check configuration and credential status."""
    has_creds = any(p.is_file() for p in CREDENTIALS_PATHS)
    has_token = TOKEN_PATH.is_file()
    token_valid = False
    if has_token:
        try:
            c = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            token_valid = c.valid or (c.expired and bool(c.refresh_token))
        except Exception:
            token_valid = False
    return {
        "credentials_configured": has_creds,
        "token_saved": has_token,
        "token_valid": token_valid,
        "config_dir": str(CONFIG_DIR)
    }

if __name__ == "__main__":
    try:
        creds = get_credentials()
        print("Authentication Status: Valid (OK)")
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
