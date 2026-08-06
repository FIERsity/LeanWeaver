"""错误分类器测试。"""

from leanweaver.errors.classify import ErrorCategory, classify_error


def test_type_mismatch():
    msg = """type mismatch
  term
    a + b
  has type
    Nat
  but is expected to have type
    String"""
    info = classify_error(msg)
    assert info.category is ErrorCategory.TYPE_MISMATCH


def test_unknown_identifier():
    info = classify_error("unknown identifier 'foo'")
    assert info.category is ErrorCategory.UNKNOWN_IDENTIFIER


def test_unsolved_goals():
    info = classify_error(
        "unsolved goals\na b : Nat\n⊢ a + b = b + a"
    )
    assert info.category is ErrorCategory.UNSOLVED_GOALS


def test_no_goals():
    info = classify_error("no goals to be solved")
    assert info.category is ErrorCategory.NO_GOALS


def test_failed_to_synthesize():
    info = classify_error(
        "failed to synthesize instance OfNat String 2"
    )
    assert info.category is ErrorCategory.FAILED_TO_SYNTHESIZE


def test_motive():
    info = classify_error(
        "motive is not type correct\n  α : Type\n  motive: α → Sort u_1"
    )
    assert info.category is ErrorCategory.MOTIVE_NOT_CORRECT


def test_recursive():
    info = classify_error("failed to compile recursive definition")
    assert info.category is ErrorCategory.RECURSIVE_FAILED


def test_invalid_field():
    info = classify_error("invalid field notation, 'x' does not have field 'foo'")
    assert info.category is ErrorCategory.INVALID_FIELD


def test_unknown_falls_through():
    info = classify_error("some exotic new error message we haven't seen")
    assert info.category is ErrorCategory.UNKNOWN
