# Architecture

## Overview

Tilbot is a Discord bot that collects TIL posts from a specific channel and stores them as monthly Markdown files in a GitHub repository.  
The system follows a **layered architecture** to keep Discord-specific concerns, business logic, and persistence isolated.

```
┌──────────────────────────────────┐
│  Presentation (Discord events)   │  ← TilCog
├──────────────────────────────────┤
│  Application (use cases)         │  ← TilService
├──────────────────────────────────┤
│  Domain (business rules)         │  ← Til, ITilRepository
├──────────────────────────────────┤
│  Infrastructure (GitHub storage) │  ← GithubTilRepository
└──────────────────────────────────┘
```

Dependencies flow strictly **top-down**. The presentation layer never touches the GitHub API directly, and infrastructure is injected from outside via the domain interface (dependency inversion).

---

## Layers and Responsibilities

### Presentation Layer

**TilCog** ([src/tilbot/presentation/cogs/til_cog.py](../src/tilbot/presentation/cogs/til_cog.py))

| Event | Behaviour |
|-------|-----------|
| `on_message` | Filters by channel and bot, calls `process_message`. Reacts ✅ on success, ❌ on error. |
| `on_message_edit` | Skips same-content, bots, and off-channel edits. Awaits `update_message`; reacts 🔁 only on success. |
| `on_message_delete` | Filters channel and bot, then calls `delete_message` as a background task. |
| `on_raw_message_delete` | Fallback for cache-miss deletes. Calls `delete_message` by `message_id` only. |

> **Async safety**: The `_run_task` helper wraps coroutines in `asyncio.create_task` and catches all exceptions via `logger.exception`, so a GitHub API failure never crashes the bot.

### Application Layer

**TilService** ([src/tilbot/application/til_service.py](../src/tilbot/application/til_service.py))

- Orchestrates create, update, and delete flows.
- Sanitizes Discord mentions (`<@...>`, `<#...>`, `<@&...>`) so no internal IDs are stored.
- Converts UTC timestamps to JST before persisting.
- Runs blocking repository calls via `asyncio.to_thread` to avoid blocking the event loop.

### Domain Layer

- **Til** ([src/tilbot/domain/models.py](../src/tilbot/domain/models.py)) — Immutable dataclass with `content`, `created_at`, and `message_id`.
- **ITilRepository** ([src/tilbot/domain/repositories.py](../src/tilbot/domain/repositories.py)) — Abstract interface for `save`, `update`, and `delete`.
- **format_entry** ([src/tilbot/domain/formatters.py](../src/tilbot/domain/formatters.py)) — Pure function that renders a `Til` as a Markdown block.

### Infrastructure Layer

**GithubTilRepository** ([src/tilbot/infrastructure/github_repo.py](../src/tilbot/infrastructure/github_repo.py))

- Implements `ITilRepository` using the GitHub API (PyGithub).
- Auto-creates and appends to monthly `YYYY-MM.md` files.
- **409 conflict retry**: On concurrent edit conflicts, re-fetches the file and retries up to 3 times for both update and delete.
- **ID-only delete search**: Since `on_raw_message_delete` has no `created_at`, delete scans the current month ±1 month to locate the entry by `message_id` alone.

**markdown_utils** ([src/tilbot/infrastructure/markdown_utils.py](../src/tilbot/infrastructure/markdown_utils.py))

- Pure functions to parse, update, and delete TIL blocks identified by `<!-- msg_id: ... -->` comments.
- Entries without a `msg_id` (old format) are left untouched.

### Configuration and Bootstrapping

- **Config** ([src/tilbot/config.py](../src/tilbot/config.py)) — Reads environment variables; raises at startup if required values are missing.
- **TilBot / build_bot** ([src/tilbot/bot.py](../src/tilbot/bot.py)) — Manually wires dependencies and registers the Cog (manual DI).

---

## Data Flow

### Post

```
1. Message posted in #til
2. TilCog.on_message → channel/bot guard
3. TilService.process_message → sanitize, JST convert, build Til
4. GithubTilRepository.save → append to YYYY-MM.md
5. React ✅
```

### Edit

```
1. Message edited
2. TilCog.on_message_edit → same-content/bot/channel guard
3. TilService.update_message → sanitize, JST convert
4. GithubTilRepository.update → replace body by msg_id (retry on 409)
5. React 🔁 on success only
```

### Delete

```
1. Message deleted (cached → on_message_delete / uncached → on_raw_message_delete)
2. TilCog → channel/bot guard
3. TilService.delete_message (message_id only)
4. GithubTilRepository.delete → scan current month ±1, remove block by msg_id
```

---

## Class Relationships

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
