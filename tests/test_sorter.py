import pytest
from storage import validate_rules
from rule_engine import RuleEngine

def test_validate_rules_success():
    """정상적인 규칙 데이터가 유효성 검사를 통과하는지 테스트"""
    rules_data = {
        "rules": [
            {"keyword": "새벽", "description": "test"},
            {"keyword": "주일"}
        ]
    }
    assert validate_rules(rules_data) is True

def test_validate_rules_missing_rules_key():
    """'rules' 키가 없을 때 ValueError 발생 테스트"""
    rules_data = {"other_key": []}
    with pytest.raises(ValueError, match="Invalid rules format"):
        validate_rules(rules_data)

def test_validate_rules_missing_keyword():
    """규칙 내 'keyword'가 없을 때 ValueError 발생 테스트"""
    rules_data = {
        "rules": [{"no_keyword": "test"}]
    }
    with pytest.raises(ValueError, match="is missing 'keyword'"):
        validate_rules(rules_data)

def test_classify_video_match():
    """키워드가 제목에 포함되어 있을 때 정확한 재생목록 ID를 찾는지 테스트"""
    rules_data = {
        "rules": [{"keyword": "새벽"}]
    }
    engine = RuleEngine(rules_data)
    user_playlists = {
        "2026 새벽예배 리스트": "PL_DAWN_ID",
        "주일예배": "PL_SUNDAY_ID"
    }
    video_title = "2026년 1월 14일 새벽예배 실황"
    
    playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    
    assert playlist_id == "PL_DAWN_ID"
    assert keyword == "새벽"

def test_classify_video_no_match():
    """일치하는 키워드가 없을 때 None을 반환하는지 테스트"""
    rules_data = {
        "rules": [{"keyword": "주일"}]
    }
    engine = RuleEngine(rules_data)
    user_playlists = {"새벽예배": "PL_DAWN_ID"}
    video_title = "수요기도회 영상"
    
    playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    
    assert playlist_id is None
    assert keyword is None

def test_classify_video_keyword_exists_but_no_playlist():
    """키워드는 매칭되지만, 해당 키워드를 포함한 재생목록이 계정에 없을 때"""
    rules_data = {
        "rules": [{"keyword": "금요"}]
    }
    engine = RuleEngine(rules_data)
    user_playlists = {"새벽예배": "PL_DAWN_ID"}
    video_title = "금요철야 성령집회"
    
    playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    
    assert playlist_id is None
    assert keyword is None

def test_classify_video_whitespace_handling():
    """제목이나 키워드에 공백이 포함되어 있어도 매칭되는지 테스트"""
    rules_data = {
        "rules": [{"keyword": "주일 2부"}]
    }
    engine = RuleEngine(rules_data)
    user_playlists = {"2026 주일 2부 예배": "PL_SUNDAY_2_ID"}
    
    # 공백이 다른 경우 (원본: "주일 2부", 제목: "주일2부")
    video_title = "예수산소망교회 주일2부예배(2026.01.11)"
    playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    
    assert playlist_id == "PL_SUNDAY_2_ID"
    assert keyword == "주일 2부"

def test_classify_video_case_insensitivity():
    """대소문자가 달라도 매칭되는지 테스트 (영어 키워드 대비)"""
    rules_data = {
        "rules": [{"keyword": "praise"}]
    }
    engine = RuleEngine(rules_data)
    user_playlists = {"Praise and Worship": "PL_PRAISE_ID"}
    video_title = "Sunday Morning PRAISE"
    
    playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    
    assert playlist_id == "PL_PRAISE_ID"
    assert keyword == "praise"

def test_classify_video_longest_keyword_priority():
    """겹치는 키워드가 있을 때 더 구체적인(긴) 키워드가 우선순위를 갖는지 테스트"""
    rules_data = {
        "rules": [
            {"keyword": "주일"},
            {"keyword": "주일 1부"}
        ]
    }
    engine = RuleEngine(rules_data)
    user_playlists = {
        "주일예배": "PL_GENERAL_ID",
        "2026 주일 1부 예배": "PL_PART1_ID"
    }
    video_title = "예수산소망교회 주일1부예배"
    
    playlist_id, keyword = engine.classify_video(video_title, user_playlists)
    
    # 더 구체적인 '주일 1부'가 매칭되어야 함
    assert playlist_id == "PL_PART1_ID"
    assert keyword == "주일 1부"