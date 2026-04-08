import logging 

import discord
from discord.ext import commands

from tilbot.application.til_service import TilService
from tilbot.config import Config
from tilbot.infrastructure.github_repo import GithubTilRepository
from tilbot.presentation.cogs.til_cog import TilCog
#ログイン成功やエラーなどの重要なイベントを記録するためのロガーを設定
logger = logging.getLogger(__name__)


class TilBot(commands.Bot):
    """TilServiceを保持するBotサブクラス。"""

    til_service: TilService

    def __init__(self, til_service: TilService, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.til_service = til_service

#Botの構築を行う関数。Configから設定を読み込み、GithubTilRepositoryとTilServiceを初期化し、Discord Botを作成してイベントハンドラーを登録する。
def build_bot() -> TilBot:
    config = Config.from_env()
    repository = GithubTilRepository(config)
    service = TilService(repository)

    # Discord Botがメッセージ内容を読み取れるようにするためのIntentsを設定
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = TilBot(til_service=service, command_prefix="!", intents=intents)

    async def setup_hook() -> None:
        await bot.add_cog(TilCog(til_service=service, config=config))

    bot.setup_hook = setup_hook # type: ignore[method-assign]

    @bot.event #on_readyイベントは、BotがDiscordに接続して準備ができたときに呼び出されるイベント
    async def on_ready() ->None:
        logger.info("ログイン成功しました: %s",bot.user)
    return bot

def main() -> None:
    """Botを構築して起動する関数。build_bot関数を呼び出してBotを作成し、Discordに接続してイベントループを開始する"""
    # ログレベルをINFOに設定し、ログのフォーマットを指定することで、Botの動作状況を記録できるようにする
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config.from_env()
    bot = build_bot()
    #Botを起動するためのrunメソッドを呼び出し、Discordに接続してイベントループを開始する。引数にはDiscord Botのトークンを渡す。
    bot.run(config.discord_token)

if __name__ == "__main__":
    main()