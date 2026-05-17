from tilbot.domain.models import Til

def format_entry(til: Til) ->str:
    """TILを保存フォーマットに変換する"""
    header = (
        f"## {til.created_at.strftime('%Y-%m-%d %H:%M')} "
        f"<!-- msg_id: {til.message_id} -->"
    ) #TILの作成日時とDiscordのメッセージIDをヘッダーに含める
    end_header = "<!-- end_header -->" #ヘッダーの終わりを示すマーカー
    end_msg = "<!-- end_msg -->" #メッセージの終わりを示すマーカー

    body = til.content.rstrip("\n") # 末尾の改行を削除
    return f"{header}\n{end_header}\n\n{body}\n\n{end_msg}\n"