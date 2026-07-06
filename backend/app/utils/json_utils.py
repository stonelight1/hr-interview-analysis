import json


def clean_json_text(text: str) -> str:
    """清理 JSON 文本，去除可能的 markdown 代码块标记"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
