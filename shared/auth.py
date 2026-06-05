import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"

GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
GPC_SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]


def load_credentials(json_filename: str, scopes: list[str]) -> service_account.Credentials:
    json_path = CREDENTIALS_DIR / json_filename
    if not json_path.exists():
        raise FileNotFoundError(
            f"Service account key not found: {json_path}\n"
            f"Place your JSON key file in the credentials/ directory."
        )
    return service_account.Credentials.from_service_account_file(str(json_path), scopes=scopes)


def build_gsc_service():
    # GOOGLE_KEY_FILE overrides individual keys — one SA for both services
    key_file = os.environ.get("GOOGLE_KEY_FILE") or os.environ.get(
        "GSC_KEY_FILE", "gsc-service-account.json"
    )
    creds = load_credentials(key_file, GSC_SCOPES)
    return build("searchconsole", "v1", credentials=creds)


def build_gpc_service():
    key_file = os.environ.get("GOOGLE_KEY_FILE") or os.environ.get(
        "GPC_KEY_FILE", "gpc-service-account.json"
    )
    creds = load_credentials(key_file, GPC_SCOPES)
    return build("androidpublisher", "v3", credentials=creds)
