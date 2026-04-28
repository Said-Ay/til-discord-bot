import asyncio
import re
from datetime import datetime, timedelta, timezone

from tilbot.domain.models import Til
from tilbot.domain.repositories import ITilRepository


class TilService:
    """TILの投稿処理を担当するアプリケーションサービス"""
    def __init__(self,
                  repository: ITilRepository) -> None:
        self.til_repository = repository 
        #ドメイン層のリポジトリを受け取る

    async def process_message(self, 
                              content: str, 
                              created_at: datetime,
                                message_id: int) -> None:
        """Discordのメッセージ内容と投稿日時を受け取って、TILとして保存する"""
        #TILの内容をサニタイズして、JSTに変換した上でドメインモデルを作成し、リポジトリに保存する
        jst_created_at = self._to_jst(created_at)
        #Discordのメンションなどを内部IDが残らない形に置換して保存する
        sanitized_content = self._sanitize_content(content)
        #TILをドメイン層のモデルに変換して保存する
        til = Til(content=sanitized_content, created_at=jst_created_at, message_id=message_id)
        #リポジトリのsaveはIO処理を伴う可能性があるため、asyncio.to_threadで非同期に実行する
        await asyncio.to_thread(self.til_repository.save, til)

    @staticmethod
    def _to_jst(dt: datetime) -> datetime:
        """DiscordのタイムスタンプはUTCで来ることが多いので、JSTに変換して保存する"""
        jst = timezone(timedelta(hours=9), name="JST")
        #もし入力がnaiveなdatetimeなら、UTCとして扱う（Discordのタイムスタンプは通常awareだが、安全のため）
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(jst)

    @staticmethod
    def _sanitize_content(content: str) -> str:
        # Discordのメンションやチャンネルリンクを内部IDが残らない形に置換する
        sanitized = re.sub(r"<#\d+>", "#channel", content)
        sanitized = re.sub(r"<@!?(\d+)>", "@user", sanitized)
        sanitized = re.sub(r"<@&(\d+)>", "@role", sanitized)
        return sanitized