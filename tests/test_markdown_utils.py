import pytest

from tilbot.infrastructure.markdown_utils import (
    EntryNotFoundError,
    delete_by_message_id,
    parse_blocks,
    update_body_by_message_id,
)


def test_parse_blocks_extracts_msg_id_blocks() -> None:
    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "hello\n"
        "\n"
        "<!-- end_msg -->\n"
        "\n"
        "## 2026-05-16 10:40 <!-- msg_id: 456 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "world\n"
        "\n"
        "<!-- end_msg -->\n"
        "\n"
        "## 2026-05-16 10:50\n"
        "old format\n"
    )

    blocks = parse_blocks(markdown)

    assert len(blocks) == 2
    assert blocks[0].message_id == 123
    assert blocks[1].message_id == 456
    assert "hello" in blocks[0].text
    assert "world" in blocks[1].text


def test_update_body_by_message_id_replaces_body_only() -> None:
    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "hello\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    updated = update_body_by_message_id(markdown, 123, "new body")

    assert "## 2026-05-16 10:30 <!-- msg_id: 123 -->" in updated
    assert "new body" in updated
    assert "hello" not in updated


def test_delete_by_message_id_removes_block() -> None:
    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "hello\n"
        "\n"
        "<!-- end_msg -->\n"
        "\n"
        "## 2026-05-16 10:40 <!-- msg_id: 456 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "world\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    updated = delete_by_message_id(markdown, 123)

    assert "msg_id: 123" not in updated
    assert "msg_id: 456" in updated


def test_update_body_by_message_id_raises_when_missing() -> None:
    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "hello\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    with pytest.raises(EntryNotFoundError):
        update_body_by_message_id(markdown, 999, "new body")


def test_update_body_by_message_id_allows_heading_in_body() -> None:
    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123 -->\n"
        "<!-- end_header -->\n"
        "\n"
        "intro\n"
        "## body heading\n"
        "details\n"
        "\n"
        "<!-- end_msg -->\n"
    )

    updated = update_body_by_message_id(markdown, 123, "new body")

    assert "new body" in updated
    assert "## body heading" not in updated


def test_update_body_by_message_id_accepts_marker_with_trailing_spaces() -> None:
    markdown = (
        "## 2026-05-16 10:30 <!-- msg_id: 123 -->\n"
        "<!-- end_header -->   \n"
        "\n"
        "hello\n"
        "\n"
        "<!-- end_msg -->   \n"
    )

    updated = update_body_by_message_id(markdown, 123, "new body")

    assert "new body" in updated