# til-discord-bot

TIL (Today I Learned) を Discord で記録・参照するためのボットです。

Discord の `#til` チャンネル投稿を受け取り、GitHub リポジトリの月次 Markdown (`YYYY-MM.md`) に追記保存します。

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

