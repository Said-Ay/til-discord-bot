import logging

import discord
from discord.ext import commands

from tilbot.application.til_service import TilService
from tilbot.config import Config

#ログイン成功やエラーなどの重要なイベントを記録するためのロガーを設定
logger = logging.getLogger(__name__)

#Cogは、Discord Botの機能をモジュール化して管理するためのクラス。TilCogは、TilServiceとConfigを受け取って初期化されるCogクラスの例。今後、Tilに関連するコマンドやイベントハンドラーをこのクラス内に実装していくことが想定される。
class TilCog(commands.Cog):
    def __init__(self, til_service: TilService, config: Config) ->None:
        self.til_service = til_service
        self.config = config

    @commands.Cog.listener() 
    #Cog内でイベントハンドラーを定義するためのデコレーター。on_readyイベントは、BotがDiscordに接続して準備ができたときに呼び出されるイベント
    async def on_message(self, message: discord.Message) ->None:
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
            
        