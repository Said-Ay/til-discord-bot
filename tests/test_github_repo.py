from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from github.GithubException import UnknownObjectException

from tilbot.config import Config
from tilbot.domain.models import Til
from tilbot.infrastructure.github_repo import GithubTilRepository
from tilbot.infrastructure.markdown_utils import EntryNotFoundError


def _make_config() -> Config:
    return Config(
        discord_token="dummy-discord-token",
        til_channel_id=1234567890,
        github_token="dummy-github-token",
        github_repo="owner/repo",
        github_branch="main",
    )


def test_save_updates_existing_monthly_file() -> None:
    config = _make_config()
    til = Til(message_id=123456, content="new content", created_at=datetime(2026, 4, 7, 9, 30))

    mock_repo = MagicMock()
    mock_file = MagicMock()
    mock_file.decoded_content = b"## 2026-04-06 10:00\n\nold content\n"
    mock_file.sha = "abc123"
    mock_repo.get_contents.return_value = mock_file

    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    with patch("tilbot.infrastructure.github_repo.Github", return_value=mock_client):
        repository = GithubTilRepository(config)
        repository.save(til)

    mock_repo.update_file.assert_called_once()
    kwargs = mock_repo.update_file.call_args.kwargs
    assert kwargs["path"] == "2026-04.md"
    assert kwargs["branch"] == "main"
    assert "old content" in kwargs["content"]
    assert "new content" in kwargs["content"]

    mock_repo.create_file.assert_not_called()


def test_save_creates_monthly_file_when_missing() -> None:
    config = _make_config()
    til = Til(message_id=123456, content="first content", created_at=datetime(2026, 4, 7, 9, 30))

    mock_repo = MagicMock()
    mock_repo.get_contents.side_effect = UnknownObjectException(
        404, {"message": "Not Found"}, None
    )

    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    with patch("tilbot.infrastructure.github_repo.Github", return_value=mock_client):
        repository = GithubTilRepository(config)
        repository.save(til)

    mock_repo.create_file.assert_called_once()
    kwargs = mock_repo.create_file.call_args.kwargs
    assert kwargs["path"] == "2026-04.md"
    assert kwargs["branch"] == "main"
    assert "## 2026-04-07 09:30" in kwargs["content"]
    assert "first content" in kwargs["content"]

    mock_repo.update_file.assert_not_called()


def test_save_raises_when_monthly_path_is_directory() -> None:
    config = _make_config()
    til = Til(message_id=123456, content="content", created_at=datetime(2026, 4, 7, 9, 30))

    mock_repo = MagicMock()
    mock_repo.get_contents.return_value = [MagicMock()]

    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    with patch("tilbot.infrastructure.github_repo.Github", return_value=mock_client):
        repository = GithubTilRepository(config)

        try:
            repository.save(til)
            assert False, "Expected ValueError to be raised"
        except ValueError as exc:
            assert "Expected a file path but got directory" in str(exc)

    mock_repo.update_file.assert_not_called()
    mock_repo.create_file.assert_not_called()


def test_update_updates_existing_message_body() -> None:
    config = _make_config()
    til = Til(message_id=123456, content="updated body", created_at=datetime(2026, 4, 7, 9, 30))

    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123456 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "old body\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    mock_repo = MagicMock()
    mock_file = MagicMock()
    mock_file.decoded_content = markdown.encode("utf-8")
    mock_file.sha = "abc123"
    mock_repo.get_contents.return_value = mock_file

    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    with patch("tilbot.infrastructure.github_repo.Github", return_value=mock_client):
        repository = GithubTilRepository(config)
        repository.update(til)

    mock_repo.update_file.assert_called_once()
    kwargs = mock_repo.update_file.call_args.kwargs
    assert "updated body" in kwargs["content"]
    assert "old body" not in kwargs["content"]


def test_delete_removes_message_block() -> None:
    config = _make_config()

    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123456 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "old body\n"
        "\n"
        "<!-- end_msg -->\n"
        "\n"
        "## 2026-05-16 10:40 <!-- msg_id: 999 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "keep\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    mock_repo = MagicMock()
    mock_file = MagicMock()
    mock_file.decoded_content = markdown.encode("utf-8")
    mock_file.sha = "abc123"
    mock_repo.get_contents.return_value = mock_file

    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    with patch("tilbot.infrastructure.github_repo.Github", return_value=mock_client):
        with patch.object(
            GithubTilRepository,
            "_current_jst",
            return_value=datetime(2026, 5, 20, tzinfo=timezone.utc),
        ):
            repository = GithubTilRepository(config)
            repository.delete(123456)

    mock_repo.update_file.assert_called_once()
    kwargs = mock_repo.update_file.call_args.kwargs
    assert "msg_id: 123456" not in kwargs["content"]
    assert "msg_id: 999" in kwargs["content"]


def test_update_raises_when_message_id_missing() -> None:
    config = _make_config()
    til = Til(message_id=123456, content="updated body", created_at=datetime(2026, 4, 7, 9, 30))

    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 999 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "old body\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    mock_repo = MagicMock()
    mock_file = MagicMock()
    mock_file.decoded_content = markdown.encode("utf-8")
    mock_file.sha = "abc123"
    mock_repo.get_contents.return_value = mock_file

    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    with patch("tilbot.infrastructure.github_repo.Github", return_value=mock_client):
        repository = GithubTilRepository(config)
        try:
            repository.update(til)
            assert False, "Expected EntryNotFoundError"
        except EntryNotFoundError:
            pass
