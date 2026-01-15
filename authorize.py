import os
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle

# 재생목록 수정을 위해 필요한 권한 범위 (Scopes)
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def main():
    creds = None
    # 기존에 생성된 token.json이 있는지 확인합니다.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 인증 정보가 없거나 만료된 경우 새로 인증을 진행합니다.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            creds.refresh(Request())
        else:
            print("Starting new authentication flow...")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 인증된 정보를 token.json에 저장합니다.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("Successfully saved token.json")

if __name__ == "__main__":
    main()
