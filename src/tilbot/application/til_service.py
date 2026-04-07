import asyncio
from datetime import datetime, timedelta, timezone

from tilbot.domain.models import Til
from tilbot.domain.repositories import ITilRepository


class TilService:
    def __init__(self, repository: ITilRepository) -> None:
        self.til_repository = repository

    async def process_message(self, content: str, created_at: datetime) -> None:
        jst_created_at = self._to_jst(created_at)
        til = Til(content=content, created_at=jst_created_at)
        await asyncio.to_thread(self.til_repository.save, til)

    @staticmethod
    def _to_jst(dt: datetime) -> datetime:
        jst = timezone(timedelta(hours=9), name="JST")
        if dt.tzinfo is None:
            # Discord timestamp should be aware, but treat naive input as UTC safely.
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(jst)