# til-discord-bot

> Discord の `#til` チャンネルに投稿するだけで、GitHub リポジトリに TIL（Today I Learned）が自動保存されるボットです。

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2)](https://discordpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 何をするボットか

```
Discord #til チャンネル
  │
  │ 投稿・編集・削除
  ▼
til-discord-bot
  │
  │ GitHub API
  ▼
YYYY-MM.md（月次ファイル）
```

| Discord の操作 | ボットの動作 |
|---------------|--------------|
| メッセージを投稿 | `YYYY-MM.md` に追記して ✅ リアクション |
| メッセージを編集 | 該当エントリの本文を更新して 🔁 リアクション |
| メッセージを削除 | 該当エントリを削除（ログのみ） |

### 保存フォーマット

```markdown
## 2026-05-20 10:30 <!-- msg_id: 123456789 -->
<!-- end_header -->

今日は Python の dataclass について学んだ。
frozen=True にすると不変オブジェクトになる。

<!-- end_msg -->
```

`msg_id` でエントリを一意に管理するため、編集・削除が正確に追跡できます。

---

## 技術スタック

| 用途 | ライブラリ |
|------|------------|
| Discord Bot フレームワーク | [discord.py](https://discordpy.readthedocs.io/) 2.x |
| GitHub API クライアント | [PyGithub](https://pygithub.readthedocs.io/) |
| 環境変数の読み込み | [python-dotenv](https://github.com/theskumar/python-dotenv) |

---

## セットアップ

### 前提条件

- Python 3.11 以上
- Discord Bot トークン（[Discord Developer Portal](https://discord.com/developers/applications) で取得）
- GitHub Personal Access Token（`repo` スコープが必要）

### 1. リポジトリをクローン

```bash
git clone https://github.com/your-username/til-discord-bot.git
cd til-discord-bot
```

### 2. 仮想環境を作成して有効化

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. 依存パッケージをインストール

```bash
pip install -e .
```

### 4. 環境変数を設定

`.env.example` をコピーして `.env` を作成し、各値を設定してください。

```bash
cp .env.example .env
```

```dotenv
DISCORD_TOKEN=your_discord_bot_token
TIL_CHANNEL_ID=123456789012345678   # 保存対象チャンネルの ID（数字のみ）
GITHUB_TOKEN=your_github_pat
GITHUB_REPO=owner/repository        # 例: your-name/til-notes
GITHUB_BRANCH=main                  # 省略可（既定値: main）
```

> **TIL_CHANNEL_ID の確認方法**: Discord の設定 → 詳細設定 → 開発者モード を有効にし、チャンネルを右クリック →「ID をコピー」

### 5. Discord Bot の権限設定

Discord Developer Portal でボットに以下の権限を付与してください。

- **Intents**: `Message Content Intent` を ON
- **Bot Permissions**: `Send Messages`, `Add Reactions`, `Read Message History`

### 6. 起動

```bash
python -m tilbot.bot
```

起動後、ログに `ログイン成功しました: BotName#0000` が表示されれば完了です。

---

## ディレクトリ構成

```
til-discord-bot/
├── src/
│   └── tilbot/
│       ├── bot.py               # 起動エントリポイント・DI 配線
│       ├── config.py            # 環境変数の読み込み
│       ├── application/
│       │   └── til_service.py   # ユースケース（保存・更新・削除）
│       ├── domain/
│       │   ├── models.py        # Til ドメインモデル
│       │   ├── repositories.py  # リポジトリインターフェース
│       │   └── formatters.py    # Markdown エントリのフォーマット
│       ├── infrastructure/
│       │   ├── github_repo.py   # GitHub API を使った永続化実装
│       │   └── markdown_utils.py# Markdown ブロックのパース・編集
│       └── presentation/
│           └── cogs/
│               └── til_cog.py   # Discord イベントハンドラ
├── tests/                       # 単体テスト
├── docs/
│   ├── architecture.md          # アーキテクチャ解説（英語）
│   └── architecture.ja.md      # アーキテクチャ解説（日本語）
├── .env.example                 # 環境変数テンプレート
└── pyproject.toml
```

アーキテクチャの詳細は [docs/architecture.ja.md](docs/architecture.ja.md)（日本語）/ [docs/architecture.md](docs/architecture.md)（English）を参照してください。

---

## テストの実行

```bash
pytest
```

---

## セキュリティに関する注意

- `.env` は `.gitignore` で管理対象外になっています。**絶対にコミットしないでください**。
- Discord のメンション（`<@...>`, `<#...>`, `<@&...>`）は保存前に `@user` / `#channel` / `@role` へ自動置換されます。内部 ID は残りません。
- トークンが漏洩した場合は、Discord Token と GitHub PAT を**即時ローテーション**してください。

