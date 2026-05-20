# アーキテクチャ

## 概要

Tilbot は、指定された Discord の TIL チャンネル投稿を収集し、GitHub リポジトリ内の月次 Markdown ファイルに保存するボットです。  
Discord 固有の処理・アプリケーションロジック・永続化処理を分離するために **レイヤードアーキテクチャ** を採用しています。

```
┌──────────────────────────────────┐
│  Presentation（Discord イベント）  │  ← TilCog
├──────────────────────────────────┤
│  Application（ユースケース）       │  ← TilService
├──────────────────────────────────┤
│  Domain（ビジネスルール）          │  ← Til, ITilRepository
├──────────────────────────────────┤
│  Infrastructure（GitHub 永続化）   │  ← GithubTilRepository
└──────────────────────────────────┘
```

依存の方向は **上から下への一方通行**です。  
Presentation は Application を呼ぶだけで GitHub API を直接触らず、Infrastructure は Domain のインターフェースを実装して外部から注入されます（依存性の逆転）。

---

## 各レイヤの役割

### プレゼンテーション層

**TilCog** ([src/tilbot/presentation/cogs/til_cog.py](../src/tilbot/presentation/cogs/til_cog.py))

| イベント | 処理内容 |
|----------|----------|
| `on_message` | チャンネル・Bot フィルタ後、`process_message` を呼び出し。成功で ✅、失敗で ❌ |
| `on_message_edit` | 同内容・Bot・他チャンネルは無視。`update_message` を await し、成功時のみ 🔁 |
| `on_message_delete` | チャンネル・Bot フィルタ後、`delete_message` を非同期タスクで実行 |
| `on_raw_message_delete` | キャッシュなし削除の保険。対象チャンネルなら `delete_message` を非同期タスクで実行 |

> **非同期安全化**: `_run_task` ヘルパーが `asyncio.create_task` でラップし、例外は必ず `logger.exception` で記録してボットが落ちないようにします。

### アプリケーション層

**TilService** ([src/tilbot/application/til_service.py](../src/tilbot/application/til_service.py))

- TIL の作成・更新・削除フローを統括します。
- Discord メンション（`<@...>`, `<#...>`, `<@&...>`）をサニタイズして内部 ID を除去します。
- タイムスタンプを JST に変換して保存します。
- GitHub API（同期処理）は `asyncio.to_thread` でスレッド実行し、イベントループをブロックしません。

### ドメイン層

- **Til** ([src/tilbot/domain/models.py](../src/tilbot/domain/models.py)) — 1件の TIL を表す不変データクラス（`content`, `created_at`, `message_id`）。
- **ITilRepository** ([src/tilbot/domain/repositories.py](../src/tilbot/domain/repositories.py)) — 永続化操作の抽象インターフェース（`save`, `update`, `delete`）。
- **format_entry** ([src/tilbot/domain/formatters.py](../src/tilbot/domain/formatters.py)) — Markdown エントリを組み立てる純粋関数。

### インフラストラクチャ層

**GithubTilRepository** ([src/tilbot/infrastructure/github_repo.py](../src/tilbot/infrastructure/github_repo.py))

- `ITilRepository` を GitHub API で実装します。
- 月次ファイル（`YYYY-MM.md`）を自動作成・追記します。
- **update/delete 時の 409 Conflict** に対して最大 3 回のリトライを行います（再取得 → 再パース → 再更新）。
- **delete のファイル探索**: `message_id` のみで削除できるよう、実行時の現在月を基準に ±1 か月のファイルを順に探索し、見つかった時点で即終了します。

**markdown_utils** ([src/tilbot/infrastructure/markdown_utils.py](../src/tilbot/infrastructure/markdown_utils.py))

- Markdown 内の TIL ブロックを `msg_id` コメントで識別してパース・更新・削除する純粋関数群です。
- `msg_id` を持たない古いフォーマットのエントリは変更しません。

### 設定と起動

- **Config** ([src/tilbot/config.py](../src/tilbot/config.py)) — 環境変数から設定を読み込み、必須項目が欠けていれば起動前にエラーを出します。
- **TilBot / build_bot** ([src/tilbot/bot.py](../src/tilbot/bot.py)) — 依存オブジェクトを組み立てて Cog を登録します（手動 DI）。

---

## データフロー

### メッセージ投稿

```
1. #til にメッセージ投稿
2. TilCog.on_message → チャンネル・Bot チェック
3. TilService.process_message → サニタイズ・JST 変換・Til 生成
4. GithubTilRepository.save → YYYY-MM.md に追記
5. ✅ リアクション付与
```

### メッセージ編集

```
1. メッセージ編集
2. TilCog.on_message_edit → 同内容・Bot・チャンネルチェック
3. TilService.update_message → サニタイズ・JST 変換
4. GithubTilRepository.update → msg_id でエントリ本文を差し替え（409 時はリトライ）
5. 成功時のみ 🔁 リアクション付与
```

### メッセージ削除

```
1. メッセージ削除（キャッシュあり → on_message_delete / なし → on_raw_message_delete）
2. TilCog → チャンネル・Bot チェック
3. TilService.delete_message（message_id のみ）
4. GithubTilRepository.delete → 現在月±1 を探索して msg_id のブロックを削除
```

---

## クラスのつながり

```
TilCog ──▶ TilService ──▶ ITilRepository
                               ▲
                               │ implements
                    GithubTilRepository
                               │
                       markdown_utils

TilService ──▶ Til
TilService ──▶ format_entry
build_bot ──▶ TilCog + TilService + GithubTilRepository + Config
```
