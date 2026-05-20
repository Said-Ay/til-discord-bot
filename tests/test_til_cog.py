import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from tilbot.config import Config
from tilbot.presentation.cogs.til_cog import TilCog


@dataclass
class DummyAuthor:
    bot: bool


@dataclass
class DummyChannel:
    id: int


class DummyMessage:
    def __init__(self, *, content: str, message_id: int, channel_id: int, bot: bool) -> None:
        self.content = content
        self.id = message_id
        self.channel = DummyChannel(channel_id)
        self.author = DummyAuthor(bot)
        self.created_at = datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc)
        self._reactions: list[str] = []

    async def add_reaction(self, emoji: str) -> None:
        self._reactions.append(emoji)


@dataclass
class DummyPayload:
    channel_id: int
    message_id: int


def _make_config(channel_id: int = 1234) -> Config:
    return Config(
        discord_token="dummy",
        til_channel_id=channel_id,
        github_token="dummy",
        github_repo="owner/repo",
        github_branch="main",
    )


def test_on_message_edit_ignores_same_content() -> None:
    til_service = AsyncMock()
    cog = TilCog(til_service=til_service, config=_make_config())

    before = DummyMessage(content="same", message_id=1, channel_id=1234, bot=False)
    after = DummyMessage(content="same", message_id=1, channel_id=1234, bot=False)

    asyncio.run(cog.on_message_edit(before, after))

    assert til_service.update_message.await_count == 0


def test_on_message_edit_success_calls_update_and_reacts() -> None:
    til_service = AsyncMock()
    cog = TilCog(til_service=til_service, config=_make_config())

    before = DummyMessage(content="before", message_id=1, channel_id=1234, bot=False)
    after = DummyMessage(content="after", message_id=1, channel_id=1234, bot=False)

    asyncio.run(cog.on_message_edit(before, after))

    til_service.update_message.assert_awaited_once_with(
        content="after",
        created_at=after.created_at,
        message_id=after.id,
    )
    assert after._reactions == ["\U0001F501"]


def test_on_message_delete_ignores_other_channel() -> None:
    til_service = AsyncMock()
    cog = TilCog(til_service=til_service, config=_make_config())

    message = DummyMessage(content="x", message_id=1, channel_id=9999, bot=False)

    asyncio.run(cog.on_message_delete(message))

    assert til_service.delete_message.await_count == 0


def test_on_raw_message_delete_calls_delete_by_message_id() -> None:
    til_service = AsyncMock()
    cog = TilCog(til_service=til_service, config=_make_config())

    payload = DummyPayload(channel_id=1234, message_id=1)

    asyncio.run(cog.on_raw_message_delete(payload))

    til_service.delete_message.assert_called_once_with(message_id=1)
