"""LeanWeaver — Make formal proofs readable to humans.

面向 Lean 4 定理证明器的中文工具链：
- 错误解释器（规则层 → LLM 兜底）
- 证明翻译器（formalf proof ↔ 自然语言，主线，开发中）
"""

__version__ = "0.1.0"

from .errors.explain import explain  # noqa: F401

__all__ = ["explain", "__version__"]
