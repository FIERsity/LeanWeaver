"""证明翻译器核心（v1：文本级翻译）。

流程：
1. 从 Lean 源码提取证明块（parser.extract_proof）
2. 把「定理声明 + tactic 序列」结构化喂给 LLM
3. LLM 输出：逐步中文（默认）可读证明 + 每步解释

v1 定位：不接 Pantograph，不做 proof-state 级解析。
先证明"formal → 自然语言"的链路能跑通，v2 再加深。

设计要点（从 verbose-lean4 学习的启示）：
- 我们要求 LLM 输出两种东西：**逐行解释**（每个 tactic 在干嘛）+ **连贯可读证明**
  （把 tactic 串成论文风格的自然语言段落）
- 强调"为什么这一步"——这是用户最想要的（对应掘金/Reddit 调研里的核心痛点）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .llm import LLMBackend, get_default_llm
from .parser import ProofBlock, extract_proof, extract_proofs

# 让 LLM 解释单个 tactic 的 system prompt
_TACTIC_SYSTEM = """You are a Lean 4 theorem prover tutor. You will be given:
- a theorem statement (in Lean)
- one proof step (a tactic) from a proof

Explain in plain {lang} what this step does and WHY it makes sense.
Keep it concise (2-4 sentences). Focus on the mathematical idea, not the syntax.
"""

# 生成完整可读证明的 system prompt
_PROOF_SYSTEM = """You are a Lean 4 theorem prover tutor helping mathematicians
understand formal proofs. You will be given:
- a theorem statement
- the list of tactics used to prove it

Produce a READABLE, COHERENT natural-language proof in {lang}, written the way
a mathematician would write it in a paper. Structure it with paragraphs or bullet points.
For each major step, briefly note which tactic implements it (e.g. "（`rw [h]`）").
Do NOT just translate the tactics literally — write real mathematical prose.
"""


@dataclass
class ProofTranslation:
    """翻译结果。"""

    theorem_name: str
    theorem_stmt: str
    tactic_count: int
    line_by_line: list[dict[str, str]] = field(default_factory=list)  # {tactic, explanation}
    full_proof: str = ""              # 连贯可读证明
    target_lang: str = "zh"

    def to_dict(self) -> dict[str, Any]:
        return {
            "theorem": self.theorem_name,
            "statement": self.theorem_stmt,
            "tactic_count": self.tactic_count,
            "line_by_line": self.line_by_line,
            "full_proof": self.full_proof,
            "target_lang": self.target_lang,
        }

    def pretty(self) -> str:
        lang_label = {"zh": "中文可读证明", "en": "Readable proof"}.get(
            self.target_lang, self.target_lang
        )
        lines = [f"定理 {self.theorem_name}：{self.theorem_stmt}", ""]
        lines.append(f"【{lang_label}】")
        lines.append(self.full_proof)
        if self.line_by_line:
            lines += ["", "【逐步解释】"]
            for item in self.line_by_line:
                lines.append(f"  • `{item['tactic']}`")
                lines.append(f"    {item['explanation']}")
        return "\n".join(lines)


def _lang_zh(lang: str) -> bool:
    return lang == "zh"


def translate_tactic(
    llm: LLMBackend,
    theorem_stmt: str,
    tactic: str,
    target_lang: str = "zh",
) -> str:
    """解释单个 tactic（用于逐步解释）。"""
    lang = "中文" if _lang_zh(target_lang) else "English"
    sys = _TACTIC_SYSTEM.format(lang=lang)
    user = f"Theorem:\n{theorem_stmt}\n\nProof step:\n{tactic}"
    return llm.complete(sys, user)


def translate_proof_block(
    block: ProofBlock,
    target_lang: str = "zh",
    llm: LLMBackend | None = None,
) -> ProofTranslation:
    """翻译一个证明块。"""
    llm = llm or get_default_llm()
    if llm is None:
        raise RuntimeError(
            "未配置 LLM。证明翻译需要模型。设置环境变量：\n"
            "  LEANWEAVER_LLM_PROVIDER=openai  +  OPENAI_API_KEY=...\n"
            "  或 LEANWEAVER_LLM_PROVIDER=ollama（本地 Ollama）"
        )

    lang = "中文" if _lang_zh(target_lang) else "English"
    result = ProofTranslation(
        theorem_name=block.theorem_name,
        theorem_stmt=block.theorem_stmt,
        tactic_count=len(block.tactics),
        target_lang=target_lang,
    )

    # 1. 逐步解释（每个 tactic 单独问）
    for tactic in block.tactics:
        try:
            exp = translate_tactic(llm, block.theorem_stmt, tactic, target_lang)
            result.line_by_line.append({"tactic": tactic, "explanation": exp})
        except Exception as exc:
            result.line_by_line.append({"tactic": tactic, "explanation": f"（失败：{exc}）"})

    # 2. 连贯可读证明（一次生成整篇）
    sys = _PROOF_SYSTEM.format(lang=lang)
    user = (
        f"Theorem:\n{block.theorem_stmt}\n\n"
        f"Proof (tactics):\n" + "\n".join(f"  {i+1}. {t}" for i, t in enumerate(block.tactics))
    )
    try:
        result.full_proof = llm.complete(sys, user)
    except Exception as exc:
        result.full_proof = f"（生成失败：{exc}）"

    return result


def translate_source(
    source: str,
    theorem_name: str | None = None,
    target_lang: str = "zh",
    llm: LLMBackend | None = None,
) -> list[ProofTranslation]:
    """翻译整个 Lean 源码中的所有证明（或指定定理）。"""
    if theorem_name:
        block = extract_proof(source, theorem_name)
        if block is None:
            raise ValueError(f"未找到定理 {theorem_name}")
        return [translate_proof_block(block, target_lang, llm)]

    blocks = extract_proofs(source)
    return [translate_proof_block(b, target_lang, llm) for b in blocks]
