"""内联补全（Copilot 式 ghost text）——纯粹的核心功能。

设计（用户指定）：
- 按下快捷键 → 上下文（含 proof state）注入
- 生成光标后面/下面最适合的 n 行补全
- 以虚字（ghost text）显示，接受后插入

与 suggest_next 的区别：
- suggest_next: 列候选 tactic + 验证层（教学/教练向）
- complete: 直接生成"接下来几行"的连续补全（Copilot 向，本模块）

流程：
1. 拿当前 proof state（LeanREPL 执行已写代码后）
2. 构造补全 prompt：状态 + 已写代码 + 光标位置
3. LLM 生成多行补全（只输出补全文本）
4. 可选：验证补全能推进（用 Lean 试跑补全 + 已写代码）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .llm import LLMBackend, get_default_llm
from .state import extract_state_trace


@dataclass
class CompletionResult:
    text: str                    # 补全文本（多行）
    state: str = ""              # 当前 proof state
    verified: bool = False       # 是否验证过
    error: Optional[str] = None


# 补全 prompt：让 LLM 直接生成光标后的连续代码
_COMPLETE_SYSTEM = """You are a Lean 4 theorem prover writing a proof.
You will be given:
- the current proof state (hypotheses + goal marked with ⊢)
- the code already written before the cursor

Write the next {n} lines of Lean tactic code that continue the proof and make
progress toward the goal. Rules:
- Output ONLY the Lean code lines (no markdown, no explanation, no "by")
- Each line must be a valid Lean tactic
- Prefer the simplest correct approach
- If the goal can be finished in one step, write that step
"""


def _clean_completion(text: str) -> str:
    """清理 LLM 输出为纯 Lean 代码行。"""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # 去掉 markdown 围栏和注释
        if s.startswith("```"):
            continue
        if s.startswith("--") or s.startswith("/-") or s.startswith("-/"):
            continue
        if s.startswith(("theorem", "lemma", "example", "def")):
            continue
        lines.append(s)
    return "\n".join(lines)


def complete(
    theorem: str,
    tactics: list[str],
    num_lines: int = 3,
    llm: LLMBackend | None = None,
    verify: bool = True,
) -> CompletionResult:
    """生成光标后的补全。

    Args:
        theorem: 定理声明。
        tactics: 光标前已写的 tactic 行。
        num_lines: 生成几行补全。
        llm: LLM 后端。
        verify: 是否用 Lean 验证补全可推进。

    Returns:
        CompletionResult。
    """
    llm = llm or get_default_llm()

    # 1. 拿当前状态
    trace = extract_state_trace(theorem, tactics)
    if trace.error:
        return CompletionResult(text="", error=trace.error)
    if not trace.steps:
        return CompletionResult(text="", error="无法提取证明状态")

    current_state = trace.steps[-1].after or trace.initial_goal
    if trace.completed:
        return CompletionResult(text="", error="证明已完成")

    if llm is None:
        return CompletionResult(text="", error="未配置 LLM")

    # 2. 构造 prompt
    code_before = "\n".join(tactics) if tactics else ""
    user = f"Current proof state:\n{current_state}\n\n"
    if code_before:
        user += f"Code before cursor:\n{code_before}\n\n"
    user += f"Write the next {num_lines} lines:"

    try:
        raw = llm.complete(_COMPLETE_SYSTEM.format(n=num_lines), user)
    except Exception as exc:
        return CompletionResult(text="", state=current_state, error=f"LLM 调用失败: {exc}")

    text = _clean_completion(raw)
    if not text:
        return CompletionResult(text="", state=current_state, error="LLM 返回空补全")

    # 3. 验证层：试跑 补全 + 已写代码，确认能推进
    if verify:
        try:
            vtrace = extract_state_trace(theorem, tactics + text.split("\n"))
            if vtrace.error:
                # 补全中有错误行——尝试去掉最后一行（可能是半截）
                partial = text.split("\n")
                vtrace2 = extract_state_trace(theorem, tactics + partial[:-1])
                if vtrace2.error or vtrace2.completed is False and not vtrace2.steps:
                    return CompletionResult(text=text, state=current_state, verified=False, error=None)
                if vtrace2.error:
                    return CompletionResult(text=text, state=current_state, verified=False, error=None)
                return CompletionResult(text=text, state=current_state, verified=True, error=None)
            return CompletionResult(text=text, state=current_state, verified=True, error=None)
        except Exception:
            pass

    return CompletionResult(text=text, state=current_state, verified=False, error=None)
