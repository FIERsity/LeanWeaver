"""下一步证明建议（吸取 LeanCopilot 的验证层思想）。

核心流程（质量关键 = 建议必须经过"实际执行验证"）：
1. 拿到当前 proof state（LeanREPL 执行已写的 tactic 后）
2. LLM 生成 N 个候选 tactic
3. 【验证层】逐个用 LeanREPL 实际执行候选：
   - 执行失败 → 丢弃
   - 执行成功但目标数没减少 → 丢弃（无推进）
   - 执行成功且目标减少 → 保留
   - 目标清空 → 标记为"可完成证明"（最强建议）
4. 返回验证过的、按推进力排序的建议

与 LeanCopilot 的区别：
- 它用专用小模型 + Lean 包内建议
- 我们用通用 LLM + 验证层 + 可在 VS Code 扩展中展示
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from .llm import LLMBackend, get_default_llm
from .state import extract_state_trace


@dataclass
class Suggestion:
    """一个验证过的建议。"""

    tactic: str                # 建议的 tactic
    verified: bool             # 是否通过验证（实际执行成功且推进）
    completes: bool            # 是否直接完成证明
    remaining_after: int       # 执行后剩余目标数
    explanation: str = ""      # 为什么建议这个（LLM 生成）
    score: float = 0.0         # 排序分数

    def to_dict(self) -> dict:
        return {
            "tactic": self.tactic,
            "verified": self.verified,
            "completes": self.completes,
            "remaining_after": self.remaining_after,
            "explanation": self.explanation,
            "score": self.score,
        }


# 生成候选 tactic 的 prompt
_SUGGEST_SYSTEM = """You are an expert Lean 4 theorem prover. The user is stuck on a proof.
You will be given the current proof state (hypotheses and the goal marked with ⊢).

