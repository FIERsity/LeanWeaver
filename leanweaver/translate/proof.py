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

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .llm import LLMBackend, get_default_llm
from .parser import ProofBlock, extract_proof, extract_proofs
from .state import ProofTrace, StateStep, extract_state_trace


# 战术 ↔ 中文术语对照表（数据层，供翻译器提升中文质量）
_GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "data" / "tactic_glossary.json"

# Herald few-shot 示例库（真实「形式化证明 → 自然语言」配对，ICLR 2025）
_HERALD_FEWSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "herald_fewshot.json"


def _load_glossary() -> str:
    """加载术语表，返回适合注入 prompt 的文本。"""
    try:
        data = json.loads(_GLOSSARY_PATH.read_text(encoding="utf-8"))
        lines = []
        for item in data.get("tactics", []):
            lines.append(f"- {item['tactic']}: 中文 [{item['zh']}] —— {item['meaning']}")
        return "\n".join(lines)
    except Exception:
        return ""


def _load_herald_fewshot(n: int = 2) -> str:
    """加载 Herald few-shot 样本，返回适合注入 prompt 的文本。

    用真实「形式化证明 → 自然语言解释」配对教模型如何翻译。
    n: 取前 n 条（控制 token 预算）。
    """
    try:
        data = json.loads(_HERALD_FEWSHOT_PATH.read_text(encoding="utf-8"))
        parts = []
        for sample in data.get("samples", [])[:n]:
            parts.append(
                f"### Example: {sample['name']}\n"
                f"Formal proof:\n{sample['formal_proof']}\n\n"
                f"Readable explanation:\n{sample['informal_proof']}\n"
            )
        return "\n".join(parts)
    except Exception:
        return ""

# 让 LLM 解释单个 tactic 的 system prompt
_TACTIC_SYSTEM = """You are a Lean 4 theorem prover tutor. You will be given:
- a theorem statement (in Lean)
- one proof step (a tactic) from a proof
- the proof state BEFORE this step
- the proof state AFTER this step

Explain in plain {lang} what this step does and WHY it makes sense.
IMPORTANT: Base your explanation strictly on the provided "Before this step" and "After this step" states. Compare them to see exactly what changed. The "Before" state is the authoritative truth of what needed to be proved at this point.
Keep it concise (2-4 sentences). Focus on the mathematical idea, not the syntax.
"""

# 让 LLM 解释单个 tactic（带状态）的 user prompt 模板
_TACTIC_STATE_USER = """--- PROOF STATE BEFORE THIS STEP (this is what currently needs to be proved) ---
{before}

Tactic executed at this step:
{tactic}

--- PROOF STATE AFTER THIS STEP ---
{after}

Note: the line starting with "⊢" in the BEFORE state is the current goal for this step. Explain ONLY how this tactic transforms the BEFORE goal into the AFTER state.
"""

# 术语表（仅中文时注入，帮助对齐数学术语）
_GLOSSARY_HINT = """
参考资料（Lean 战术的中文标准译法，翻译时优先采用）：
{glossary}
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

# 注释翻译模式（commented）：输出逐行中文注释的证明（Herald commented_proof 风格）
_COMMENTED_SYSTEM = """You are a Lean 4 theorem prover tutor. You will be given:
- a theorem statement
- the list of tactics used to prove it

Produce a {lang} ANNOTATED version of the proof, where you KEEP the original Lean
tactic code line by line and add a comment after each tactic explaining in {lang}
what it does and why. Format:

```lean
theorem ... := by
  tactic1  -- 注释：这一步...
  tactic2  -- 注释：这一步...
```

Style: like a teacher walking through the proof line by line. Comments in plain {lang}.
"""

# Herald few-shot 提示（教模型真实的高质量翻译范例）
_FEWSHOT_HINT = """
Here are real examples of formal proofs translated into readable explanations (from the Herald dataset):
{fewshot}

