# Design Decisions

This document records the key architectural and implementation decisions made in this project, along with the reasoning behind each choice.

---

## 1. Layered Architecture (Presentation / Application / Domain / Infrastructure)

**Decision**: Separate the codebase into four layers with strict one-way dependency flow.

**Reason**:
- Each layer has a single responsibility, making the code easier to read and modify independently.
- The domain layer has no external dependencies, so business rules can be tested without Discord or GitHub.
- Swapping the storage backend (e.g., replacing GitHub with a database) only requires changing the infrastructure layer.

**Trade-off**: More files and indirection than a simple single-file bot. Acceptable given the number of moving parts (Discord events, GitHub API, Markdown parsing).

---

## 2. `ITilRepository` Interface in the Domain Layer

**Decision**: Define an abstract interface `ITilRepository` in the domain layer; have `GithubTilRepository` implement it in the infrastructure layer.

**Reason**:
- Dependency Inversion Principle — the application layer depends on an abstraction, not a concrete GitHub implementation.
- Tests can inject a `MagicMock` instead of a real GitHub client, making unit tests fast and reliable without network access.

---

## 3. `asyncio.to_thread` for GitHub API Calls

**Decision**: Wrap all `GithubTilRepository` calls with `asyncio.to_thread` in `TilService`.

**Reason**:
- PyGithub is a synchronous library. Calling it directly on the Discord event loop would block all other events (messages, heartbeats) until the HTTP request completes.
- `asyncio.to_thread` runs the blocking call on a thread pool, keeping the event loop free.

**Alternative considered**: An async GitHub library (e.g., `httpx` + raw REST). Rejected because PyGithub provides a higher-level API that reduces boilerplate significantly for this project size.

---

## 4. Edit Handler Uses `await`; Delete Handler Uses `asyncio.create_task`

**Decision**: `on_message_edit` awaits `update_message` directly. `on_message_delete` / `on_raw_message_delete` fire a background task via `_run_task`.

**Reason**:
- Edit needs to know whether the update succeeded before deciding whether to add the 🔁 reaction. Awaiting ensures the reaction is only added on success.
- Delete has no meaningful feedback channel (the message is already gone). Running it as a background task means the event handler returns immediately without holding up the event loop.

---

## 5. Delete Requires `message_id` Only (No `created_at`)

**Decision**: `TilService.delete_message` and `ITilRepository.delete` take only `message_id`, not a timestamp.

**Reason**:
- `on_raw_message_delete` fires when Discord removes a message that is no longer in the client cache (e.g., bot restarted). In this case, only `payload.message_id` is available — there is no `created_at`.
- Using a unified signature for both cached and uncached deletes avoids two separate code paths.

---

## 6. Month ±1 Scan Strategy for Delete

**Decision**: When deleting, scan the current month, the previous month, and the next month (`_month_candidates`), stopping at the first match.

**Reason**:
- A message sent just before midnight on the last day of a month may be stored under the previous month's file. Similarly, timezone conversion (UTC → JST) can shift a message to the next calendar month.
- Scanning only the current month would silently fail to delete such entries.
- Three files is a bounded, cheap scan — it never grows regardless of how many TIL entries exist.

---

## 7. `on_raw_message_delete` as a Fallback

**Decision**: Implement both `on_message_delete` (cached) and `on_raw_message_delete` (uncached).

**Reason**:
- Discord.py only fires `on_message_delete` if the deleted message is still in the internal message cache. The cache has a size limit and is cleared on bot restart.
- Without `on_raw_message_delete`, any delete that occurs after the bot restarts or when the cache overflows would be silently ignored.

---

## 8. 409 Conflict Retry (Up to 3 Attempts)

**Decision**: On a `GithubException` with status 409, re-fetch the file and retry the update/delete up to `MAX_RETRIES = 3` times.

**Reason**:
- GitHub's file update API uses optimistic locking via a `sha` parameter. If two writes race, the second will receive a 409 because its `sha` is now stale.
- Re-fetching the file gives the latest `sha` and content, allowing a clean retry without losing either write.
- Three attempts covers realistic concurrent scenarios (e.g., rapid edits) without looping indefinitely.

---

## 9. Embedding `msg_id` as an HTML Comment in Markdown

**Decision**: Store the Discord message ID as `<!-- msg_id: 123456 -->` in the Markdown header line.

**Reason**:
- A stable, unique identifier is needed to locate and update/delete the correct entry later, regardless of content changes.
- HTML comments are invisible when the Markdown is rendered (e.g., on GitHub), so they do not clutter the human-readable output.
- Storing the ID in the filename or a separate index file would complicate the storage structure unnecessarily.

---

## 10. Monthly File Format (`YYYY-MM.md`)

**Decision**: One Markdown file per calendar month, appended to chronologically.

**Reason**:
- Grouping by month keeps individual files at a manageable size.
- The file name is directly derivable from a timestamp, so no index or lookup table is needed to find which file to read.
- GitHub renders Markdown files natively, so the TIL log is immediately human-readable in the repository.

---

## 11. Discord Mention Sanitization

**Decision**: Replace `<@user_id>`, `<#channel_id>`, and `<@&role_id>` patterns with human-readable placeholders before saving.

**Reason**:
- Raw Discord mention syntax (e.g., `<@123456789>`) is meaningless outside of Discord and leaks internal snowflake IDs into the public GitHub repository.
- Sanitizing at the application layer (in `TilService`) keeps this concern out of both the domain model and the infrastructure.

---

## 12. 🔁 Reaction Only on Successful Edit

**Decision**: The 🔁 reaction is added to an edited message only after `update_message` completes without error.

**Reason**:
- Adding a reaction before confirming success would mislead the user into thinking the edit was saved when it may not have been.
- If `update_message` raises (e.g., `EntryNotFoundError` for an old message with no `msg_id`), the exception is logged and the handler returns quietly — no false feedback is given.
