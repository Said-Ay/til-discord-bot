from __future__ import annotations

from datetime import datetime 
from github import Github
from github.GithubException import UnknownObjectException

from tilbot.config import Config
from tilbot.domain.models import Til
from tilbot.domain.repositories import ITilRepository


class GithubTilRepository(ITilRepository):
    def __init__(self, config: Config):
        self._config = config
        self._client = Github(config.github_token)
        self._repo = self._client.get_repo(config.github_repo)

    def save(self, til: Til) -> None:
        """TILの投稿をGitHubリポジトリに保存する"""
        path = self._build_monthly_path(til.created_at)
        new_entry = self._format_entry(til)

        try:
            #既存ファイルがある場合は追記して更新する
            file_obj = self._repo.get_contents(path, ref=self._config.github_branch)
            existing_text = file_obj.decoded_content.decode("utf-8")
            updated_text = self._append_entry(existing_text, new_entry)
            self._repo.update_file(
                path=path,
                message=f"chore:append TIL {til.created_at.strftime('%Y-%m-%d %H:%M')}",
                content=updated_text,
                sha=file_obj.sha,
                branch=self._config.github_branch,
                )
        except UnknownObjectException:
            #ファイルが存在しない場合は新規作成する
            self._repo.create_file(
                path=path,
                message=f"chore:create monthly TIL {path}",
                content=new_entry,
                branch=self._config.github_branch,
            )

    @staticmethod
    def _build_monthly_path(created_at: datetime) ->str:
        """TILの作成日時から月次ファイルのパスを生成する"""
        return created_at.strftime("%Y-%m.md")
    
    @staticmethod
    def _format_entry(til:Til) -> str:
        """TILの内容をマークダウン形式のエントリーに整形する"""
        header = til.created_at.strftime("## %Y-%m-%d %H:%M")
        return f"{header}\n\n{til.content.strip()}\n"

    @staticmethod
    def _append_entry(existing_text: str, new_entry: str) -> str:
        """既存の月次ファイルの内容に新しいエントリーを追記する"""
        if not existing_text.strip():
            return new_entry
        return f"{existing_text.rstrip()}\n\n{new_entry}"