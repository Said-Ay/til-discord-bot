import os
from dataclasses import dataclass

from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


@dataclass(frozen=True)
class Config:
    discord_token: str
    til_channel_id: int
    github_token: str
    github_repo: str
    github_branch: str = "main"

    @classmethod
    def from_env(cls) -> "Config":
        """環境変数から設定を読み込んでConfigインスタンスを作成する"""
        discord_token = os.getenv("DISCORD_TOKEN")
        til_channel_id_str = os.getenv("TIL_CHANNEL_ID")
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")
        github_branch = os.getenv("GITHUB_BRANCH", "main")

        # 必須項目のチェック
        if not all([discord_token, til_channel_id_str, github_token, github_repo]):
            raise ValueError(
                "必須の環境変数が不足しています"
                "(DISCORD_TOKEN, TIL_CHANNEL_ID, GITHUB_TOKEN, GITHUB_REPO)"
            )
        if not til_channel_id_str.isdigit():
            raise ValueError(
                f"TIL_CHANNEL_ID は数字のみで指定してください: {til_channel_id_str!r}"
            )

        return cls(
            discord_token=discord_token,
            til_channel_id=int(til_channel_id_str),
            github_token=github_token,
            github_repo=github_repo,
            github_branch=github_branch,
        )