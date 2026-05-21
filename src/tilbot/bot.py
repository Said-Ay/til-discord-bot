import asyncio
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
    asyncio.run(_async_main())


async def _health_check_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """GET /healthz に 200 OK を返す最小 HTTP ハンドラー"""
    await reader.read(1024)
    writer.write(
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\n\r\nOK"
    )
    await writer.drain()
    writer.close()


async def _async_main() -> None:
    config = Config.from_env()

    server = await asyncio.start_server(
        _health_check_handler, "0.0.0.0", config.health_check_port
    )
    logger.info("ヘルスチェックサーバーを起動しました: port=%d", config.health_check_port)

    bot = build_bot()

    async with server:
        await asyncio.gather(
            server.serve_forever(),
            bot.start(config.discord_token),
        )


if __name__ == "__main__":
    main()
