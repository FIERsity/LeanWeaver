"""证明翻译器（主线）。

目标：在"形式化证明 ↔ 自然语言"之间搭桥。
- formal → 中文/英文可读证明：逐步解释每个 tactic + 生成连贯可读证明
- 中文 → Lean 骨架：反向翻译（开发中）

当前状态：v1（文本级翻译，不依赖 Lean 状态机）已可用。
"""

from .llm import LLMBackend, OpenAIBackend, OllamaBackend, get_default_llm
from .parser import ProofBlock, extract_proof, extract_proofs
from .proof import ProofTranslation, translate_proof_block, translate_source

__all__ = [
    "LLMBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "get_default_llm",
    "ProofBlock",
    "extract_proof",
    "extract_proofs",
    "ProofTranslation",
    "translate_proof_block",
    "translate_source",
]
