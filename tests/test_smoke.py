from tilbot.config import Config
from tilbot.domain.models import Til
from tilbot.domain.repositories import ITilRepository
from tilbot.application.til_service import TilService
from tilbot.infrastructure.github_repo import GithubTilRepository
from tilbot.infrastructure.markdown_utils import EntryNotFoundError


def test_imports() -> None:
    """主要なモジュールがすべてインポートできることを確認する"""
    assert Config is not None
    assert Til is not None
    assert ITilRepository is not None
    assert TilService is not None
    assert GithubTilRepository is not None
    assert EntryNotFoundError is not None

