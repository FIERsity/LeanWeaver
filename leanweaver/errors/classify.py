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
    UNKNOWN = "unknown"                      # 未识别


@dataclass
class ErrorInfo:
    """一次错误诊断的解析结果。"""

    category: ErrorCategory
    message: str                       # 原始报错文本
    code: Optional[str] = None         # 出错代码片段（若有）
    matched_keyword: Optional[str] = None  # 命中的关键词
    hints: list[str] = field(default_factory=list)  # 从报错中提取的附加线索


# 分类规则：按 (优先级, 正则/子串, 类别) 排列。越靠前越优先。
# 注意顺序很关键：某些子串互相包含（如 "function expected" 里也有 "expected"）。
_RULES: list[tuple[str, ErrorCategory]] = [
    # 类型不匹配 —— 最常见的 Lean 报错
    ("type mismatch", ErrorCategory.TYPE_MISMATCH),
    ("has type", ErrorCategory.TYPE_MISMATCH),
    ("but is expected to have type", ErrorCategory.TYPE_MISMATCH),
    ("expected type", ErrorCategory.TYPE_MISMATCH),
    # 未知标识符
    ("unknown identifier", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown constant", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown declaration", ErrorCategory.UNKNOWN_IDENTIFIER),
    ("unknown namespace", ErrorCategory.UNKNOWN_IDENTIFIER),
    # 未解决目标
    ("unsolved goals", ErrorCategory.UNSOLVED_GOALS),
    ("remaining goals", ErrorCategory.UNSOLVED_GOALS),
    # 没有目标（证明写多了）
    ("no goals to be solved", ErrorCategory.NO_GOALS),
    ("tactic failed, there are no goals", ErrorCategory.NO_GOALS),
    ("unexpected end of proof", ErrorCategory.NO_GOALS),
    # 类型类合成失败
    ("failed to synthesize", ErrorCategory.FAILED_TO_SYNTHESIZE),
    ("no instances", ErrorCategory.FAILED_TO_SYNTHESIZE),
    ("could not synthesize", ErrorCategory.FAILED_TO_SYNTHESIZE),
    # motive 不正确
    ("motive is not type correct", ErrorCategory.MOTIVE_NOT_CORRECT),
    ("motive is not", ErrorCategory.MOTIVE_NOT_CORRECT),
    ("invalid 'match' expression, expected type is not known", ErrorCategory.MOTIVE_NOT_CORRECT),
    # 递归定义失败
    ("failed to compile recursive definition", ErrorCategory.RECURSIVE_FAILED),
    ("decreasing recursion", ErrorCategory.RECURSIVE_FAILED),
    ("recursive definition failed", ErrorCategory.RECURSIVE_FAILED),
    ("unexpected occurrence of recursive", ErrorCategory.RECURSIVE_FAILED),
    ("cannot define a recursive function", ErrorCategory.RECURSIVE_FAILED),
    # 字段记号无效
    ("invalid field notation", ErrorCategory.INVALID_FIELD),
    ("unknown field", ErrorCategory.INVALID_FIELD),
    # 期望函数
    ("function expected", ErrorCategory.FUNCTION_EXPECTED),
    ("not a function", ErrorCategory.FUNCTION_EXPECTED),
    # 语法/解析错误
    ("unexpected token", ErrorCategory.UNEXPECTED_TOKEN),
    ("unexpected end of input", ErrorCategory.SYNTAX_ERROR),
    ("unexpected symbol", ErrorCategory.UNEXPECTED_TOKEN),
    ("expected", ErrorCategory.SYNTAX_ERROR),  # 通用兜底，放最后
    # 未使用变量（警告类）
    ("unused variable", ErrorCategory.UNUSED_VARIABLE),
    ("declaration uses 'sorry'", ErrorCategory.DECLARATION_USES_SORRY),
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

    for keyword, category in _RULES:
        if keyword in lowered:
            return ErrorInfo(
                category=category,
                message=message,
                matched_keyword=keyword,
            )

    return ErrorInfo(category=ErrorCategory.UNKNOWN, message=message)
