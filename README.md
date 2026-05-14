# til-discord-bot

TIL (Today I Learned) を Discord で記録・参照するためのボットです。

Discord の `#til` チャンネル投稿を受け取り、GitHub リポジトリの月次 Markdown (`YYYY-MM.md`) に追記保存します。

## 何をするボットか

- 指定した `#til` チャンネルの投稿を収集して GitHub に保存します
- 月次ファイル（`YYYY-MM.md`）を自動作成・追記します
- Discord の生メンションは保存前にサニタイズします

## 技術スタック

- Python 3.11+
- discord.py
- PyGithub
- python-dotenv

## 起動手順

1. 仮想環境を作成して有効化
2. 依存関係をインストール
3. `.env.example` をコピーして `.env` を作成
4. 起動

```powershell
python -m pip install -e .
python -m tilbot.bot
```

## ディレクトリ構成（概略）

```
docs/
	architecture.md
	architecture.ja.md
src/
	tilbot/
		application/
			til_service.py
		domain/
			models.py
			repositories.py
		infrastructure/
			github_repo.py
		presentation/
			cogs/
				til_cog.py
		bot.py
		config.py
```

## Architecture Docs

- English: [docs/architecture.md](docs/architecture.md)
- 日本語: [docs/architecture.ja.md](docs/architecture.ja.md)

## Requirements

- Python 3.11+

## Setup

1. 仮想環境を作成して有効化
2. パッケージをインストール
3. `.env` を作成して必要な環境変数を設定

## Install

```powershell
python -m pip install -e .
```

## Environment Variables

`.env.example` をコピーして `.env` を作成し、以下を設定します。

- `DISCORD_TOKEN`
- `TIL_CHANNEL_ID`
- `GITHUB_TOKEN`
- `GITHUB_REPO`
- `GITHUB_BRANCH` (任意、既定値: `main`)

## Security Notes

- `.env` は Git 追跡対象外です。絶対にコミットしないでください。
- Discord の生メンション（`<#...>`, `<@...>`, `<@&...>`）は保存時にサニタイズされます。
- トークン漏洩が疑われる場合は、Discord Token と GitHub PAT を即時ローテーションしてください。

