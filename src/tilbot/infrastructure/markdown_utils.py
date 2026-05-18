from __future__ import annotations
from dataclasses import dataclass
import re
from typing import List 

HEADER_WITH_ID_RE = re.compile(
    r"^##\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+<!--\s*msg_id:\s*(\d+)\s*-->\s*$"
) #TILエントリーのヘッダーをマッチさせる正規表現。メッセージIDをキャプチャするグループを含む
HEADER_ANY_RE = re.compile(r"^##\s+") #任意のヘッダーをマッチさせる正規表現。IDの有無に関わらずヘッダー行を識別するために使用

@dataclass(frozen=True)
class EntryBlock:
    """マークダウン内のTILエントリーのブロックを表すデータクラス"""
    message_id: int
    start_idx: int
    end_idx: int
    text: str

def parse_blocks(markdown: str) -> List[EntryBlock]:
    """マークダウンからエントリーブロックのリストを抽出する"""
    lines = markdown.splitlines(keepends=True) #行末の改行を保持して分割
    
    line_starts: List[int] = []    
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) #各行の開始位置を計算してリストに保存することで、後でブロックのテキストを抽出する際にスライスのインデックスを正確に計算できるようにする

    header_lines: List[int] = [
        i for i,line in enumerate(lines) if HEADER_ANY_RE.match(line.rstrip("\n"))
    ] #ヘッダー行のインデックスを収集

    blocks: List[EntryBlock] = [] #エントリーブロックのリストを初期化
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