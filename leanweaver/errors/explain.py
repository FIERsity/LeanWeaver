"""错误解释器主入口。

纯规则、零 LLM：
1. 接收一条 Lean 报错文本
2. 分类（classify，确定性）
3. 渲染中英文解释（templates）

无网络、无 API、无幻觉 —— 每个解释都是确定性的。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .classify import ErrorCategory, ErrorInfo, classify_error
from .templates import render


@dataclass
class ExplainResult:
    """一次解释的结果。"""

    category: ErrorCategory
    original: str                    # 原始报错
    title: str                       # 中/英文标题
    what: str                        # 通俗解释
    why: list[str] = field(default_factory=list)   # 常见原因
    fix: list[str] = field(default_factory=list)   # 修复建议
    example: Optional[str] = None    # 示例
    matched_keyword: Optional[str] = None
    lang: str = "en"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "title": self.title,
            "what": self.what,
            "why": self.why,
            "fix": self.fix,
            "example": self.example,
            "matched_keyword": self.matched_keyword,
            "lang": self.lang,
        }

    def pretty(self) -> str:
        """人类可读的输出（CLI 用，locale-aware 标签）。"""
        if self.lang == "zh":
            why_label, fix_label, example_label = "常见原因", "修复建议", "示例"
            matched_label = "命中关键词"
        else:
            why_label, fix_label, example_label = "Common causes", "Fixes", "Example"
            matched_label = "matched keyword"
        lines = [f"[{self.title}]", "", self.what]
        if self.why:
            lines += ["", f"{why_label}:"]
            lines += [f"  - {w}" for w in self.why]
        if self.fix:
            lines += ["", f"{fix_label}:"]
            lines += [f"  - {f}" for f in self.fix]
        if self.example:
            lines += ["", f"{example_label}:", f"  {self.example}"]
        if self.matched_keyword:
            lines += ["", f"({matched_label}: {self.matched_keyword})"]
        return "\n".join(lines)


def explain(
    message: str,
    code: str | None = None,
    lang: str = "en",
) -> ExplainResult:
    """解释一条 Lean 报错（纯规则，确定性）。

    Args:
        message: Lean 报错文本。
        code: 可选的出错代码片段（用于增强解释）。
        lang: 解释语言（en 默认 / zh 插件）。

    Returns:
        ExplainResult。
    """
    info: ErrorInfo = classify_error(message)
    rendered = render(info.category, code=code, lang=lang)

    return ExplainResult(
        category=info.category,
        original=message,
        title=rendered["title"],
        what=rendered["what"],
        why=rendered["why"],
        fix=rendered["fix"],
        example=rendered.get("example"),
        matched_keyword=info.matched_keyword,
        lang=lang,
    )
