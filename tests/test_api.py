import pytest
from unittest.mock import MagicMock, patch
from youtube_service import YouTubeService

@pytest.fixture
def mock_service():
    with patch.object(YouTubeService, '_load_credentials', return_value=MagicMock()):
        service = YouTubeService('fake_token.json')
        service.client = MagicMock()
        return service

def test_get_uploads_playlist_id(mock_service):
    """채널 정보를 조회하여 업로드 재생목록 ID를 가져오는지 테스트"""
    mock_response = {
        'items': [{
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UU_UPLOADS_ID'
                }
            }
        }]
    }
    mock_service.client.channels.return_value.list.return_value.execute.return_value = mock_response
    
    uploads_id = mock_service.get_uploads_playlist_id("UC_ID")
    
    assert uploads_id == 'UU_UPLOADS_ID'

def test_get_user_playlists(mock_service):
    """사용자의 재생목록을 {제목: ID} 맵으로 변환하는지 테스트"""
    mock_response = {
        'items': [
            {'id': 'ID1', 'snippet': {'title': 'Title1'}},
            {'id': 'ID2', 'snippet': {'title': 'Title2'}}
        ]
    }
    mock_service.client.playlists.return_value.list.return_value.execute.return_value = mock_response
    
    result = mock_service.get_user_playlists()
    
    assert result == {'Title1': 'ID1', 'Title2': 'ID2'}

def test_add_video_to_playlist_success(mock_service):
    """비디오 추가 API가 성공적으로 호출되는지 테스트"""
    # 중복 체크 통과 가정
    with patch.object(mock_service, 'is_video_in_playlist', return_value=False):
        mock_service.client.playlistItems.return_value.insert.return_value.execute.return_value = {}
        
        success = mock_service.add_video_to_playlist("VID_123", "PL_456")
        
        assert success is True
        mock_service.client.playlistItems.return_value.insert.assert_called_once()

def test_is_video_in_playlist(mock_service):
    """중복 체크 로직이 올바르게 작동하는지 테스트"""
    # 1. 이미 존재하는 경우
    mock_service.client.playlistItems.return_value.list.return_value.execute.return_value = {'items': [{'id': 'ITEM_ID'}]}
    assert mock_service.is_video_in_playlist("VID_EXIST", "PL_ID") is True
    
    # 2. 존재하지 않는 경우
    mock_service.client.playlistItems.return_value.list.return_value.execute.return_value = {'items': []}
    assert mock_service.is_video_in_playlist("VID_NEW", "PL_ID") is False

def test_get_new_videos_pagination(mock_service):
    """최신 영상 조회 시 페이지네이션이 동작하여 모든 최신 영상을 가져오는지 테스트"""
    # 마지막 실행 시점
    last_ts = "2025-01-01T00:00:00Z"
    
    # 페이지 1: 모두 최신 영상 (다음 페이지 존재)
    page1 = {
        'items': [
            {'contentDetails': {'videoId': 'v1'}, 'snippet': {'title': 't1', 'publishedAt': '2025-01-03T10:00:00Z'}},
            {'contentDetails': {'videoId': 'v2'}, 'snippet': {'title': 't2', 'publishedAt': '2025-01-03T09:00:00Z'}}
        ],
        'nextPageToken': 'token_page_2'
    }
    # 페이지 2: 최신 영상 1개, 과거 영상 1개 (여기서 중단되어야 함, 혹은 다 읽더라도 필터링됨)
    page2 = {
        'items': [
            {'contentDetails': {'videoId': 'v3'}, 'snippet': {'title': 't3', 'publishedAt': '2025-01-02T10:00:00Z'}},
            {'contentDetails': {'videoId': 'v4'}, 'snippet': {'title': 't4', 'publishedAt': '2024-12-31T23:59:59Z'}} # Old
        ]
        # nextPageToken 없음
    }

    mock_service.client.playlistItems.return_value.list.return_value.execute.side_effect = [page1, page2]

    videos = mock_service.get_new_videos("UU_ID", last_ts)
    
    # v1, v2, v3 만 가져와야 함 (v4는 제외)
    assert len(videos) == 3
    assert videos[0].id == 'v1'
    assert videos[1].id == 'v2'
    assert videos[2].id == 'v3'
