"""Lean 4 错误分类器。

Lean 4 通过 LSP 返回的诊断信息（Diagnostic）包含：
- message: 错误文本（通常含多行，如 "type mismatch ..."）
- range: 出错位置
- severity: 错误/警告/信息

这里的目标：把 message 文本分类到有限的错误类别，供规则模板匹配。
分类是"宽容匹配"——用关键词优先级排序，宁可归到"其他"也不误分类。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ErrorCategory(str, Enum):
    """Lean 4 高频错误类别。"""

    TYPE_MISMATCH = "type_mismatch"          # 类型不匹配
    UNKNOWN_IDENTIFIER = "unknown_identifier"  # 未知标识符
    UNSOLVED_GOALS = "unsolved_goals"        # 存在未解决目标
    NO_GOALS = "no_goals"                    # 没有需要解决的目标（多写了证明）
    FAILED_TO_SYNTHESIZE = "failed_to_synthesize"  # 类型类合成失败
    UNEXPECTED_TOKEN = "unexpected_token"    # 语法错误
    INVALID_FIELD = "invalid_field"          # 字段记号无效
    FUNCTION_EXPECTED = "function_expected"  # 期望函数
    MOTIVE_NOT_CORRECT = "motive_not_correct"  # motive 类型不正确（match/rec 相关）
    RECURSIVE_FAILED = "recursive_failed"    # 递归定义不通过终止性检查
    UNUSED_VARIABLE = "unused_variable"      # 未使用变量（警告）
    DECLARATION_USES_SORRY = "uses_sorry"    # 使用了 sorry
    MISSING_IMPORT = "missing_import"        # 缺失导入
    SYNTAX_ERROR = "syntax_error"            # 语法错误（通用）
    INVALID_TARGET = "invalid_target"        # motive/归纳目标无效（依赖类型疑难）
    CALC_ERROR = "calc_error"                # calc 块错误
    UNKNOWN = "unknown"                      # 未识别


@dataclass
class ErrorInfo:
    """一次错误诊断的解析结果。"""

    category: ErrorCategory
    message: str                       # 原始报错文本
    code: Optional[str] = None         # 出错代码片段（若有）
    matched_keyword: Optional[str] = None  # 命中的关键词
    hints: list[str] = field(default_factory=list)  # 从报错中提取的附加线索


# Lean 4 LSP 诊断中的结构化 error code（比文本匹配更可靠）。
# 例：error(lean.unknownIdentifier): Unknown identifier `bar`
_ERROR_CODES: dict[str, ErrorCategory] = {
    "lean.unknownIdentifier": ErrorCategory.UNKNOWN_IDENTIFIER,
    "lean.unknownConstant": ErrorCategory.UNKNOWN_IDENTIFIER,
    "lean.invalidField": ErrorCategory.INVALID_FIELD,
    "lean.synthInstanceFailed": ErrorCategory.FAILED_TO_SYNTHESIZE,
    "lean.invalidMotive": ErrorCategory.MOTIVE_NOT_CORRECT,
    "lean.unknownDeclaration": ErrorCategory.UNKNOWN_IDENTIFIER,
    "lean.unusedVariables": ErrorCategory.UNUSED_VARIABLE,
}

# 分类规则：按 (优先级, 正则/子串, 类别) 排列。越靠前越优先。
# 注意顺序很关键：某些子串互相包含（如 "function expected" 里也有 "expected"）。
_RULES: list[tuple[str, ErrorCategory]] = [
    # 期望函数（真实格式："Function expected at foo\nbut this term has type Nat"。
    #   注意："but this term has type" 含 "has type" 会撞上 type mismatch，
    #   所以 "function expected" 必须排在 "has type" 之前）
    ("function expected", ErrorCategory.FUNCTION_EXPECTED),
    ("not a function", ErrorCategory.FUNCTION_EXPECTED),
    # 类型不匹配 —— 最常见的 Lean 报错（Lean 4.32 真实格式：
    #   "Type mismatch\n  n\nhas type\n  Nat\nbut is expected to have type\n  String"）
    ("type mismatch", ErrorCategory.TYPE_MISMATCH),
    ("has type", ErrorCategory.TYPE_MISMATCH),
    ("but is expected to have type", ErrorCategory.TYPE_MISMATCH),
    ("expected type", ErrorCategory.TYPE_MISMATCH),
    ("is not definitionally equal to", ErrorCategory.TYPE_MISMATCH),
    ("of sort", ErrorCategory.TYPE_MISMATCH),
    # motive/归纳目标无效（难：induction 时索引出现多次）
    ("invalid target", ErrorCategory.INVALID_TARGET),
    ("occurs more than once", ErrorCategory.INVALID_TARGET),
    # calc 专用（必须先于通用 type mismatch / unsolved goals）
    ("invalid 'calc' step", ErrorCategory.CALC_ERROR),
    ("invalid calc", ErrorCategory.CALC_ERROR),
    ("calc step", ErrorCategory.CALC_ERROR),
    # 未知标识符（Lean 4.32："Unknown identifier `bar`"）
    ("unknown identifier", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown constant", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown declaration", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown namespace", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown module prefix", ErrorCategory.MISSING_IMPORT),
    # 未解决目标
    ("unsolved goals", ErrorCategory.UNSOLVED_GOALS),
    ("remaining goals", ErrorCategory.UNSOLVED_GOALS),
    # 没有目标（证明写多了）
    ("no goals to be solved", ErrorCategory.NO_GOALS),
    ("no goals to be solved", ErrorCategory.NO_GOALS),
    ("tactic failed, there are no goals", ErrorCategory.NO_GOALS),
    ("unexpected end of proof", ErrorCategory.NO_GOALS),
    # Tactic 失败（真实格式："Tactic `rfl` failed: ..."、
    #   "Tactic `constructor` failed: no applicable constructor found"）
    ("tactic `rfl` failed", ErrorCategory.TYPE_MISMATCH),
    ("tactic `constructor` failed", ErrorCategory.TYPE_MISMATCH),
    ("tactic `exact` failed", ErrorCategory.TYPE_MISMATCH),
    ("tactic `apply` failed", ErrorCategory.TYPE_MISMATCH),
    ("tactic failed", ErrorCategory.TYPE_MISMATCH),
    # 类型类合成失败
    ("failed to synthesize", ErrorCategory.FAILED_TO_SYNTHESIZE),
    ("no instances", ErrorCategory.FAILED_TO_SYNTHESIZE),
    ("could not synthesize", ErrorCategory.FAILED_TO_SYNTHESIZE),
    # motive 不正确
    ("motive is not type correct", ErrorCategory.MOTIVE_NOT_CORRECT),
    ("motive is not", ErrorCategory.MOTIVE_NOT_CORRECT),
    ("invalid 'match' expression, expected type is not known", ErrorCategory.MOTIVE_NOT_CORRECT),
    # 递归定义失败（真实格式："fail to show termination for ...\nfailed to infer structural recursion:"）
    ("fail to show termination", ErrorCategory.RECURSIVE_FAILED),
    ("failed to infer structural recursion", ErrorCategory.RECURSIVE_FAILED),
    ("failed to compile recursive definition", ErrorCategory.RECURSIVE_FAILED),
    ("decreasing recursion", ErrorCategory.RECURSIVE_FAILED),
    ("recursive definition failed", ErrorCategory.RECURSIVE_FAILED),
    ("unexpected occurrence of recursive", ErrorCategory.RECURSIVE_FAILED),
    ("cannot define a recursive function", ErrorCategory.RECURSIVE_FAILED),
    # 字段记号无效（真实格式："Invalid field `z`: ..."）
    ("invalid field", ErrorCategory.INVALID_FIELD),
    ("invalid field notation", ErrorCategory.INVALID_FIELD),
    ("unknown field", ErrorCategory.INVALID_FIELD),
    # 语法/解析错误
    ("unexpected token", ErrorCategory.UNEXPECTED_TOKEN),
    ("unexpected end of input", ErrorCategory.SYNTAX_ERROR),
    ("unexpected symbol", ErrorCategory.UNEXPECTED_TOKEN),
    ("expected", ErrorCategory.SYNTAX_ERROR),  # 通用兜底，放最后
    # 未使用变量（警告类，真实格式："Variable name `a` is not explicitly referenced."）
    ("unused variable", ErrorCategory.UNUSED_VARIABLE),
    ("not explicitly referenced", ErrorCategory.UNUSED_VARIABLE),
    ("declaration uses 'sorry'", ErrorCategory.DECLARATION_USES_SORRY),
    ("declaration uses `sorry`", ErrorCategory.DECLARATION_USES_SORRY),
    # 缺失导入
    ("unknown module", ErrorCategory.MISSING_IMPORT),
    ("failed to import", ErrorCategory.MISSING_IMPORT),
]


def classify_error(message: str) -> ErrorInfo:
    """把一条 Lean 报错文本分类到最匹配的错误类别。

    Args:
        message: Lean LSP 诊断的 message 字段（可能多行）。

    Returns:
        ErrorInfo：分类结果。
    """
    # 归一化：统一大小写、压缩空白，便于子串匹配
    norm = re.sub(r"\s+", " ", message).strip()
    lowered = norm.lower()

    # 第一优先：结构化 error code（error(lean.xxx)）
    code_match = re.search(r"error\(lean\.([a-zA-Z]+)\)", message)
    if code_match:
        code = f"lean.{code_match.group(1)}"
        if code in _ERROR_CODES:
            return ErrorInfo(
                category=_ERROR_CODES[code],
                message=message,
                matched_keyword=code,
            )

    for keyword, category in _RULES:
        if keyword in lowered:
            return ErrorInfo(
                category=category,
                message=message,
                matched_keyword=keyword,
            )

    return ErrorInfo(category=ErrorCategory.UNKNOWN, message=message)
