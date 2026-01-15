import os
import logging
from dotenv import load_dotenv
from youtube_service import YouTubeService
from rule_engine import RuleEngine
from storage import load_json, save_state, validate_rules

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 설정 파일 경로
TOKEN_FILE = 'token.json'
RULES_FILE = 'rules.json'
STATE_FILE = 'state.json'

def main():
    load_dotenv(override=True)
    
    try:
        # 1. 초기화 (의존성 주입 형태의 구성)
        youtube_service = YouTubeService(TOKEN_FILE)
        
        rules_data = load_json(RULES_FILE)
        validate_rules(rules_data)
        rule_engine = RuleEngine(rules_data)
        
        state = load_json(STATE_FILE) or {'last_published_at': '1970-01-01T00:00:00Z'}
        last_ts = state.get('last_published_at', '1970-01-01T00:00:00Z')
        
        channel_id = os.getenv("TARGET_CHANNEL_ID")
        if not channel_id:
            logger.error("TARGET_CHANNEL_ID not found in .env")
            return

        # 2. 재생목록 및 영상 데이터 로드
        logger.info("Fetching user playlists and new videos...")
        user_playlists = youtube_service.get_user_playlists()
        uploads_id = youtube_service.get_uploads_playlist_id(channel_id)
        new_videos = youtube_service.get_new_videos(uploads_id, last_ts)

        if not new_videos:
            logger.info("No new videos found.")
            return

        # 3. 분류 및 처리 (과거 순 정렬)
        new_videos.sort(key=lambda x: x.published_at)
        
        # 처리 개수 제한 설정 로드
        max_count_env = os.getenv("MAX_PROCESS_COUNT")
        max_count = int(max_count_env) if max_count_env and max_count_env.isdigit() else 10
        
        processed_count = 0
        latest_published_at = last_ts
        
        for video in new_videos:
            # 설정된 처리 제한(실제 추가 시도 횟수)에 도달하면 중단
            if processed_count >= max_count:
                logger.info(f"Reached MAX_PROCESS_COUNT ({max_count}). Stopping batch.")
                break

            logger.info(f"Processing: {video.title}")
            
            playlist_id, matched_keyword = rule_engine.classify_video(video.title, user_playlists)
            
            if playlist_id:
                # 중복 체크 (1 유닛 소모)
                if youtube_service.is_video_in_playlist(video.id, playlist_id):
                    logger.info(f" -> Matched '{matched_keyword}', but already in playlist. Skipping (Quota saved).")
                else:
                    # 실제 추가 (50 유닛 소모)
                    logger.info(f" -> Matched '{matched_keyword}'. Adding to playlist {playlist_id}...")
                    if youtube_service.add_video_to_playlist(video.id, playlist_id):
                        logger.info(" -> Success!")
                        processed_count += 1 # 실제 작업을 수행했을 때만 카운트 증가
                    else:
                        logger.warning(" -> Failed to add video.")
            else:
                logger.info(" -> No matching rule or playlist found.")
            
            # 건너뛰었거나 처리했거나, 해당 시점까지는 확인 완료됨을 기록
            latest_published_at = video.published_at

        # 4. 최종 상태 저장
        save_state(STATE_FILE, latest_published_at)
        logger.info(f"Update complete. Latest timestamp: {latest_published_at}")

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()