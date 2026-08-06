"""Lean 文件诊断分析测试。

需要本机有 lean（elan 安装）。没有 lean 时这些测试会被跳过。
"""

import shutil

import pytest

from leanweaver.check import (
    LeanDiagnostic,
    check_text,
    find_lean,
    parse_diagnostic,
)


HAVE_LEAN = shutil.which("lean") is not None or (
    __import__("pathlib").Path.home() / ".elan" / "bin" / "lean"
).exists()


@pytest.mark.skipif(not HAVE_LEAN, reason="lean 未安装")
def test_check_text_with_error():
    result = check_text(
        "structure Point where\n  x : Nat\n  y : Nat\n\ndef getZ (p : Point) : Nat := p.z\n"
    )
    assert result.error_count >= 1
    # 找到 invalid field 的诊断
    kinds = [d.kind for d in result.diagnostics]
    assert any("invalidField" in k for k in kinds)


@pytest.mark.skipif(not HAVE_LEAN, reason="lean 未安装")
def test_check_text_clean_file():
    result = check_text("theorem t : 1 = 1 := by\n  rfl\n")
    assert result.error_count == 0


def test_parse_diagnostic():
    raw = {
        "severity": "error",
        "data": "Unknown identifier `bar`",
        "kind": "lean.unknownIdentifier._namedError",
        "fileName": "test.lean",
        "pos": {"line": 2, "column": 8},
        "endPos": {"line": 2, "column": 11},
    }
    diag = parse_diagnostic(raw)
    assert diag.severity == "error"
    assert diag.line == 2
    assert diag.column == 8
    assert diag.kind == "lean.unknownIdentifier._namedError"
    assert "unknownIdentifier" in diag.kind
    assert "bar" in str(diag)