Follow the same style and level of detail in your answer.
"""


@dataclass
class ProofTranslation:
    """翻译结果。"""

    theorem_name: str
    theorem_stmt: str
    tactic_count: int
    line_by_line: list[dict[str, str]] = field(default_factory=list)  # {tactic, explanation}
    full_proof: str = ""              # 连贯可读证明
    commented: str = ""              # 注释模式输出（逐行中文/英文注释）
    target_lang: str = "zh"

    def to_dict(self) -> dict[str, Any]:
        return {
            "theorem": self.theorem_name,
            "statement": self.theorem_stmt,
            "tactic_count": self.tactic_count,
            "line_by_line": self.line_by_line,
            "full_proof": self.full_proof,
            "commented": self.commented,
            "target_lang": self.target_lang,
        }

    def pretty(self, include_commented: bool = False) -> str:
        lang_label = {"zh": "中文可读证明", "en": "Readable proof"}.get(
            self.target_lang, self.target_lang
        )
        lines = [f"定理 {self.theorem_name}：{self.theorem_stmt}", ""]
        lines.append(f"【{lang_label}】")
        lines.append(self.full_proof)
        if include_commented and self.commented:
            lines += ["", "【逐行注释】"]
            lines.append(self.commented)
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
    before: str | None = None,
    after: str | None = None,
    sampling: dict | None = None,
) -> str:
    """解释单个 tactic（用于逐步解释）。

    有真实状态（before/after）时用状态差解释，更可靠；
    无状态时回退到纯文本（v1 行为）。
    """
    lang = "中文" if _lang_zh(target_lang) else "English"
    sys = _TACTIC_SYSTEM.format(lang=lang)
    if _lang_zh(target_lang):
        gl = _load_glossary()
        if gl:
            sys += "\n" + _GLOSSARY_HINT.format(glossary=gl)
    if before is not None:
        # 单步解释只依赖状态差（Before/After 已含全部上下文），
        # 不再传整个定理声明 —— 避免模型把声明结论误当成当前目标。
        # after 为 None 表示该步后证明完成。
        user = _TACTIC_STATE_USER.format(
            theorem="",
            before=before,
            tactic=tactic,
            after=after if after is not None else "(证明完成，无剩余目标)",
        )
    else:
        user = f"Theorem:\n{theorem_stmt}\n\nProof step:\n{tactic}"
    return llm.complete(sys, user, **(sampling or {}))


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
    # 采样参数（调用方可通过 sampling / env 传入 temperature 等）
    sampling = getattr(llm, "sampling", {})

    # 整篇可读证明的 system prompt：中文时注入术语表，双语都注入 Herald few-shot
    sys_proof = _PROOF_SYSTEM.format(lang=lang)
    if _lang_zh(target_lang):
        gl = _load_glossary()
        if gl:
            sys_proof += "\n" + _GLOSSARY_HINT.format(glossary=gl)
    fs = _load_herald_fewshot(n=2)
    if fs:
        sys_proof += "\n" + _FEWSHOT_HINT.format(fewshot=fs)
    result = ProofTranslation(
        theorem_name=block.theorem_name,
        theorem_stmt=block.theorem_stmt,
        tactic_count=len(block.tactics),
        target_lang=target_lang,
    )

    # 1. 尝试用 LeanREPL 提取真实状态轨迹（v2）
    # 需要完整的 `theorem <name> <sig>` 声明（不是只有 sig 部分）
    full_decl = f"theorem {block.theorem_name} {block.theorem_stmt}"
    trace = extract_state_trace(full_decl, block.tactics)
    has_state = trace.steps and not trace.error

    # 2. 逐步解释（有状态用状态差，无状态回退纯文本）
    for i, tactic in enumerate(block.tactics):
        before = trace.steps[i].before if has_state and i < len(trace.steps) else None
        after = trace.steps[i].after if has_state and i < len(trace.steps) else None
        try:
            exp = translate_tactic(
                llm, block.theorem_stmt, tactic, target_lang,
                before=before, after=after, sampling=sampling,
            )
            result.line_by_line.append({"tactic": tactic, "explanation": exp})
        except Exception as exc:
            result.line_by_line.append({"tactic": tactic, "explanation": f"（失败：{exc}）"})

    # 3. 连贯可读证明（有状态时也注入状态轨迹）
    user_parts = [f"Theorem:\n{block.theorem_stmt}", "Proof:"]
    if has_state:
        for i, step in enumerate(trace.steps):
            user_parts.append(
                f"  {i+1}. `{step.tactic}`  [before: {step.before.splitlines()[-1][:80]} → after: {(step.after or 'done').splitlines()[-1][:80]}]".replace("\n", " ")
            )
    else:
        for i, t in enumerate(block.tactics):
            user_parts.append(f"  {i+1}. {t}")
    user = "\n".join(user_parts)
    try:
        result.full_proof = llm.complete(sys_proof, user, **sampling)
    except Exception as exc:
        result.full_proof = f"（生成失败：{exc}）"

    # 4. 注释翻译模式（逐行注释，Herald commented_proof 风格）
    sys_commented = _COMMENTED_SYSTEM.format(lang=lang)
    fs = _load_herald_fewshot(n=1)
    if fs:
        sys_commented += "\n" + _FEWSHOT_HINT.format(fewshot=fs)
    commented_user = (
        f"Theorem:\n{block.theorem_stmt}\n\nProof (tactics):\n"
        + "\n".join(f"  {i+1}. {t}" for i, t in enumerate(block.tactics))
    )
    try:
        result.commented = llm.complete(sys_commented, commented_user, **sampling)
    except Exception as exc:
        result.commented = f"（生成失败：{exc}）"

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
