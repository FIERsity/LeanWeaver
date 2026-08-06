"""证明提取器测试。"""

from leanweaver.translate.parser import extract_proof, extract_proofs


SAMPLE = """\
import Mathlib

theorem add_comm_sample (a b : Nat) : a + b = b + a := by
  rw [Nat.add_comm]

lemma two_plus_two : 2 + 2 = 4 := by
  norm_num

example (P : Prop) (h : P) : P := by
  exact h

def square (n : Nat) : Nat := n * n
"""


def test_extract_proofs_finds_all():
    blocks = extract_proofs(SAMPLE)
    names = [b.theorem_name for b in blocks]
    assert "add_comm_sample" in names
    assert "two_plus_two" in names


def test_extract_by_name():
    block = extract_proof(SAMPLE, "add_comm_sample")
    assert block is not None
    assert block.theorem_name == "add_comm_sample"
    assert block.tactics  # 有 tactic
    assert any("rw" in t for t in block.tactics)


def test_extract_first_when_no_name():
    block = extract_proof(SAMPLE)
    assert block is not None
    assert block.theorem_name == "add_comm_sample"


def test_multi_line_tactic():
    src = """\
theorem multi (a b c : Nat) : a + (b + c) = (a + b) + c := by
  rw [Nat.add_assoc]
"""
    block = extract_proof(src)
    assert block is not None
    assert len(block.tactics) >= 1


def test_no_proof_returns_none():
    block = extract_proof("def square (n : Nat) : Nat := n * n", "square")
    # def 没有 by 块，返回 None（或跳过）
    assert block is None or not block.tactics
