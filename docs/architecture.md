# Architecture

## Overview

Tilbot is a Discord bot that collects TIL posts from a specific channel and stores them as monthly Markdown files in a GitHub repository. The system follows a layered structure to keep Discord-specific concerns, business logic, and persistence isolated.

## Layers and Responsibilities

### Presentation Layer

- **TilCog** ([src/tilbot/presentation/cogs/til_cog.py](../src/tilbot/presentation/cogs/til_cog.py))
  - Listens to Discord events and filters messages by channel.
  - Calls application services to process incoming messages.
  - Adds a reaction on successful save.

### Application Layer

- **TilService** ([src/tilbot/application/til_service.py](../src/tilbot/application/til_service.py))
  - Orchestrates TIL handling for create, update, and delete flows.
  - Sanitizes Discord mentions and converts timestamps to JST.
  - Delegates persistence to the repository interface.
  - Runs blocking repository calls in a thread via `asyncio.to_thread`.

### Domain Layer

- **Til** ([src/tilbot/domain/models.py](../src/tilbot/domain/models.py))
  - Immutable domain model representing a single TIL entry.
- **ITilRepository** ([src/tilbot/domain/repositories.py](../src/tilbot/domain/repositories.py))
  - Interface for persistence operations (`save`, `update`, `delete`).

### Infrastructure Layer

- **GithubTilRepository** ([src/tilbot/infrastructure/github_repo.py](../src/tilbot/infrastructure/github_repo.py))
  - Implements `ITilRepository` using the GitHub API (PyGithub).
  - Creates or updates monthly Markdown files (`YYYY-MM.md`).

### Configuration and Bootstrapping

- **Config** ([src/tilbot/config.py](../src/tilbot/config.py))
  - Reads configuration from environment variables.
- **TilBot / build_bot** ([src/tilbot/bot.py](../src/tilbot/bot.py))
  - Wires dependencies and registers the Cog.

## Data Flow

1. A Discord message is posted in the configured TIL channel.
2. `TilCog.on_message` filters and forwards the message to `TilService.process_message`.
3. `TilService` sanitizes content, converts timestamps, and builds a `Til` model.
4. `GithubTilRepository.save` appends the entry to `YYYY-MM.md` in GitHub.

## Class Relationships

```
TilCog --> TilService --> ITilRepository
                         ^
                         |
                 GithubTilRepository

TilService --> Til
TilBot/build_bot --> TilCog + TilService + Config
```

## Notes and Future Hooks

- Dependency direction is strictly from Presentation -> Application -> Domain.
  Infrastructure implements domain interfaces and is injected from the outside.
