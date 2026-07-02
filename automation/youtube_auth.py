import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Set up paths for credential files
CREDENTIALS_DIR = os.path.join(os.path.dirname(__file__), "credentials")
os.makedirs(CREDENTIALS_DIR, exist_ok=True)

from helper.secrets import Secrets

secrets = Secrets()
youtube_creds_path = secrets.write_temp_credentials(CREDENTIALS_DIR)
CLIENT_SECRETS_FILE = youtube_creds_path or os.path.join(CREDENTIALS_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.pickle")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def authenticate_youtube():
    credentials = None

    # Load existing credentials if available
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as token:
                credentials = pickle.load(token)
            print("📂 Loaded credentials from credentials directory")
        except Exception as e:
            print(f"⚠️ Error loading token file: {e}")
            credentials = None

    # Check if credentials are invalid or expired
    if not credentials or not credentials.valid:
        try:
            if credentials and credentials.expired and credentials.refresh_token:
                # Refresh the token if possible
                credentials.refresh(Request())
                print("🔄 Token refreshed successfully!")
            else:
                # Check if client secrets file exists
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    raise FileNotFoundError(f"Client secrets file not found at: {CLIENT_SECRETS_FILE}")

                # Prompt user for re-authentication if no valid refresh token
                print("🔑 Token expired or invalid. Re-authenticating...")
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                credentials = flow.run_local_server(port=8080)
        except Exception as e:
            print(f"❌ Error during token refresh or authentication: {e}")
            if os.path.exists(CLIENT_SECRETS_FILE):
                print("⚠️ Re-authenticating...")
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                credentials = flow.run_local_server(port=8080)
            else:
                raise FileNotFoundError(f"Client secrets file not found at: {CLIENT_SECRETS_FILE}")

        # Save the new or refreshed credentials
        try:
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(credentials, token)
                print("💾 Token saved successfully in credentials directory!")
        except Exception as e:
            print(f"⚠️ Error saving token file: {e}")

    print("✅ Authentication successful!")
    return credentials
