"""真实 Lean 4.32 报错样本测试。

这些报错文本来自本机 lean 4.32.2 实际运行生成的输出（见 docs/real-error-samples.md）。
用于验证分类器对真实世界报错的覆盖，而不只是理想化的人工样例。
"""

from leanweaver.errors.classify import ErrorCategory, classify_error


def test_real_type_mismatch():
    # lean: Type mismatch / n has type Nat but is expected to have type String
    msg = """Type mismatch
  n
has type
  Nat
but is expected to have type
  String"""
    assert classify_error(msg).category is ErrorCategory.TYPE_MISMATCH


def test_real_unknown_identifier_with_code():
    # lean: error(lean.unknownIdentifier): Unknown identifier `bar`
    msg = "Unknown identifier `bar`"
    assert classify_error(msg).category is ErrorCategory.UNKNOWN_IDENTIFIER


def test_real_unsolved_goals():
    msg = """unsolved goals
a b c : Nat
⊢ c + (a + b) = c + b + a"""
    assert classify_error(msg).category is ErrorCategory.UNSOLVED_GOALS


def test_real_no_goals():
    msg = "No goals to be solved"
    assert classify_error(msg).category is ErrorCategory.NO_GOALS


def test_real_synth_failed_with_code():
    # lean: error(lean.synthInstanceFailed): failed to synthesize instance of type class HAdd Nat Nat String
    msg = "failed to synthesize instance of type class\n  HAdd Nat Nat String"
    assert classify_error(msg).category is ErrorCategory.FAILED_TO_SYNTHESIZE


def test_real_invalid_field_with_code():
    # lean: error(lean.invalidField): Invalid field `z`
    msg = "Invalid field `z`: The environment does not contain `Point.z`"
    assert classify_error(msg).category is ErrorCategory.INVALID_FIELD


def test_real_function_expected():
    msg = """Function expected at
  foo
but this term has type
  Nat"""
    assert classify_error(msg).category is ErrorCategory.FUNCTION_EXPECTED


def test_real_rfl_failed():
    # Tactic `rfl` failed: The left-hand side 1 is not definitionally equal to 2
    msg = """Tactic `rfl` failed: The left-hand side
  1
is not definitionally equal to the right-hand side
  2"""
    assert classify_error(msg).category is ErrorCategory.TYPE_MISMATCH


def test_real_recursion_failed():
    msg = """fail to show termination for
  bad
with errors
failed to infer structural recursion:"""
    assert classify_error(msg).category is ErrorCategory.RECURSIVE_FAILED


def test_real_missing_import():
    # lean: error: unknown module prefix 'DoesNotExist'
    msg = "unknown module prefix 'DoesNotExist'"
    assert classify_error(msg).category is ErrorCategory.MISSING_IMPORT


def test_real_unused_variable_warning():
    msg = "Variable name `a` is not explicitly referenced."
    info = classify_error(msg)
    assert info.category is ErrorCategory.UNUSED_VARIABLE


def test_real_sorry_warning():
    msg = "declaration uses `sorry`"
    assert classify_error(msg).category is ErrorCategory.DECLARATION_USES_SORRY


def test_real_motive_invalid_with_code():
    # 真实场景中 motive 错误常伴随 error(lean.invalidMotive)
    msg = "error(lean.invalidMotive): invalid motive"
    assert classify_error(msg).category is ErrorCategory.MOTIVE_NOT_CORRECT


def test_hard_invalid_target_motive():
    # 真实难例：induction 时索引出现多次
    msg = "Invalid target: Target (or one of its indices) occurs more than once\n  n"
    info = classify_error(msg)
    assert info.category is ErrorCategory.INVALID_TARGET


def test_hard_calc_error():
    # 真实难例：calc 步类型不匹配
    msg = """invalid 'calc' step, right-hand side is
  n - n : Nat
but is expected to be
  1 : Nat"""
    info = classify_error(msg)
    assert info.category is ErrorCategory.CALC_ERROR


def test_hard_calc_zh_explanation():
    from leanweaver.errors.explain import explain

    result = explain(
        "invalid 'calc' step, right-hand side is\n  n - n : Nat\nbut is expected to be\n  1 : Nat",
        lang="zh",
    )
    assert "calc" in result.title
    assert len(result.fix) > 0
    assert "right-hand side" in result.what or "链条" in result.what


def test_hard_motive_zh_explanation():
    from leanweaver.errors.explain import explain

    result = explain(
        "Invalid target: Target (or one of its indices) occurs more than once\n  n",
        lang="zh",
    )
    assert "归纳" in result.title or "索引" in result.what
    assert len(result.fix) > 0
