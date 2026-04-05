import os
import pytest
from tilbot.config import Config

def test_config_from_env_success(monkeypatch):
    """環境変数が正しく設定されている場合、Configインスタンスが生成されること"""
    # monkeypatchを使ってテスト用の環境変数をセット
    monkeypatch.setenv("DISCORD_TOKEN", "test_discord")
    monkeypatch.setenv("TIL_CHANNEL_ID", "11112222")
    monkeypatch.setenv("GITHUB_TOKEN", "test_github")
    monkeypatch.setenv("GITHUB_REPO", "test/repo")
    
    config = Config.from_env()
    
    assert config.discord_token == "test_discord"
    assert config.til_channel_id == 11112222
    assert config.github_token == "test_github"
    assert config.github_repo == "test/repo"
    assert config.github_branch == "main"  # デフォルト値の確認

def test_config_from_env_missing_vars(monkeypatch):
    """必須の環境変数が欠けている場合、ValueErrorが発生すること"""
    # 環境変数をクリア
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    
    with pytest.raises(ValueError, match="必須の環境変数が不足しています"):
        Config.from_env()