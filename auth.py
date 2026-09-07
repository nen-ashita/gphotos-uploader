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
        "OAuthクライアント設定ファイル (credentials.json) が見つかりませんでした。\n"
        f"以下のいずれかに配置してください:\n"
        f"  1. {CONFIG_DIR / 'credentials.json'}\n"
        f"  2. {Path(__file__).parent / 'credentials.json'}\n\n"
        "取得手順:\n"
        "1. Google Cloud Console (https://console.cloud.google.com/) でプロジェクトを作成\n"
        "2. 'Photos Library API' を有効化\n"
        "3. OAuth同意画面を設定 (User Type: 外部、テストユーザーに対象アカウントを追加)\n"
        "4. 認証情報 > 認証情報を作成 > OAuthクライアントID (種類: デスクトップ アプリ) を作成\n"
        "5. ダウンロードしたJSONを上記パスに保存してください。"
    )

def get_credentials(interactive: bool = True) -> Credentials:
    """保存された認証トークンを取得、またはOAuth認証フローを実行してトークンを保存します。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            print(f"既存トークンの読み込みエラー: {e}", file=sys.stderr)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"トークンの自動更新に失敗しました: {e}。再認証を実行します。", file=sys.stderr)
                creds = None

        if not creds:
            if not interactive:
                raise RuntimeError("認証トークンが存在しないか期限切れです。一度ターミナル等で対話的認証を実行してください。")
            
            cred_file = find_credentials_file()
            print("ブラウザを開いてGoogleアカウントへのアクセスを承認してください...")
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), SCOPES)
            creds = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
            TOKEN_PATH.chmod(0o600)
            print("認証に成功し、トークンを安全に保存しました。")

    return creds

def check_status():
    """現在の認証ファイルおよびトークンの設定状況を確認します"""
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
        print("認証ステータス: 有効 (OK)")
    except Exception as err:
        print(f"エラー: {err}", file=sys.stderr)
        sys.exit(1)
