"""基于 LeanREPL 的真实证明状态提取（翻译器 v2 核心）。

用 lean-interact（LeanREPL 的 Python 封装）逐步执行证明，
拿到每一步的 proof state —— 即「前状态 → tactic → 后状态」三元组序列。

这是翻译质量的本质提升：LLM 看到真实的状态差，
才能可靠解释「这一步在做什么、为什么」。
（v1 只有 tactic 文本，没有状态，是"猜"；v2 有状态，是"看"。）

依赖：lean-interact（pip install lean-interact）+ 本机 lean（elan）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StateStep:
    """一步证明的状态变化。"""

    tactic: str                # 本步 tactic
    before: str                # 执行前的目标/上下文
    after: Optional[str]       # 执行后的剩余目标（None=已解决）
    is_error: bool = False     # 该步是否出错

    def to_dict(self) -> dict:
        return {
            "tactic": self.tactic,
            "before": self.before,
            "after": self.after,
            "is_error": self.is_error,
        }


@dataclass
class ProofTrace:
    """一个证明的完整状态轨迹。"""

    theorem_stmt: str               # 定理声明
    initial_goal: str               # 初始目标
    steps: list[StateStep] = field(default_factory=list)
    error: Optional[str] = None     # 执行过程错误

    @property
    def completed(self) -> bool:
        """证明是否完整执行（最后无剩余目标）。"""
        return bool(self.steps) and not self.steps[-1].after and not self.steps[-1].is_error

    def pretty(self) -> str:
        lines = [f"定理: {self.theorem_stmt}", f"初始目标: {self.initial_goal}", ""]
        for i, s in enumerate(self.steps):
            marker = "❌" if s.is_error else "✅"
            lines.append(f"  第{i+1}步 {marker} `{s.tactic}`")
            if s.before:
                lines.append(f"    前: {s.before.splitlines()[-1][:100]}")
            if s.after:
                lines.append(f"    后: {s.after.splitlines()[-1][:100]}")
        return "\n".join(lines)


def extract_state_trace(
    theorem: str,
    tactics: list[str],
    header: str = "",
    verbose: bool = False,
) -> ProofTrace:
    """用 LeanREPL 执行一个定理的证明，提取逐步状态。

    Args:
        theorem: 定理声明，如 "theorem demo (a b : Nat) : a + b = b + a := by"
        tactics: 证明的 tactic 序列（不含 by）。
        header: 可选的导入/前置代码（如 "import Mathlib"）。
        verbose: 是否打印 REPL 日志。

    Returns:
        ProofTrace：状态轨迹。
    """
    try:
        from lean_interact import Command, LeanREPLConfig, LeanServer, ProofStep
    except ImportError:
        return ProofTrace(
            theorem_stmt=theorem,
            initial_goal="",
            error="未安装 lean-interact，请执行 pip install lean-interact",
        )

    # 确保 lean/lake 可被找到：~/.elan/bin 通常不在 VS Code 扩展进程的 PATH 里
    import os as _os

    _elan_bin = Path.home() / ".elan" / "bin"
    if _elan_bin.exists():
        _os.environ["PATH"] = f"{_elan_bin}:{_os.environ.get('PATH', '')}"
        lake_candidate = _elan_bin / "lake"
        lean_candidate = _elan_bin / "lean"
    else:
        lake_candidate = None
        lean_candidate = None

    # 构造带 sorry 的定理，拿到初始 proof state
    sorry_stmt = f"{theorem} := by\n  sorry"
    if header:
        sorry_stmt = f"{header}\n{sorry_stmt}"

    try:
        # 显式传 lake 路径（lean-interact 默认只查 PATH）
        config = LeanREPLConfig(
            verbose=verbose,
            lake_path=str(lake_candidate) if lake_candidate and lake_candidate.exists() else "lake",
        )
        server = LeanServer(config)
    except Exception as exc:
        return ProofTrace(
            theorem_stmt=theorem, initial_goal="", error=f"LeanREPL 启动失败: {exc}"
        )

    try:
        res = server.run(Command(cmd=sorry_stmt))
        if not hasattr(res, "sorries") or not res.sorries:
            err = getattr(res, "error", None) or "无法获取证明状态（定理可能不可证明？）"
            return ProofTrace(theorem_stmt=theorem, initial_goal="", error=str(err))

        s = res.sorries[0]
        state = s.proof_state
        initial_goal = s.goal

        trace = ProofTrace(theorem_stmt=theorem, initial_goal=initial_goal)

        for tactic in tactics:
            before = trace.steps[-1].after if trace.steps else initial_goal
            r = server.run(ProofStep(proof_state=state, tactic=tactic))
            # 错误 tactic 返回 LeanError（带 .message），成功返回 ProofStepResponse（带 .goals）
            if type(r).__name__ == "LeanError" or hasattr(r, "message"):
                trace.steps.append(
                    StateStep(tactic=tactic, before=before, after=before, is_error=True)
                )
                trace.error = str(getattr(r, "message", r))
                break
            goals = getattr(r, "goals", None) or []
            after = goals[0] if goals else None
            trace.steps.append(
                StateStep(tactic=tactic, before=before, after=after, is_error=False)
            )
            state = getattr(r, "proof_state", state)
            if not goals:
                break  # 证明完成

        return trace
    except Exception as exc:
        return ProofTrace(
            theorem_stmt=theorem, initial_goal="", error=f"状态提取失败: {exc}"
        )
    finally:
        try:
            server.kill()
        except Exception:
            pass
