#!/usr/bin/env python3
"""
Safety Gate for OpenClaw Agent
Based on Afu Brain / MASL principles (simplified)
Detects high-risk actions before execution
"""

from enum import Enum
import re

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# High-risk patterns: actions that need explicit confirmation
HIGH_RISK_PATTERNS = [
    r'\btrash\b', r'\brm\b', r'\bdelete\b', r'\bdrop\b',
    r'\bexec.*sudo\b', r'\bexec.*chmod\b', r'\bchmod\s+777\b',
    r'\brm\s+-rf\b', r'\brm\s+-r\b',
]

# Critical patterns: actions that need full explanation + explicit approval
CRITICAL_PATTERNS = [
    r'\bsend.*email\b', r'\bsend.*mail\b', r'\bpost.*public\b',
    r'\bpayment\b', r'\btransfer\b', r'\b匯款\b', r'\b轉帳\b',
    r'\bcrontab\b.*replace', r'\bcrontab\b.*delete',
    r'\bsystemctl\b.*stop', r'\bsystemctl\b.*disable',
    r'\bopenaiclaw\s+gateway\b.*stop',
]

# Actions that are always safe (just read/notify)
SAFE_PATTERNS = [
    r'\bread\b', r'\bget\b', r'\blist\b', r'\bstatus\b',
    r'\bcheck\b', r'\bsearch\b', r'\bfetch\b', r'\bquery\b',
    r'\bnotify\b', r'\breport\b', r'\bgenerate\b',
]

# Medium risk: creates/changes but not destructive
MEDIUM_PATTERNS = [
    r'\bwrite\b', r'\bcreate\b', r'\bupload\b', r'\bappend\b',
    r'\bedit\b', r'\bmodify\b', r'\breplace\b',
    r'\bsend.*telegram\b', r'\bsend.*line\b',
]

def classify_action(action_text: str) -> tuple[RiskLevel, str, list[str]]:
    """
    Classify an action and return (risk_level, reason, matched_rules)
    """
    action_lower = action_text.lower()
    matched = []

    # Check critical first
    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, action_lower):
            return RiskLevel.CRITICAL, "涉及財務、系統或公開發送，需要完整說明並等待明確批准", [pattern]

    # Check high risk
    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, action_lower):
            return RiskLevel.HIGH, "涉及刪除或系統變更，需要確認", [pattern]

    # Check medium risk
    for pattern in MEDIUM_PATTERNS:
        if re.search(pattern, action_lower):
            return RiskLevel.MEDIUM, "會創建或修改資料，執行後會通知", [pattern]

    return RiskLevel.LOW, "安全操作，直接執行", []

def get_confirmation_message(action: str, risk: RiskLevel, reason: str) -> str:
    """Generate a confirmation request message"""
    if risk == RiskLevel.CRITICAL:
        return f"""⚠️ 【危險動作確認】
即將執行：高風險操作
內容：{action}
原因：{reason}

請明確回覆「確認執行」我才會繼續。"""

    elif risk == RiskLevel.HIGH:
        return f"""⚠️ 【需要確認】
即將執行：{action}
原因：{reason}

請回覆「是」或「確認」我才會執行。"""

    return ""

def explain_action(action: str, risk: RiskLevel) -> str:
    """Explain what will happen (for CRITICAL actions)"""
    if risk == RiskLevel.CRITICAL:
        return f"""即將執行的動作：
{action}

我會：
1. 說明具體會變更什麼
2. 等待你明確批准
3. 執行後回報結果

請問是否繼續？"""
    return ""