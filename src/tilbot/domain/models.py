from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Til:
    """1件のTILを表すドメインモデル"""
    content: str #投稿内容
    created_at: datetime #投稿日時
    