Generate {n} DIFFERENT plausible next tactics that would make progress on this goal.
Return them as a JSON array of objects: [{{"tactic": "exact h", "reason": "为什么"}}, ...]
Each tactic must be a valid single Lean 4 tactic (no 'by', no full proof).
Cover different strategies when possible (e.g. exact/apply/constructor/rcases on hypotheses).
Do NOT output anything except the JSON array.
"""

# 解析候选
_CANDIDATE_RE = re.compile(
    r'\{\s*"tactic"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"reason"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}'
)


def parse_candidates(text: str) -> list[dict]:
    """从 LLM 输出解析候选 tactic。宽容解析：JSON 数组或逐行。"""
    candidates: list[dict] = []
    # 尝试整体 JSON
    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "tactic" in item:
                    candidates.append(
                        {"tactic": str(item["tactic"]).strip(), "reason": str(item.get("reason", ""))}
                    )
    except json.JSONDecodeError:
        pass

    # JSON 失败 → 尝试正则提取
    if not candidates:
        for m in _CANDIDATE_RE.finditer(text):
            candidates.append(
                {"tactic": m.group(1).replace("\\\"", '"'), "reason": m.group(2)}
            )

    # 还不行 → 逐行
    if not candidates:
        for line in text.splitlines():
            line = line.strip().lstrip("-•*1234567890.)")
            if line and not line.startswith(("```", "json", "[")):
                candidates.append({"tactic": line.strip(), "reason": ""})

    # 清理
    out = []
    seen = set()
    for c in candidates:
        t = c["tactic"].strip()
        if t and t not in seen:
            seen.add(t)
            out.append(c)
    return out


def _count_goals(state_text: str) -> int:
    """从状态文本估算目标数（⊢ 出现的次数）。"""
    return state_text.count("⊢")


def suggest_next(
    theorem: str,
    tactics: list[str],
    num_candidates: int = 6,
    target_lang: str = "zh",
    llm: LLMBackend | None = None,
    verify: bool = True,
) -> dict:
    """为卡住的证明建议下一步。

    Args:
        theorem: 定理声明（如 "theorem foo (a : Nat) : ..."）。
        tactics: 用户已写的 tactic 序列。
        num_candidates: LLM 生成候选数。
        target_lang: 解释语言。
        llm: LLM 后端。
        verify: 是否实际验证候选（默认 True，核心质量保证）。

    Returns:
        {"state": 当前状态文本, "suggestions": [Suggestion], "error": ...}
    """
    llm = llm or get_default_llm()

    # 1. 拿当前状态
    trace = extract_state_trace(theorem, tactics)
    if trace.error:
        return {"state": "", "suggestions": [], "error": trace.error}
    if not trace.steps:
        return {"state": "", "suggestions": [], "error": "无法提取证明状态"}
    if trace.completed:
        return {"state": "", "suggestions": [], "error": "证明已完成，无需建议"}

    # 当前状态 = 最后一步之后的目标（或初始目标）
    current_state = trace.steps[-1].after or trace.initial_goal
    current_goals = _count_goals(current_state)

    if llm is None:
        return {"state": current_state, "suggestions": [], "error": "未配置 LLM"}

    # 2. LLM 生成候选
    lang = "Chinese" if target_lang == "zh" else "English"
    sys = _SUGGEST_SYSTEM.format(n=num_candidates)
    user = f"Current proof state:\n{current_state}\n\nGenerate {num_candidates} next tactics in {lang}."
    try:
        raw = llm.complete(sys, user)
    except Exception as exc:
        return {"state": current_state, "suggestions": [], "error": f"LLM 调用失败: {exc}"}

    candidates = parse_candidates(raw)
    if not candidates:
        return {"state": current_state, "suggestions": [], "error": "LLM 未返回有效候选"}

    # 3. 验证层（核心）：逐个执行候选
    suggestions: list[Suggestion] = []
    if verify:
        # 重新用 LeanREPL 执行到当前状态
        vtrace = extract_state_trace(theorem, tactics)
        if not vtrace.steps or vtrace.error:
            return {"state": current_state, "suggestions": [], "error": "验证环境不可用"}

        try:
            from lean_interact import LeanREPLConfig, LeanServer, ProofStep, Command

            # 构造带 sorry 的定理拿初始状态
            sorry_stmt = f"{theorem} := by\n  sorry"
            config = LeanREPLConfig()
            server = LeanServer(config)
            try:
                res = server.run(Command(cmd=sorry_stmt))
                if not hasattr(res, "sorries") or not res.sorries:
                    return {"state": current_state, "suggestions": [], "error": "无法初始化验证环境"}
                state = res.sorries[0].proof_state
                # 先执行已写的 tactic 到当前点
                for t in tactics:
                    r = server.run(ProofStep(proof_state=state, tactic=t))
                    if type(r).__name__ == "LeanError":
                        return {"state": current_state, "suggestions": [], "error": f"已有 tactic 执行失败: {t}"}
                    state = getattr(r, "proof_state", state)

                # 逐个验证候选
                for cand in candidates:
                    tactic = cand["tactic"]
                    r = server.run(ProofStep(proof_state=state, tactic=tactic))
                    if type(r).__name__ == "LeanError":
                        continue  # 执行失败 → 丢弃
                    goals = getattr(r, "goals", None) or []
                    remaining = len(goals)
                    if remaining == 0:
                        # 完成证明 —— 最强建议
                        suggestions.append(
                            Suggestion(
                                tactic=tactic,
                                verified=True,
                                completes=True,
                                remaining_after=0,
                                explanation=cand["reason"],
                                score=float("inf"),
                            )
                        )
                        continue
                    # 有剩余目标：目标必须发生变化才算推进（即使数量相同，如 Q→P）
                    after_text = goals[0]
                    if after_text == current_state:
                        continue  # 目标完全没变 → 无推进，丢弃
                    # 目标数变少或目标内容变化 → 有效推进
                    suggestions.append(
                        Suggestion(
                            tactic=tactic,
                            verified=True,
                            completes=False,
                            remaining_after=remaining,
                            explanation=cand["reason"],
                            score=(current_goals - remaining) * 10 + 1,  # 目标减少优先
                        )
                    )
            finally:
                try:
                    server.kill()
                except Exception:
                    pass
        except ImportError:
            # 没有 lean-interact，跳过验证（退化）
            for cand in candidates:
                suggestions.append(
                    Suggestion(
                        tactic=cand["tactic"],
                        verified=False,
                        completes=False,
                        remaining_after=-1,
                        explanation=cand["reason"],
                    )
                )
    else:
        for cand in candidates:
            suggestions.append(
                Suggestion(
                    tactic=cand["tactic"],
                    verified=False,
                    completes=False,
                    remaining_after=-1,
                    explanation=cand["reason"],
                )
            )

    # 排序：能完成的在前，然后按推进力
    suggestions.sort(key=lambda s: (not s.completes, -s.score))
    return {
        "state": current_state,
        "suggestions": suggestions[:num_candidates],
        "error": None,
    }
