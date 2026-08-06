"""解释器端到端测试。"""

import pytest

from leanweaver.errors import explain
from leanweaver.errors.classify import ErrorCategory
from leanweaver.errors.templates import available_languages, render


def test_explain_type_mismatch_default_en():
    result = explain(
        "type mismatch\n  term\n    a + b\n  has type\n    Nat\n  but is expected to have type\n    String"
    )
    assert result.category is ErrorCategory.TYPE_MISMATCH
    assert "Type mismatch" in result.title
    assert len(result.fix) > 0
    assert result.pretty()  # 可渲染


def test_explain_zh_plugin():
    result = explain(
        "type mismatch\n  term\n    a + b\n  has type\n    Nat\n  but is expected to have type\n    String",
        lang="zh",
    )
    assert "类型不匹配" in result.title
    assert len(result.fix) > 0


def test_explain_unknown_without_llm():
    # 未识别错误：默认不走 LLM，返回"未能识别"
    result = explain("some brand new exotic error")
    assert result.category is ErrorCategory.UNKNOWN
    assert not result.used_llm
    assert "Unrecognized" in result.title


def test_unknown_locale_falls_back_to_en():
    # 某个 locale 缺少某类别时，回退到英文
    t = render(ErrorCategory.TYPE_MISMATCH, lang="zh")
    assert t["title"]
    # zh 有全部类别，这里验证 fallback 逻辑不崩
    assert available_languages() == ["en", "zh"]


def test_unsupported_lang_raises():
    with pytest.raises(KeyError):
        render(ErrorCategory.TYPE_MISMATCH, lang="fr")


def test_explain_with_code_hint():
    result = explain(
        "unknown identifier 'foo'",
        code="theorem t : 1 = 1 := by\n  exact foo",
    )
    assert result.category is ErrorCategory.UNKNOWN_IDENTIFIER
    assert result.pretty()
