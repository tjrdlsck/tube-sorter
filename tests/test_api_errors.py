import pytest
from unittest.mock import MagicMock, patch
from googleapiclient.errors import HttpError
from youtube_service import YouTubeService

@pytest.fixture
def mock_service():
    """YouTubeService 인스턴스를 생성하고 내부 client를 모킹합니다."""
    # _load_credentials가 파일을 읽지 않도록 모킹
    with patch.object(YouTubeService, '_load_credentials', return_value=MagicMock()):
        service = YouTubeService('fake_token.json')
        service.client = MagicMock()
        return service

def create_http_error(status, message, reason="error"):
    """Google API의 HttpError 객체를 시뮬레이션하기 위한 헬퍼 함수"""
    resp = MagicMock()
    resp.status = status
    resp.reason = reason
    content = bytes(f'{{"error": {{"message": "{message}", "errors": [{{"reason": "{reason}"}}]}}}}', 'utf-8')
    return HttpError(resp, content)

def test_get_uploads_playlist_id_channel_not_found(mock_service):
    """시나리오 1: 존재하지 않는 채널 ID 조회 시 ValueError 발생 여부"""
    mock_service.client.channels.return_value.list.return_value.execute.return_value = {'items': []}
    
    with pytest.raises(ValueError, match="Channel not found"):
        mock_service.get_uploads_playlist_id("INVALID_CHANNEL_ID")

def test_get_user_playlists_quota_exceeded(mock_service):
    """시나리오 2: API 할당량 초과(403) 시 대응 확인"""
    error = create_http_error(403, "Quota Exceeded", "quotaExceeded")
    mock_service.client.playlists.return_value.list.return_value.execute.side_effect = error
    
    result = mock_service.get_user_playlists()
    
    assert result == {}

def test_add_video_to_playlist_auth_error(mock_service):
    """시나리오 3: 인증 오류(401) 발생 시 False 반환 여부"""
    # 중복 체크는 통과(False)한다고 가정
    with patch.object(mock_service, 'is_video_in_playlist', return_value=False):
        error = create_http_error(401, "Invalid Credentials", "authError")
        mock_service.client.playlistItems.return_value.insert.return_value.execute.side_effect = error
        
        success = mock_service.add_video_to_playlist("VID_123", "PL_456")
        
        assert success is False

def test_get_user_playlists_network_timeout(mock_service):
    """시나리오 4: 네트워크 타임아웃 등 일반적인 Exception 발생 시 대응"""
    mock_service.client.playlists.return_value.list.return_value.execute.side_effect = TimeoutError("Connection timed out")
    
    result = mock_service.get_user_playlists()
    
    assert result == {}