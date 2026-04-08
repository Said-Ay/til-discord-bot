from datetime import datetime
from unittest.mock import MagicMock, patch

from github.GithubException import UnknownObjectException

from tilbot.config import Config
from tilbot.domain.models import Til
from tilbot.infrastructure.github_repo import GithubTilRepository


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
    til = Til(content="new content", created_at=datetime(2026, 4, 7, 9, 30))

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
    til = Til(content="first content", created_at=datetime(2026, 4, 7, 9, 30))

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
    til = Til(content="content", created_at=datetime(2026, 4, 7, 9, 30))

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
