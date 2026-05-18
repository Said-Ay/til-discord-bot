from tilbot.infrastructure.markdown_utils import parse_blocks


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