"""证明翻译器（主线，开发中）。

目标：在"形式化证明 ↔ 自然语言（中文优先）"之间搭桥。
- formal → 中文可读证明：解释每个 tactic 在干什么、为什么
- 中文 → Lean 骨架：把自然语言证明转成 Lean 证明框架

当前状态：骨架 + LLM 适配器接口，主体功能在 roadmap 阶段 ②。
"""

from .llm import LLMBackend, get_default_llm

__all__ = ["LLMBackend", "get_default_llm"]
