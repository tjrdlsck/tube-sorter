import logging
import os
from typing import List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from models import Video

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self, token_file: str):
        self.token_file = token_file
        self.creds = self._load_credentials()
        self.client = build('youtube', 'v3', credentials=self.creds)

    def _load_credentials(self):
        if not os.path.exists(self.token_file):
            raise FileNotFoundError(f"{self.token_file} not found. Run authorize.py first.")
        
        creds = Credentials.from_authorized_user_file(self.token_file)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                raise
        return creds

    def get_uploads_playlist_id(self, channel_id: str) -> str:
        request = self.client.channels().list(part="contentDetails", id=channel_id)
        response = request.execute()
        if not response.get('items'):
            raise ValueError(f"Channel not found: {channel_id}")
        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    def get_new_videos(self, uploads_playlist_id: str, last_published_at: str) -> List[Video]:
        request = self.client.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=20
        )
        response = request.execute()
        
        new_videos = []
        for item in response.get('items', []):
            published_at = item['snippet']['publishedAt']
            if published_at > last_published_at:
                new_videos.append(Video(
                    id=item['contentDetails']['videoId'],
                    title=item['snippet']['title'],
                    published_at=published_at
                ))
        return new_videos

    def get_user_playlists(self) -> dict:
        playlists = {}
        next_page_token = None
        try:
            while True:
                request = self.client.playlists().list(
                    part="snippet",
                    mine=True,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                for item in response.get('items', []):
                    playlists[item['snippet']['title']] = item['id']
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
        except Exception as e:
            logger.error(f"Failed to fetch user playlists: {e}")
        return playlists

    def is_video_in_playlist(self, video_id: str, playlist_id: str) -> bool:
        """
        [개선사항 2] 멱등성 보장: 영상이 이미 재생목록에 존재하는지 확인합니다.
        """
        try:
            request = self.client.playlistItems().list(
                part="id",
                playlistId=playlist_id,
                videoId=video_id,
                maxResults=1
            )
            response = request.execute()
            return len(response.get('items', [])) > 0
        except Exception as e:
            logger.error(f"Error checking video {video_id} in playlist {playlist_id}: {e}")
            return False

    def add_video_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        # 중복 체크 먼저 수행
        if self.is_video_in_playlist(video_id, playlist_id):
            logger.info(f"Video {video_id} already exists in playlist {playlist_id}. Skipping.")
            return True

        try:
            request = self.client.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            request.execute()
            return True
        except Exception as e:
            logger.error(f"Error adding video {video_id} to playlist {playlist_id}: {e}")
            return False
