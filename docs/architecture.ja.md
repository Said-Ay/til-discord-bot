# アーキテクチャ

## 概要

Tilbot は、指定された Discord の TIL チャンネル投稿を収集し、GitHub リポジトリ内の月次 Markdown ファイルに保存するボットです。Discord 固有の処理、アプリケーションロジック、永続化処理を分離するためにレイヤ構成を採用しています。

## 各レイヤの役割

### プレゼンテーション層

- **TilCog** ([src/tilbot/presentation/cogs/til_cog.py](../src/tilbot/presentation/cogs/til_cog.py))
  - Discord のイベントを受け取り、チャンネルを判定します。
  - アプリケーション層に処理を委譲します。
  - 保存成功時にリアクションを付与します。

### アプリケーション層

- **TilService** ([src/tilbot/application/til_service.py](../src/tilbot/application/til_service.py))
  - TIL の作成・更新・削除フローを統括します。
  - メンションのサニタイズと JST 変換を行います。
  - 永続化はリポジトリインターフェースに委譲します。
  - GitHub API 呼び出しは `asyncio.to_thread` でスレッド実行します。

### ドメイン層

- **Til** ([src/tilbot/domain/models.py](../src/tilbot/domain/models.py))
  - 1件の TIL を表す不変モデルです。
- **ITilRepository** ([src/tilbot/domain/repositories.py](../src/tilbot/domain/repositories.py))
  - 永続化操作のインターフェース（`save`, `update`, `delete`）。

### インフラストラクチャ層

- **GithubTilRepository** ([src/tilbot/infrastructure/github_repo.py](../src/tilbot/infrastructure/github_repo.py))
  - `ITilRepository` の実装。
  - GitHub API を通じて `YYYY-MM.md` に追記します。

### 設定と起動

- **Config** ([src/tilbot/config.py](../src/tilbot/config.py))
  - 環境変数から設定を読み込みます。
- **TilBot / build_bot** ([src/tilbot/bot.py](../src/tilbot/bot.py))
  - 依存関係を組み立て、Cog を登録します。

## データフロー

1. TIL チャンネルでメッセージが投稿されます。
2. `TilCog.on_message` が内容を取得し、`TilService.process_message` に渡します。
3. `TilService` がサニタイズと JST 変換を行い、`Til` を生成します。
4. `GithubTilRepository.save` が GitHub 上の `YYYY-MM.md` に追記します。

## クラスのつながり

```
TilCog --> TilService --> ITilRepository
                         ^
                         |
                 GithubTilRepository

TilService --> Til
TilBot/build_bot --> TilCog + TilService + Config
```

## 補足

- `TilService.update_message` / `delete_message` は実装済みですが、現在の Cog では Discord の編集・削除イベントにまだ接続されていません。
- 依存方向は Presentation -> Application -> Domain を守り、Infrastructure はドメインのインターフェース実装として外から注入します。
