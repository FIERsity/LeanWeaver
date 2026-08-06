"""Lean 错误解释器（规则层）。

将 Lean 4 LSP 输出的结构化诊断信息，分类并翻译成中文人话解释。
本层为纯规则实现，不依赖任何 LLM —— 快、免费、可离线。
"""

from .classify import classify_error, ErrorCategory
from .explain import explain, ExplainResult
from .templates import available_languages

__all__ = ["classify_error", "ErrorCategory", "explain", "ExplainResult", "available_languages"]
