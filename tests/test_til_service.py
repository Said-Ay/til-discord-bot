import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock

from tilbot.application.til_service import TilService


def test_process_message_calls_repository_save_once() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    asyncio.run(service.process_message("hello", created_at))

    mock_repo.save.assert_called_once()


def test_process_message_converts_utc_to_jst() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at_utc = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    asyncio.run(service.process_message("utc content", created_at_utc))

    saved_til = mock_repo.save.call_args.args[0]
    assert saved_til.content == "utc content"
    assert saved_til.created_at.tzname() == "JST"
    assert saved_til.created_at.utcoffset().total_seconds() == 9 * 60 * 60
    assert saved_til.created_at.hour == 9
    assert saved_til.created_at.minute == 0


def test_process_message_treats_naive_datetime_as_utc_then_converts_to_jst() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    naive_created_at = datetime(2026, 4, 7, 0, 0)
    asyncio.run(service.process_message("naive content", naive_created_at))

    saved_til = mock_repo.save.call_args.args[0]
    assert saved_til.created_at.tzname() == "JST"
    assert saved_til.created_at.utcoffset().total_seconds() == 9 * 60 * 60
    assert saved_til.created_at.hour == 9
    assert saved_til.created_at.minute == 0


def test_process_message_sanitizes_discord_mentions() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    raw_content = "check <#1122334455667788990> and <@12345> with <@&67890>"
    asyncio.run(service.process_message(raw_content, created_at))

    saved_til = mock_repo.save.call_args.args[0]
    assert "<#1122334455667788990>" not in saved_til.content
    assert "<@12345>" not in saved_til.content
    assert "<@&67890>" not in saved_til.content
    assert "#channel" in saved_til.content
    assert "@user" in saved_til.content
    assert "@role" in saved_til.content
