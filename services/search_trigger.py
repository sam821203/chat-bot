"""Determines whether to force a search before answering (agent mode)."""

# 觸發詞：含任一時即強制先執行 Google 搜尋再回答（僅 Agent 模式）
TRIGGER_KEYWORDS = frozenset({
    "最近", "最新", "目前", "現在", "今年", "近期", "即時",
    "戰爭", "衝突", "疫情", "選舉", "談判",
    "世足", "冠軍", "股價", "匯率", "查最新", "幫我查", "搜尋",
    "recent", "latest", "current", "now", "war", "election", "search",
})


def should_force_search(content: str) -> bool:
    """若用戶訊息包含觸發詞則回傳 True（用於強制先搜再答）。"""
    if not content or not isinstance(content, str):
        return False
    text = content.strip()
    return any(kw in text for kw in TRIGGER_KEYWORDS)


class SearchTriggerChecker:
    """Checks if user content should trigger a forced search before answering."""

    @staticmethod
    def should_force_search(content: str) -> bool:
        return should_force_search(content)
