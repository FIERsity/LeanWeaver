"""LeanREPL 状态提取测试（需要本机 lean + lean-interact）。"""

import shutil

import pytest

from leanweaver.translate.state import extract_state_trace, StateStep

HAVE_LEAN = shutil.which("lean") is not None or (
    __import__("pathlib").Path.home() / ".elan" / "bin" / "lean"
).exists()

try:
    import lean_interact  # noqa: F401

    HAVE_INTERACT = True
except ImportError:
    HAVE_INTERACT = False

HAVE_ENV = HAVE_LEAN and HAVE_INTERACT


def _with_retry(fn, attempts: int = 3):
    """LeanREPL 启动偶发竞争（并行测试时），加重试稳定测试。"""
    import time

    last = None
    for _ in range(attempts):
        try:
            return fn()
        except AssertionError as exc:
            last = exc
            time.sleep(1.5)
    raise last


@pytest.mark.skipif(not HAVE_ENV, reason="需要 lean + lean-interact")
def test_multi_step_trace():
    def _run():
        trace = extract_state_trace(
            "theorem t1 (P Q R : Prop) (h1 : P → Q) (h2 : Q → R) (hp : P) : R",
            ["apply h2", "apply h1", "exact hp"],
        )
        assert trace.completed
        assert len(trace.steps) == 3
        assert trace.steps[0].tactic == "apply h2"
        assert "R" in trace.initial_goal
        assert trace.steps[0].before
        assert trace.steps[0].after
        assert "⊢ Q" in trace.steps[0].after
        return trace

    _with_retry(_run)


@pytest.mark.skipif(not HAVE_ENV, reason="需要 lean + lean-interact")
def test_rw_trace():
    def _run():
        trace = extract_state_trace(
            "theorem t2 (a b : Nat) : a + b = b + a",
            ["rw [Nat.add_comm]"],
        )
        assert trace.completed
        assert len(trace.steps) == 1
        return trace

    _with_retry(_run)


@pytest.mark.skipif(not HAVE_ENV, reason="需要 lean + lean-interact")
def test_error_step():
    def _run():
        trace = extract_state_trace(
            "theorem t3 (P Q : Prop) (h : P) : Q",
            ["exact h"],
        )
        # exact h 无法证明 Q → 应记录错误步骤
        assert trace.steps
        assert trace.steps[-1].is_error or not trace.completed
        return trace

    _with_retry(_run)
