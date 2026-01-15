from typing import List, Tuple, Optional
from models import Rule

class RuleEngine:
    def __init__(self, rules_data: dict):
        self.rules = rules_data.get('rules', [])
        # 긴 키워드 우선 매칭을 위해 미리 정렬
        self.sorted_rules = sorted(
            self.rules,
            key=lambda x: len(x['keyword']),
            reverse=True
        )

    @staticmethod
    def normalize(text: str) -> str:
        return "".join(text.split()).lower()

    def find_playlist_id_by_keyword(self, keyword: str, user_playlists: dict) -> Optional[str]:
        normalized_keyword = self.normalize(keyword)
        for title, pl_id in user_playlists.items():
            if normalized_keyword in self.normalize(title):
                return pl_id
        return None

    def classify_video(self, video_title: str, user_playlists: dict) -> Tuple[Optional[str], Optional[str]]:
        normalized_title = self.normalize(video_title)
        
        for rule in self.sorted_rules:
            keyword = rule['keyword']
            if self.normalize(keyword) in normalized_title:
                target_id = self.find_playlist_id_by_keyword(keyword, user_playlists)
                if target_id:
                    return target_id, keyword
        return None, None
