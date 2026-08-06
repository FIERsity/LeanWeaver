"""LeanWeaver — 让 Lean 4 报错对人有意义。

纯规则、确定性、零 LLM 依赖的 Lean 报错解释器。
- 毫秒级、离线、免费
- 中英文双语
- 覆盖 20+ 类高频报错（含 motive/calc 等疑难）

不接任何大模型 —— 每个解释都是确定性的，可复现，无幻觉。
"""

__version__ = "0.4.0"

from .errors.explain import explain  # noqa: F401

__all__ = ["explain", "__version__"]
