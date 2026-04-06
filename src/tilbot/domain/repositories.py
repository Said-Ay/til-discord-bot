from abc import ABC, abstractmethod
from typing import Optional
from .models import Til

class ITilRepository (ABC):
    """TILデータを保存するためのインターフェース"""

    @abstractmethod
    def save(self, til: Til) -> None:
        """TILの投稿を保存する"""
        pass