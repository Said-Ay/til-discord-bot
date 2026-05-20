from abc import ABC, abstractmethod

from .models import Til


class ITilRepository(ABC):
    """TILデータを保存するためのインターフェース"""

    @abstractmethod
    def save(self, til: Til) -> None:
        """TILの投稿を保存する"""
        pass
    @abstractmethod
    def update(self,til: Til) -> None:
        """TILの投稿を更新する"""
        pass    
    @abstractmethod
    def delete(self, message_id: int) -> None:
        """TILの投稿を削除する"""
        pass