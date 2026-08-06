"""Lean 错误中文解释模板库。

每个错误类别对应一个模板：
- title: 中文标题
- what: 这个错误是什么意思（通俗解释）
- why: 常见原因
- fix: 修复建议（可能多条）
- example: 常见错误写法 → 正确写法（尽量给出）

模板里支持 {code} 占位符（出错代码片段，可选）。
"""

from __future__ import annotations

from typing import Any

from .classify import ErrorCategory


# fmt: off
TEMPLATES: dict[ErrorCategory, dict[str, Any]] = {
    ErrorCategory.TYPE_MISMATCH: {
        "title": "类型不匹配（type mismatch）",
        "what": (
            "Lean 是强类型系统，它发现你写的一个表达式，其类型和它期望的类型对不上。"
            "简单说：你给了一个 A 类型的东西，但这里需要 B 类型。"
        ),
        "why": [
            "把不同类型的值混用了，比如把 Nat 当 String 用",
            "变量/函数用错了，比如想用加法却用了字符串拼接",
            "依赖类型场景下，某一步算出来的类型和声明不一致",
        ],
        "fix": [
            "看报错里的两行：`has type`（你给的实际类型）和 `but is expected to have type`（期望类型），确认它们为什么不同",
            "检查是否忘了转换（如 Nat → Int 需要显式转换）",
            "如果涉及类型族/依赖类型，检查参数顺序是否对",
        ],
        "example": (
            "错误：把 `a + b`（Nat）当成了 String 使用。\n"
            "修复：确保 `a`、`b` 的类型符合运算要求，或改用正确的类型。"
        ),
    },

    ErrorCategory.UNKNOWN_IDENTIFIER: {
        "title": "未知标识符（unknown identifier）",
        "what": (
            "Lean 找不到你写的这个名字——它不在当前作用域里。"
            "可能是拼写错误、没导入、没定义，或者变量在作用域外被使用了。"
        ),
        "why": [
            "名字拼错了（大小写、下划线）",
            "忘了 `import` 对应的模块",
            "引用了不在当前作用域里的变量（比如出了 `by` 块、`have` 块）",
            "定义还没写，或者写在了使用它的地方之后",
        ],
        "fix": [
            "检查拼写和大小写",
            "如果来自 mathlib，确认是否 `import Mathlib.*`",
            "如果来自局部定义，把它移进作用域（或移出 `by` 块）",
            "用 IDE 的自动补全确认名字真实存在",
        ],
    },

    ErrorCategory.UNSOLVED_GOALS: {
        "title": "存在未解决的目标（unsolved goals）",
        "what": (
            "你写完证明后，Lean 发现还有证明目标没有完成。"
            "也就是说：你的证明不完整，有些该证明的命题还悬着。"
        ),
        "why": [
            "证明写到一半就结束了，漏掉了某些子目标",
            "某一步用了 `·` 但没补全所有分支",
            "最后一个 tactic 没有完全解决目标",
        ],
        "fix": [
            "看报错列出的剩余目标（`⊢ ...`），逐个补全",
            "如果剩余目标是 trivial 的，加 `simp` / `omega` / `aesop` 收尾",
            "检查 `·` 缩进块是否每个都闭合",
        ],
    },

    ErrorCategory.NO_GOALS: {
        "title": "没有需要解决的目标（no goals to be solved）",
        "what": (
            "证明已经完成了，但你还在继续写证明步骤。"
            "Lean 会提示：已经没有目标需要解决了，多余的命令会被拒绝。"
        ),
        "why": [
            "在 `by ...` 块末尾多写了 tactic",
            "一个定理里写了两个 `by`",
            "`have` / `let` 之后目标已被解决，又追加了步骤",
        ],
        "fix": [
            "删掉多余的最后一步",
            "如果两个 `by` 相邻，合并成一个",
        ],
    },

    ErrorCategory.FAILED_TO_SYNTHESIZE: {
        "title": "类型类合成失败（failed to synthesize）",
        "what": (
            "Lean 试图自动搜索某个类型类（typeclass）实例，但没找到。"
            "常见于 `OfNat`、`HMul`、`Decidable`、`Add` 等自动推导的场景。"
        ),
        "why": [
            "缺了某个类型类实例（instance）",
            "类型是自定义的，还没注册对应的运算实例",
            "参数类型不满足实例的前置条件",
        ],
        "fix": [
            "看报错提示需要哪个 typeclass（如 `OfNat ... 2`），找到缺的实例",
            "为自定义类型补上 `instance`",
            "有时加上 `import Mathlib.Data...` 就有了现成实例",
        ],
    },

    ErrorCategory.MOTIVE_NOT_CORRECT: {
        "title": "motive 类型不正确（motive is not type correct）",
        "what": (
            "这是 `match` / `induction` / 递归消解中最容易让人懵的错误。"
            "motive（动机）是你要证明/构造的命题模式，Lean 要求它对所有构造子分支都成立。"
            "报这个错通常意味着 motive 的写法有类型错误，或依赖参数处理不对。"
        ),
        "why": [
            "`match` 的分支返回类型不一致",
            "motive 里依赖的索引参数（indexed type）写错了",
            "在依赖模式匹配时，某分支用了错误的变量",
        ],
        "fix": [
            "确保所有 `match` 分支返回同一类型",
            "如果处理索引类型（如 `Vec α n`），motive 需要包含索引变量",
            "试试先用 `induction` 而不是手写 `match`，Lean 会自动生成正确的 motive",
        ],
    },

    ErrorCategory.RECURSIVE_FAILED: {
        "title": "递归定义未通过检查（recursive definition failed）",
        "what": (
            "Lean 的终止性检查器认为这个递归不会终止，或结构递归没有在参数上递减。"
            "Lean 要求递归调用必须发生在某个参数的结构更小处（structural recursion）。"
        ),
        "why": [
            "递归调用的参数没有变小（如 `f n := f (n+1)`）",
            "递归发生在非结构位置（如被传入其他函数内部）",
            "多个参数递归时，没有指明哪个参数在递减",
        ],
        "fix": [
            "让递归调用作用在更小的参数上（`n-1`、`xs.tail` 等）",
            "用 `termination_by` 显式声明递减的量",
            "必要时改用 `decreasing_by` 提供证明",
        ],
    },

    ErrorCategory.INVALID_FIELD: {
        "title": "字段记号无效（invalid field notation）",
        "what": (
            "你用了点号字段访问（如 `x.field`），但该类型上没有这个字段，"
            "或者 Lean 无法从这个表达式的类型推断出结构体。"
        ),
        "why": [
            "字段名拼错或不存在",
            "访问字段的对象类型不明确（Lean 无法推断）",
            "对象不是结构体类型",
        ],
        "fix": [
            "检查字段名是否正确（在 IDE 中 `x.` 会自动补全）",
            "给对象加上显式类型标注帮助推断",
            "确认访问的确实是结构体/类型类字段",
        ],
    },

    ErrorCategory.FUNCTION_EXPECTED: {
        "title": "期望函数（function expected）",
        "what": (
            "你把一个不是函数的值当成函数调用了（后面跟了参数）。"
            "Lean 说：这里期望一个函数，但你给的不是。"
        ),
        "why": [
            "变量名写错，把普通值当成函数名",
            "函数需要先应用部分参数",
            "高阶函数参数类型写错",
        ],
        "fix": [
            "检查被调用的名字是不是真的函数",
            "确认参数个数和类型",
        ],
    },

    ErrorCategory.UNEXPECTED_TOKEN: {
        "title": "意外记号（unexpected token）",
        "what": (
            "解析器在一个它没预料到的位置遇到了这个符号——通常是语法错误，"
            "比如括号没闭合、符号写错、`by` 放错位置。"
        ),
        "why": [
            "括号/引号不配对",
            "写了 Lean 不认识的符号",
            "关键字拼错（如 `theroem` → `theorem`）",
        ],
        "fix": [
            "检查出错位置的括号配对",
            "看是不是把 `:=` 写成 `=`，或漏了 `:`",
            "对照 IDE 的语法高亮定位第一个变红的位置",
        ],
    },

    ErrorCategory.SYNTAX_ERROR: {
        "title": "语法错误（syntax error）",
        "what": "Lean 的解析器没能理解这段代码的语法结构。",
        "why": [
            "声明语句不完整（缺 `:=` / `:` / 冒号）",
            "符号或关键字写错",
            "结构体/项式写法有误",
        ],
        "fix": [
            "从出错位置往前找最近的不完整语句",
            "参考同类型的正确写法（IDE 示例或文档）",
        ],
    },

    ErrorCategory.UNUSED_VARIABLE: {
        "title": "未使用变量（unused variable）",
        "what": "（警告）你引入了一个变量，但证明/代码中从未使用它。",
        "why": ["多余的假设或变量", "想用但写错了名字"],
        "fix": ["删掉它，或确认是否想用 `_` 占位"],
    },

    ErrorCategory.DECLARATION_USES_SORRY: {
        "title": "声明使用了 sorry",
        "what": "（警告）这个定理用 `sorry` / `admit` 占位，意味着它其实没有被真正证明。",
        "why": ["调试时的临时占位，忘了补全"],
        "fix": ["用真实的证明替换 `sorry`", "提交前用 `grep sorry` 检查全仓库"],
    },

    ErrorCategory.MISSING_IMPORT: {
        "title": "缺失导入（missing import / unknown module）",
        "what": "你要导入的模块不存在，或路径写错。",
        "why": ["模块名拼写错误", "该模块在 mathlib 里的路径不对", "依赖没有拉取（lake 未更新）"],
        "fix": ["确认模块真实路径（IDE 跳转验证）", "`lake update` / `lake build` 拉取依赖"],
    },

    ErrorCategory.UNKNOWN: {
        "title": "未能识别的错误",
        "what": (
            "规则库还没收录这类报错。"
            "如果它经常出现，欢迎到仓库提 issue，我们会补充模板。"
        ),
        "why": [],
        "fix": ["也可以手动打开 LLM 兜底模式（见 README）"],
    },
}
# fmt: on


def render(category: ErrorCategory, code: str | None = None) -> dict[str, Any]:
    """渲染某个类别的中文解释（含可选代码片段）。"""
    t = TEMPLATES.get(category, TEMPLATES[ErrorCategory.UNKNOWN])
    text = {
        "title": t["title"],
        "what": t["what"],
        "why": t["why"],
        "fix": t["fix"],
        "example": t.get("example"),
    }
    if code and "{code}" in text["what"]:
        text["what"] = text["what"].replace("{code}", code)
    return text
