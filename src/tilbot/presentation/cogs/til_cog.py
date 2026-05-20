
import logging
import asyncio

import discord
from discord.ext import commands

from tilbot.application.til_service import TilService
from tilbot.config import Config

#ログイン成功やエラーなどの重要なイベントを記録するためのロガーを設定
logger = logging.getLogger(__name__)

#Cogは、Discord Botの機能をモジュール化して管理するためのクラス。TilCogは、TilServiceとConfigを受け取って初期化されるCogクラスの例。今後、Tilに関連するコマンドやイベントハンドラーをこのクラス内に実装していくことが想定される。
class TilCog(commands.Cog):
    def __init__(self, til_service: TilService, config: Config) ->None:
        """TilServiceとConfigを受け取って初期化するTilCogクラスのコンストラクタ。TilServiceはTILの投稿を処理するためのサービスクラスであり、ConfigはBotの設定情報を保持するクラスです。これらをインスタンス変数として保存することで、TilCog内のイベントハンドラーやコマンドでこれらのオブジェクトにアクセスできるようになります。"""
        self.til_service = til_service
        self.config = config

    def _run_task(self, coro, *,context:str) -> None:
        # * 以降の引数は、呼び出すときに「名前=値」の形（キーワード）が必須.順番間違いのバグを防ぐマーク。
        """非同期タスクを実行するためのヘルパーメソッド。引数として非同期関数（コルーチン）を受け取り、asyncio.create_taskを使用して非同期タスクとして実行します。これにより、イベントハンドラー内で非同期処理を簡単に実行できるようになります。"""
        async def _wrap() -> None: #非同期関数を定義して、引数として渡された非同期関数を実行します。エラーが発生した場合には、ロガーを使用して例外情報を記録します。context引数は、エラーが発生した際のコンテキスト情報を提供するために使用されます。
            try:
                await coro #引数として渡された非同期関数を実行.coroとは、coroutineの略で、非同期関数を指す一般的な変数名です。
            except Exception:
                logger.exception(f"{context}の処理中にエラーが発生しました")
        asyncio.create_task(_wrap()) #非同期タスクとして実行



    @commands.Cog.listener() 
    #Cog内でイベントハンドラーを定義するためのデコレーター。on_readyイベントは、BotがDiscordに接続して準備ができたときに呼び出されるイベント
    async def on_message(self, message: discord.Message) ->None:
        """
        メッセージが送信されたときに呼び出されるイベントハンドラー。
        引数としてdiscord.Messageオブジェクトを受け取ります。
        メッセージがBot自身のものである場合や、特定のチャンネル以外で送信された場合には処理をスキップします。
        それ以外の場合には、TilServiceのprocess_messageメソッドを呼び出して、メッセージの内容と作成日時を処理します。
        処理が成功した場合には、メッセージに✅リアクションを追加し、失敗した場合には❌リアクションを追加します。
        """
        if message.author.bot: 
            #Bot自身のメッセージや他のBotのメッセージを無視するためのチェック。これにより、Botが自分自身のメッセージに反応して無限ループになることを防ぐことができる。
            return
        
        if message.channel.id != self.config.til_channel_id:
             #特定のチャンネルでのみ反応するためのチェック。これにより、Botが他のチャンネルのメッセージに反応しないようにすることができる。
            return
        
        try: #TilServiceのprocess_messageメソッドを呼び出して、メッセージの内容と作成日時を処理する。process_messageは非同期関数であるため、awaitを使用して呼び出す必要がある。
            await self.til_service.process_message(
                content=message.content,
                created_at=message.created_at,
                message_id=message.id, #message_idをTilServiceに渡すように変更
            )
            await message.add_reaction("✅")
        except Exception: #Tilの保存に失敗した場合の例外処理。
            logger.exception("Tilの保存に失敗しました")
            await message.add_reaction("❌")
        
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """
        メッセージが編集されたときに呼び出されるイベントハンドラー。
        編集前のメッセージと編集後のメッセージを引数として受け取ります。
        編集されたメッセージが特定のチャンネルに属している場合、TilServiceのupdate_messageメソッドを呼び出して、編集された内容を処理します。
        処理が成功した場合には、編集されたメッセージに✅リアクションを追加し、失敗した場合には❌リアクションを追加します。
        """
        if before.content == after.content:
            return
        if after.author.bot:
            return
        if after.channel.id != self.config.til_channel_id:
            return

        try:
            await self.til_service.update_message(
                content=after.content,
                created_at=after.created_at,
                message_id=after.id, #message_idをTilServiceに渡すように変更
            )
        except Exception:
            logger.exception("edit message_id = %s の処理中にエラーが発生しました", after.id)
            return
        
        try:
            await after.add_reaction("🔁")
        except Exception:
            logger.exception("リアクションの追加に失敗しました: %s", after.id)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        メッセージが削除されたときに呼び出されるイベントハンドラー。
        削除されたメッセージを引数として受け取ります。
        削除されたメッセージが特定のチャンネルに属している場合、TilServiceのdelete_messageメソッドを呼び出して、削除された内容を処理します。
        """
        if message.channel.id != self.config.til_channel_id:
            return
        if message.author.bot:
            return
        self._run_task(
            self.til_service.delete_message(
                message_id=message.id, #message_idをTilServiceに渡すように変更
            ),
            context=f"delete message_id = {message.id}"
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        """
        メッセージ削除のRawイベントを受け取る。
        キャッシュが無い場合でも message_id で削除を試みる。
        チャンネルが対象外の場合も無視する。
        """
        if payload.channel_id != self.config.til_channel_id:
            return
        self._run_task(
            self.til_service.delete_message(
                message_id=payload.message_id,
            ),
            context=f"raw delete message_id = {payload.message_id}"
        )