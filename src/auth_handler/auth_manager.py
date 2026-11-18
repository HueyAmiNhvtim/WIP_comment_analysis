import os
from dotenv import load_dotenv
import googleapiclient.discovery

from google.auth.exceptions import RefreshError

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

class AuthManager:
    """Centralized Authentication Manager for all platforms."""
    def __init__(self, env_path = ".env"):
        self.youtube_client = None
        self.twitch_client = None
        
        self.__read_env(env_path)
        self.authenticate_all()
    
    def __read_env(self, env_path):
        """Read and initialize the environment variables"""
        load_dotenv(dotenv_path=env_path, override=True)  # Ensures variables from your .env file are loaded into os.environ
        self.ytb_name = os.getenv("YTB_API_SERVICE_NAME", default="youtube")
        self.ytb_version = os.getenv("YTB_API_VERSION", default="v3")
        self.ytb_scopes = os.getenv("YTB_API_SCOPES", default="").split(",")
        self.ytb_token_fp = os.getenv("YTB_TOKEN_FP", default="")
        self.ytb_creds_fp = os.getenv("YTB_CRED_FP", default="")
    
    def authenticate_youtube(self):
        """Authenticate and return the YouTube API client."""
        # Return the cached client if we've already authenticated
        if self.youtube_client:
            return self.youtube_client
            
        creds = None
        if os.path.exists(self.ytb_token_fp):
            creds = Credentials.from_authorized_user_file(self.ytb_token_fp,  self.ytb_scopes)
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                # Possible expired refresh token.
                if os.path.exists(self.ytb_token_fp):
                    os.remove(self.ytb_token_fp)
                creds = None

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.ytb_creds_fp, self.ytb_scopes
            )
            creds = flow.run_local_server(port=0) # May subject to change once we put the whole thing to run within
                                                  # the Docker thingie.
        # Save the credentials for the next run
        with open(self.ytb_token_fp, "w") as token:
            token.write(creds.to_json())
        
        self.youtube_client  = googleapiclient.discovery.build(self.ytb_name, self.ytb_version, credentials=creds)
        return self.youtube_client
        
    def authenticate_twitch(self):
        """Authenticate and return the Twitch API client."""
        if not self.twitch_client:
            # TODO: Implement Twitch OAuth logic here. Yeah, probably for the future tbh.
            self.twitch_client = "twitch_authenticated_client_placeholder"
        return self.twitch_client

    def authenticate_all(self):
        """Authenticate all available platforms in one go."""
        self.authenticate_youtube()
        # self.authenticate_twitch()
        return self
