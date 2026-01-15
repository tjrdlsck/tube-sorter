import pytest
import time
from unittest.mock import MagicMock, patch
from youtube_service import YouTubeService
from rule_engine import RuleEngine

@pytest.fixture
def mock_service():
    with patch.object(YouTubeService, '_load_credentials', return_value=MagicMock()):
        service = YouTubeService('fake_token.json')
        service.client = MagicMock()
        return service

def test_classify_video_performance_large_rules():
    """시나리오 1: 500개의 규칙과 500개의 재생목록 매칭 성능 테스트"""
    rules_data = {
        "rules": [{"keyword": f"Keyword_{i}"} for i in range(500)]
    }
    user_playlists = {f"Playlist Title Keyword_{i}": f"PL_ID_{i}" for i in range(500)}
    engine = RuleEngine(rules_data)
    
    # 마지막(499번째) 규칙에 매칭되는 영상 제목
    video_title = "This video matches Keyword_499 specifically"
    
    start_time = time.time()
    iterations = 1000
    for _ in range(iterations):
        playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    end_time = time.time()
    
    assert playlist_id == "PL_ID_499"
    assert keyword == "Keyword_499"
    avg_time = (end_time - start_time) / iterations
    print(f"\n[Performance] Avg classification time with 500 rules: {avg_time*1000:.4f}ms")

def test_get_user_playlists_high_volume(mock_service):
    """시나리오 2: 500개의 재생목록을 페이지네이션하여 맵으로 변환하는 로직 테스트"""
    responses = []
    for i in range(10):
        next_token = f"token_{i+1}" if i < 9 else None
        items = [{'id': f'ID_{i*50+j}', 'snippet': {'title': f'Title_{i*50+j}'}} for j in range(50)]
        responses.append({'items': items, 'nextPageToken': next_token})
        
    mock_service.client.playlists.return_value.list.return_value.execute.side_effect = responses
    
    start_time = time.time()
    result = mock_service.get_user_playlists()
    end_time = time.time()
    
    assert len(result) == 500
    assert result['Title_499'] == 'ID_499'
    print(f"[Performance] Mapped 500 playlists in {end_time - start_time:.4f}s")
