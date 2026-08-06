"""解释器端到端测试。"""

from leanweaver.errors import explain
from leanweaver.errors.classify import ErrorCategory


def test_explain_type_mismatch():
    result = explain("type mismatch\n  term\n    a + b\n  has type\n    Nat\n  but is expected to have type\n    String")
    assert result.category is ErrorCategory.TYPE_MISMATCH
    assert "类型不匹配" in result.title
    assert len(result.fix) > 0
    assert result.pretty()  # 可渲染


def test_explain_unknown_without_llm():
    # 未识别错误：默认不走 LLM，返回"未能识别"
    result = explain("some brand new exotic error")
    assert result.category is ErrorCategory.UNKNOWN
    assert not result.used_llm
    assert "未能识别" in result.title


def test_explain_with_code_hint():
    result = explain(
        "unknown identifier 'foo'",
        code="theorem t : 1 = 1 := by\n  exact foo",
    )
    assert result.category is ErrorCategory.UNKNOWN_IDENTIFIER
    assert result.pretty()
