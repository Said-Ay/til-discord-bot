from __future__ import annotations
from dataclasses import dataclass
import re

HEADER_WITH_ID_RE = re.compile(
    r"^##\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+<!--\s*msg_id:\s*(\d+)\s*-->\s*$"
) #TILエントリーのヘッダーをマッチさせる正規表現。メッセージIDをキャプチャするグループを含む
HEADER_ANY_RE = re.compile(r"^##\s+") #任意のヘッダーをマッチさせる正規表現。IDの有無に関わらずヘッダー行を識別するために使用


class EntryNotFoundError(Exception):
    """指定されたmessage_idのエントリーが見つからない場合に発生する例外"""

@dataclass(frozen=True)
class EntryBlock:
    """マークダウン内のTILエントリーのブロックを表すデータクラス"""
    message_id: int
    start_idx: int
    end_idx: int
    text: str

def parse_blocks(markdown: str) -> list[EntryBlock]:
    """マークダウンからエントリーブロックのリストを抽出する"""
    lines = markdown.splitlines(keepends=True) #行末の改行を保持して分割

    line_starts: list[int] = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) #各行の開始位置を計算してリストに保存することで、後でブロックのテキストを抽出する際にスライスのインデックスを正確に計算できるようにする

    header_lines: list[int] = [
        i for i,line in enumerate(lines) if HEADER_ANY_RE.match(line.rstrip("\n"))
    ] #ヘッダー行のインデックスを収集

    blocks: list[EntryBlock] = [] #エントリーブロックのリストを初期化
    for idx, line_no in enumerate(header_lines): #ヘッダー行をループして、TILエントリーのブロックを抽出する
        line = lines[line_no].rstrip("\n")
        match = HEADER_WITH_ID_RE.match(line)
        start_idx = line_starts[line_no]
        end_idx = len(markdown)
        if idx +1 < len(header_lines):
            next_line_no = header_lines[idx + 1]
            end_idx = line_starts[next_line_no]
        if not match:
            continue #ヘッダー行がTILエントリーの形式にマッチしない場合はスキップする
        message_id = int(match.group(1))
        text = markdown[start_idx:end_idx]
        blocks.append(EntryBlock(message_id=message_id, start_idx=start_idx, end_idx=end_idx, text=text))
    
    return blocks

def update_block_text(markdown: str, block: EntryBlock, new_body: str) -> str:
    """指定されたブロックのテキストを新しいテキストに置き換える"""
    target_text = markdown[block.start_idx:block.end_idx]
    if target_text != block.text: #ブロックのテキストがマークダウン内の対応するテキストと一致しない場合は、エラーを発生させることで、データの不整合を防止する
        raise ValueError("ブロックのテキストがマークダウン内の対応するテキストと一致しません")
    lines = block.text.splitlines()
    if not lines: #ブロックのテキストが空の場合は、エラーを発生させることで、無効な操作を防止する
        raise ValueError("ブロックのテキストが空です")
    
    header_line = lines[0]
    try: #ブロックのテキストから必要なマーカーを見つけるために、end_headerとend_msgの行番号を取得する。マーカーが見つからない場合はValueErrorをキャッチしてわかりやすいエラーメッセージを提供する
        end_header_idx = lines.index("<!-- end_header -->")
        end_msg_idx = lines.index("<!-- end_msg -->")
    except ValueError as exc: #valueerrorをキャッチして、必要なマーカーが見つからない場合にわかりやすいエラーメッセージを提供する
        raise ValueError("ブロックのテキストに必要なマーカーが含まれていません") from exc
    end_header_line = lines[end_header_idx]
    end_msg_line = lines[end_msg_idx]

    body = new_body.rstrip("\n") #新しいテキストの末尾の改行を削除することで、マークダウン内のエントリーのフォーマットを維持する
    new_block = f"{header_line}\n{end_header_line}\n\n{body}\n\n{end_msg_line}\n"
    return markdown[:block.start_idx] + new_block + markdown[block.end_idx:]

def delete_block(markdown: str, block: EntryBlock) -> str:
    """指定されたブロックをマークダウンから削除する"""
    target_text = markdown[block.start_idx:block.end_idx]
    if target_text != block.text:# 位置ズレ対策：本当に消していい文字かハサミを入れる前に最終チェック
         raise ValueError("ブロックのテキストがマークダウン内の対応するテキストと一致しません")
    new_text = markdown[:block.start_idx] + markdown[block.end_idx:]
    new_text = re.sub(r"\n{3,}", "\n\n", new_text) #後片付け:複数の改行を2つの改行に置き換えることで、マークダウン内の余分な空行を削除する
    return new_text.rstrip("\n") + "\n" #マナー：末尾の改行を1つにすることで、マークダウンのフォーマットを維持する


def _find_block_by_message_id(blocks: List[EntryBlock], message_id: int) -> EntryBlock:
    for block in blocks:
        if block.message_id == message_id:
            return block
    raise EntryNotFoundError(f"message_id {message_id} not found")


def update_body_by_message_id(markdown: str, message_id: int, new_body: str) -> str:
    blocks = parse_blocks(markdown)
    block = _find_block_by_message_id(blocks, message_id)
    return update_block_text(markdown, block, new_body)


def delete_by_message_id(markdown: str, message_id: int) -> str:
    blocks = parse_blocks(markdown)
    block = _find_block_by_message_id(blocks, message_id)
    return delete_block(markdown, block)