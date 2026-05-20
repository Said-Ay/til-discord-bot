"""このファイルは、GitHubリポジトリを使用してTILの投稿を保存、更新、削除するためのGithubTilRepositoryクラスを定義しています。GithubTilRepositoryはITilRepositoryインターフェースを実装しており、GitHub APIを使用して月次ファイルにTILエントリーを管理します。TILの投稿は、作成日時に基づいて月次ファイルに保存され、更新や削除も同様に月次ファイル内で行われます。エントリーの更新や削除は、指定されたmessage_idに対応するエントリーをマークダウンから検索し、必要に応じて内容を変更または削除することで実現されます。また、GitHub APIの呼び出しで競合が発生した場合にはリトライする仕組みも実装されています。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone 
from github import Github
from github.GithubException import GithubException, UnknownObjectException

from tilbot.config import Config
from tilbot.domain.models import Til
from tilbot.domain.repositories import ITilRepository
from tilbot.domain.formatters import format_entry
from tilbot.infrastructure.markdown_utils import (
    EntryNotFoundError,
    delete_by_message_id,
    update_body_by_message_id,
)

class GithubTilRepository(ITilRepository):
    _MAX_RETRIES = 3

    def __init__(self, config: Config):
        self._config = config
        self._client = Github(config.github_token)
        self._repo = self._client.get_repo(config.github_repo)

    def save(self, til: Til) -> None:
        """TILの投稿をGitHubリポジトリに保存する"""
        path = self._build_monthly_path(til.created_at)
        new_entry = format_entry(til) #TILを保存フォーマットに変換する

        try:
            #既存ファイルがある場合は追記して更新する
            file_obj_or_list = self._repo.get_contents(path, ref=self._config.github_branch)
            if isinstance(file_obj_or_list, list):
                raise ValueError(f"Expected a file path but got directory: {path}")

            file_obj = file_obj_or_list
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

    def update(self, til: Til) -> None:
        """TILの投稿を更新する"""
        path = self._build_monthly_path(til.created_at)
        self._apply_update_or_delete(
            path=path,
            message_id=til.message_id,
            new_body=til.content,
            is_delete=False)

    def delete(self, message_id: int) -> None:
        """TILの投稿を削除する"""
        reference = self._current_jst()
        for target in self._month_candidates(reference):
            path = self._build_monthly_path(target)
            try:
                file_obj_or_list = self._repo.get_contents(path, ref=self._config.github_branch)
                if isinstance(file_obj_or_list, list):
                    raise ValueError(f"Expected a file path but got directory: {path}")
                file_obj = file_obj_or_list
            except UnknownObjectException:
                continue

            existing_text = file_obj.decoded_content.decode("utf-8")
            try:
                updated_text = delete_by_message_id(existing_text, message_id)
            except EntryNotFoundError:
                continue

            self._repo.update_file(
                path=path,
                message=f"chore:delete TIL {message_id}",
                content=updated_text,
                sha=file_obj.sha,
                branch=self._config.github_branch,
            )
            return

        raise EntryNotFoundError(f"message_id {message_id} not found")

    def _apply_update_or_delete(
        self,
        *,
        path: str, 
        message_id: int, 
        new_body: str, 
        is_delete: bool
        ) -> None:
        """TILの投稿の更新または削除を適用する"""
        for attempt in range(self._MAX_RETRIES):
            try: #月次ファイルの内容を取得して、指定されたmessage_idに対応するエントリーを更新または削除する。エントリーが見つからない場合はEntryNotFoundErrorを発生させることで、存在しないTILの更新や削除を防止する
                file_obj_or_list = self._repo.get_contents(path, ref=self._config.github_branch)
                if isinstance(file_obj_or_list, list): #パスがディレクトリの場合はエラーを発生させることで、誤ってディレクトリを操作することを防止する
                    raise ValueError(f"Expected a file path but got directory: {path}")
                file_obj = file_obj_or_list #ファイルオブジェクトを取得する
                existing_text = file_obj.decoded_content.decode("utf-8")
                if is_delete: #削除の場合はdelete_by_message_idを呼び出して、指定されたmessage_idに対応するエントリーをマークダウンから削除する。更新の場合はupdate_body_by_message_idを呼び出して、指定されたmessage_idに対応するエントリーの本文を新しいテキストに置き換える
                    updated_text = delete_by_message_id(existing_text, message_id)
                    commit_message = f"chore:delete TIL {message_id}"
                else:
                    updated_text = update_body_by_message_id(existing_text, message_id, new_body)
                    commit_message = f"chore:update TIL {message_id}"
                self._repo.update_file(
                    path=path,
                    message=commit_message,
                    content=updated_text,
                    sha=file_obj.sha, #ファイルのSHAを指定して更新することで、同時編集による競合を防止する.SHAはファイルの内容が変更されるたびに変わるため、最新のSHAを取得して更新する必要がある
                    branch=self._config.github_branch,
                )
                return
            except UnknownObjectException as exc:
                raise #ファイルが存在しない場合はエラーを発生させることで、存在しない月次ファイルの更新や削除を防止する
            except EntryNotFoundError:
                raise #指定されたmessage_idのエントリーが見つからない場合はエラーを発生させることで、存在しないTILの更新や削除を防止する
            except GithubException as exc: #GitHub APIの呼び出しでエラーが発生した場合は、409 Conflict時のみリトライする
                if exc.status == 409 and attempt < self._MAX_RETRIES - 1: #409 Conflictエラーの場合はリトライする
                    continue
                raise
    @staticmethod
    def _build_monthly_path(created_at: datetime) ->str:
        """TILの作成日時から月次ファイルのパスを生成する"""
        return created_at.strftime("%Y-%m.md")

    @staticmethod
    def _current_jst() -> datetime:
        jst = timezone(timedelta(hours=9), name="JST")
        return datetime.now(jst)

    @staticmethod
    def _shift_month(reference: datetime, delta_months: int) -> datetime:
        month_index = reference.month - 1 + delta_months
        year = reference.year + month_index // 12
        month = month_index % 12 + 1
        return reference.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

    @classmethod
    def _month_candidates(cls, reference: datetime) -> list[datetime]:
        return [
            cls._shift_month(reference, 0),
            cls._shift_month(reference, -1),
            cls._shift_month(reference, 1),
        ]
    

    @staticmethod
    def _append_entry(existing_text: str, new_entry: str) -> str:
        """既存の月次ファイルの内容に新しいエントリーを追記する"""
        if not existing_text.strip():
            return new_entry
        return f"{existing_text.rstrip()}\n\n{new_entry}"