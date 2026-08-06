"""下一步建议测试（含验证层）。"""

import shutil

import pytest

from leanweaver.translate.llm import LLMBackend
from leanweaver.translate.suggest import parse_candidates, suggest_next

HAVE_LEAN = shutil.which("lean") is not None or (
    __import__("pathlib").Path.home() / ".elan" / "bin" / "lean"
).exists()

try:
    import lean_interact  # noqa: F401

    HAVE_INTERACT = True
except ImportError:
    HAVE_INTERACT = False

HAVE_ENV = HAVE_LEAN and HAVE_INTERACT


class MockLLM(LLMBackend):
    """返回固定候选的 mock。"""

    def complete(self, system, user, **kw):
        # 3 个候选：exact hp（能完成）、apply h（能推进）、bad_tactic（无效）
        return (
            '[{"tactic": "exact hp", "reason": "直接匹配"}, '
            '{"tactic": "apply h", "reason": "应用蕴含"}, '
            '{"tactic": "bad_tactic_xyz", "reason": "无效"}]'
        )

    def explain_error(self, message, code=None, lang="en"):
        return ""

    def translate_proof(self, lean_proof, target_lang="zh"):
        return ""


def test_parse_candidates_json():
    text = '[{"tactic": "exact h", "reason": "a"}, {"tactic": "apply h", "reason": "b"}]'
    cands = parse_candidates(text)
    assert len(cands) == 2
    assert cands[0]["tactic"] == "exact h"


def test_parse_candidates_line_by_line():
    text = "exact h\napply h2\nconstructor"
    cands = parse_candidates(text)
    assert len(cands) >= 3


@pytest.mark.skipif(not HAVE_ENV, reason="需要 lean + lean-interact")
def test_suggest_verified():
    """验证层：只保留能推进的候选，丢弃无效的。"""
    llm = MockLLM()
    result = suggest_next(
        "theorem t1 (P Q R : Prop) (h : P → Q) (h2 : Q → R) (hp : P) : R",
        ["apply h2"],
        num_candidates=3,
        llm=llm,
        verify=True,
    )
    assert result["error"] is None, result["error"]
    assert "state" in result and result["state"]
    # 验证后的建议
    tactics = [s.tactic for s in result["suggestions"]]
    # apply h2 后目标是 Q，apply h 能推进 Q→P，应被保留
    assert "apply h" in tactics, f"有效推进候选应被保留: {tactics}"
    # 无效的 bad_tactic 应该被验证层丢弃
    assert "bad_tactic_xyz" not in tactics, f"无效候选应被丢弃: {tactics}"
    # 所有建议必须通过验证
    assert all(s.verified for s in result["suggestions"]), "所有建议都应经过验证"


@pytest.mark.skipif(not HAVE_ENV, reason="需要 lean + lean-interact")
def test_suggest_completed_proof():
    """证明已完成时返回提示。"""
    llm = MockLLM()
    result = suggest_next(
        "theorem t2 (a b : Nat) : a + b = b + a",
        ["rw [Nat.add_comm]"],
        llm=llm,
        verify=True,
    )
    assert result["error"] and "已完成" in result["error"]
