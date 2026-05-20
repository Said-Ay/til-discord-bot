import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock

from tilbot.application.til_service import TilService
from tilbot.domain.formatters import format_entry
from tilbot.domain.models import Til


def test_process_message_calls_repository_save_once() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    asyncio.run(service.process_message("hello", created_at, message_id=123456))

    mock_repo.save.assert_called_once()


def test_process_message_converts_utc_to_jst() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at_utc = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    asyncio.run(service.process_message("utc content", created_at_utc, message_id=123456))

    saved_til = mock_repo.save.call_args.args[0]
    assert saved_til.message_id == 123456
    assert saved_til.content == "utc content"
    assert saved_til.created_at.tzname() == "JST"
    assert saved_til.created_at.utcoffset().total_seconds() == 9 * 60 * 60
    assert saved_til.created_at.hour == 9
    assert saved_til.created_at.minute == 0


def test_process_message_treats_naive_datetime_as_utc_then_converts_to_jst() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    naive_created_at = datetime(2026, 4, 7, 0, 0)
    asyncio.run(service.process_message("naive content", naive_created_at, message_id=123456))

    saved_til = mock_repo.save.call_args.args[0]
    assert saved_til.message_id == 123456
    assert saved_til.created_at.tzname() == "JST"
    assert saved_til.created_at.utcoffset().total_seconds() == 9 * 60 * 60
    assert saved_til.created_at.hour == 9
    assert saved_til.created_at.minute == 0


def test_process_message_sanitizes_discord_mentions() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    raw_content = "check <#1122334455667788990> and <@12345> with <@&67890>"
    asyncio.run(service.process_message(raw_content, created_at, message_id=123456))

    saved_til = mock_repo.save.call_args.args[0]
    assert saved_til.message_id == 123456
    assert "<#1122334455667788990>" not in saved_til.content
    assert "<@12345>" not in saved_til.content
    assert "<@&67890>" not in saved_til.content
    assert "#channel" in saved_til.content
    assert "@user" in saved_til.content
    assert "@role" in saved_til.content


def test_update_message_calls_repository_update_once() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    created_at = datetime(2026, 4, 7, 0, 0, tzinfo=timezone.utc)
    asyncio.run(service.update_message("updated", created_at, message_id=987654))

    mock_repo.update.assert_called_once()
    saved_til = mock_repo.update.call_args.args[0]
    assert saved_til.message_id == 987654
    assert saved_til.content == "updated"


def test_delete_message_calls_repository_delete_once() -> None:
    mock_repo = MagicMock()
    service = TilService(mock_repo)

    asyncio.run(service.delete_message(message_id=987654))

    mock_repo.delete.assert_called_once()
    message_id = mock_repo.delete.call_args.args[0]
    assert message_id == 987654


def test_format_entry_includes_msg_id_and_markers() -> None:
    til = Til(
        message_id=123456,
        content="hello",
        created_at=datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc),
    )

    entry = format_entry(til)

    assert "## 2026-05-16 10:30 <!-- msg_id: 123456 -->" in entry
    assert "<!-- end_header -->" in entry
    assert "hello" in entry
    assert "<!-- end_msg -->" in entry
