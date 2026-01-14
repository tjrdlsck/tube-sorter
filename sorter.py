import os
import json
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 설정 파일 경로
TOKEN_FILE = 'token.json'
RULES_FILE = 'rules.json'
STATE_FILE = 'state.json'

def get_youtube_client():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"{TOKEN_FILE} not found. Run authorize.py first.")
    
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise
            
    return build('youtube', 'v3', credentials=creds)

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None
    return None

def validate_rules(rules_data):
    """규칙 데이터의 유효성을 검사합니다."""
    if not rules_data or 'rules' not in rules_data:
        raise ValueError("Invalid rules format: 'rules' key is missing.")
    for i, rule in enumerate(rules_data['rules']):
        if 'keyword' not in rule:
            raise ValueError(f"Rule at index {i} is missing 'keyword'.")
    return True

def save_state(last_published_at):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last_published_at': last_published_at}, f)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

def get_uploads_playlist_id(youtube, channel_id):
    request = youtube.channels().list(part="contentDetails", id=channel_id)
    response = request.execute()
    if not response.get('items'):
        raise ValueError(f"Channel not found: {channel_id}")
    return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

def add_video_to_playlist(youtube, video_id, playlist_id):
    try:
        request = youtube.playlistItems().insert(
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

def get_user_playlists(youtube):
    """현재 로그인한 사용자의 모든 재생목록을 가져와 {제목: ID} 맵을 반환합니다."""
    playlists = {}
    next_page_token = None
    try:
        while True:
            request = youtube.playlists().list(
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

def find_playlist_id_by_keyword(keyword, user_playlists):
    """사용자의 재생목록 중 키워드가 포함된 가장 적절한 재생목록 ID를 찾습니다."""
    def normalize(text):
        return "".join(text.split()).lower()

    normalized_keyword = normalize(keyword)
    for title, pl_id in user_playlists.items():
        if normalized_keyword in normalize(title):
            return pl_id
    return None

def classify_video(video_title, rules_data, user_playlists):
    """
    영상 제목을 기반으로 규칙을 매칭하고 대상 재생목록 ID를 반환합니다.
    공백/대소문자를 무시하며, 긴 키워드에 우선순위를 둡니다.
    """
    def normalize(text):
        return "".join(text.split()).lower()

    normalized_title = normalize(video_title)
    # 긴 키워드 우선 매칭 (방어적 코딩)
    sorted_rules = sorted(
        rules_data.get('rules', []),
        key=lambda x: len(x['keyword']),
        reverse=True
    )

    for rule in sorted_rules:
        keyword = rule['keyword']
        normalized_keyword = normalize(keyword)
        if normalized_keyword in normalized_title:
            target_id = find_playlist_id_by_keyword(keyword, user_playlists)
            if target_id:
                return target_id, keyword
    return None, None



def main():
    try:
        youtube = get_youtube_client()
        rules_data = load_json(RULES_FILE)
        validate_rules(rules_data)
        
        state = load_json(STATE_FILE) or {'last_published_at': '1970-01-01T00:00:00Z'}
        last_ts = state.get('last_published_at', '1970-01-01T00:00:00Z')
        
        channel_id = os.getenv("TARGET_CHANNEL_ID")
        if not channel_id:
            logger.error("TARGET_CHANNEL_ID not found in .env")
            return

        # 0. 재생목록 정보 로드
        logger.info("Fetching playlists for keyword matching...")
        user_playlists = get_user_playlists(youtube)

        # 1. 업로드된 동영상 목록 가져오기
        uploads_id = get_uploads_playlist_id(youtube, channel_id)
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_id,
            maxResults=20
        )
        response = request.execute()
        
        new_videos = []
        for item in response.get('items', []):
            published_at = item['snippet']['publishedAt']
            if published_at > last_ts:
                new_videos.append({
                    'id': item['contentDetails']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': published_at
                })

        if not new_videos:
            logger.info("No new videos found.")
            return

        # 2. 분류 및 등록 (과거 순 정렬)
        new_videos.sort(key=lambda x: x['published_at'])
        
        # 처리 개수 제한 (API 할당량 관리 및 테스트용)
        max_count = os.getenv("MAX_PROCESS_COUNT")
        if max_count:
            try:
                max_count = int(max_count)
                if len(new_videos) > max_count:
                    logger.info(f"Limiting process count to {max_count} (Total new: {len(new_videos)})")
                    new_videos = new_videos[:max_count]
            except ValueError:
                logger.warning(f"Invalid MAX_PROCESS_COUNT value: {max_count}. Processing all.")

        latest_published_at = last_ts
        
        for video in new_videos:
            logger.info(f"Processing: {video['title']}")
            
            playlist_id, matched_keyword = classify_video(video['title'], rules_data, user_playlists)
            
            if playlist_id:
                logger.info(f" -> Matched '{matched_keyword}'. Adding to playlist {playlist_id}...")
                if add_video_to_playlist(youtube, video['id'], playlist_id):
                    logger.info(" -> Success!")
                else:
                    logger.warning(" -> Failed to add video.")
            else:
                logger.info(" -> No matching rule or playlist found.")
            
            latest_published_at = video['published_at']

        # 3. 상태 저장
        save_state(latest_published_at)
        logger.info(f"Update complete. Latest timestamp: {latest_published_at}")

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
