"""错误解释器主入口。

职责：
1. 接收一条 Lean 报错文本（LSP diagnostic message）
2. 分类（classify）
3. 渲染中文解释（templates）
4. 可选：规则未命中时调用 LLM 兜底（本模块默认关闭，见 leanweaver.translate.llm）

对外保持简单接口：`explain(message, code=None) -> ExplainResult`。
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
    title: str                       # 中文标题
    what: str                        # 通俗解释
    why: list[str] = field(default_factory=list)   # 常见原因
    fix: list[str] = field(default_factory=list)   # 修复建议
    example: Optional[str] = None    # 示例
    matched_keyword: Optional[str] = None
    used_llm: bool = False           # 是否走了 LLM 兜底
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
            "used_llm": self.used_llm,
            "lang": self.lang,
        }

    def pretty(self) -> str:
        """Human-readable output for the CLI (locale-aware labels)."""
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
    use_llm: bool = False,
    llm=None,
    lang: str = "en",
) -> ExplainResult:
    """解释一条 Lean 报错。

    Args:
        message: Lean 报错文本（LSP diagnostic message）。
        code: 可选的出错代码片段，用于增强解释。
        use_llm: 规则未命中时是否用 LLM 兜底（默认关闭）。
        llm: 可选的 LLM 适配器实例（见 translate.llm），use_llm=True 时需要。
        lang: 解释语言（默认 en；zh 为可选插件）。

    Returns:
        ExplainResult。
    """
    info: ErrorInfo = classify_error(message)
    rendered = render(info.category, code=code, lang=lang)

    result = ExplainResult(
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

    # 规则未命中 → 可选 LLM 兜底
    if info.category is ErrorCategory.UNKNOWN and use_llm:
        if llm is None:
            from ..translate.llm import get_default_llm

            llm = get_default_llm()
        if llm is not None:
            try:
                text = llm.explain_error(message, code=code, lang=lang)
                result.used_llm = True
                result.what = text
                result.why = []
                result.fix = []
            except Exception as exc:  # LLM 失败不影响结果
                result.why.append(f"（LLM 兜底失败：{exc}）")

    return result
