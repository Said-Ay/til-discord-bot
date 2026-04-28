from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Til:
    """1件のTILを表すドメインモデル"""
    content: str #投稿内容
    created_at: datetime #投稿日時
    message_id: int 
    #DiscordのメッセージID。保存前はNoneで、保存後にDiscordから取得して設定される