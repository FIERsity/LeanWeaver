"""Chinese (zh) templates for Lean error explanations — locale plugin.

Default locale is English (see locales/en.py). This is an optional plugin
enabled by passing lang="zh".
"""

from __future__ import annotations

from typing import Any

from ..classify import ErrorCategory

TEMPLATES_ZH: dict[ErrorCategory, dict[str, Any]] = {
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

    ErrorCategory.NOT_PROPOSITION: {
        "title": "定理结论不是命题（not a proposition）",
        "what": (
            "你声明了一个 `theorem`（或 `lemma`/`example`），但它的结论不是命题。"
            "在 Lean 中，`theorem` 用于证明命题——结论类型必须是 `Prop`"
            "（比如 `P`、`a = b`、`x > 0`），而不是 `Nat`、`String` 这类数据类型。"
            "如果要构造数据类型的值，应该用 `def` 而不是 `theorem`。"
        ),
        "why": [
            "用了 `theorem` 但结论是数据类型（Nat、String、List...）",
            "本应该用 `def`（它可以返回任意类型）而不是 `theorem`",
            "这个声明其实不是数学命题",
        ],
        "fix": [
            "如果想定义函数/值，把 `theorem` 改成 `def`",
            "如果想证明性质，确保结论是 `Prop`（如 `x = 0`、`x > 0`、`P`）",
            "记住：`theorem`/`lemma`/`example` 用于证明；`def` 用于定义",
        ],
    },

    ErrorCategory.INFER_FAILED: {
        "title": "无法推断类型（failed to infer type）",
        "what": (
            "Lean 无法自动确定某物的类型——可能是变量（binder）、`let` 声明、或定义。"
            "它需要足够的类型信息才能判断这个项应该是什么类型。"
        ),
        "why": [
            "变量/binder 没有指定类型，且上下文也无法推断",
            "`let`/定义的类型不明确，Lean 无法判断",
            "能决定类型的信息缺失或不一致",
        ],
        "fix": [
            "加显式类型标注，如 `(x : Nat)`、`let x : Nat := ...`",
            "给定义加类型签名，如 `def foo (n : Nat) : Nat := ...`",
            "如果是在定理里的 binder，在声明里写明它的类型",
        ],
    },

    ErrorCategory.SYNTHESIZE_IMPLICIT: {
        "title": "无法合成隐式参数/占位符（cannot synthesize implicit argument）",
        "what": (
            "Lean 无法推断出某个隐式参数或占位符（`_`）的值。"
            "它知道这个参数必须存在，但无法从周围上下文推导出它应该是什么。"
        ),
        "why": [
            "隐式类型类/类型参数无法从上下文推导",
            "`_` 占位符没有唯一解——可能有多个选项",
            "决定该参数所需的信息还没给出",
        ],
        "fix": [
            "显式提供参数，如 `f (x := value)` 或 `f (α := Nat)`",
            "加类型标注帮助推断",
            "如果是类型类参数，确保所需的 `instance` 存在且在作用域内",
        ],
    },

    ErrorCategory.TACTIC_FAILED: {
        "title": "tactic 执行失败（tactic failed）",
        "what": (
            "你用的 tactic 在这种情形下无法达成目标。"
            "Lean 执行了它，但它失败了——'failed' 后面的信息通常会说明原因"
            "（比如没有匹配的假设、目标不适用）。"
        ),
        "why": [
            "tactic 的前提不满足（如 `exact` 没有匹配的项、`assumption` 没有匹配的假设）",
            "tactic 不适用于当前目标的形式",
            "自定义 tactic 未实现/未定义",
        ],
        "fix": [
            "读报错：这个 tactic 想做什么、在哪一步失败",
            "对 `exact`/`assumption`：确认项/假设真的匹配目标",
            "对自定义 tactic：检查是否已实现并导入",
        ],
    },

    ErrorCategory.ALREADY_DECLARED: {
        "title": "重复声明（already declared）",
        "what": "你试图声明一个在当前作用域里已经存在的名字（定义、定理或字段）。",
        "why": [
            "这个名字之前已经定义过（本文件或导入的模块里）",
            "两个声明重名了",
            "字段/构造子名与已有名字冲突",
        ],
        "fix": [
            "换一个名字",
            "如果是重复定义，删掉早先那个",
            "如果来自导入，可能名字已被占用——改你自己的名字",
        ],
    },

    ErrorCategory.AMBIGUOUS: {
        "title": "歧义（ambiguous term / typeclass instance）",
        "what": "Lean 发现某个东西有不止一种可能的解释（类型或类型类实例），无法决定你指的是哪个。",
        "why": [
            "项的类型有歧义——多个类型都合适",
            "多个类型类实例都同样适用",
            "没有更多信息，Lean 无法选出唯一含义",
        ],
        "fix": [
            "加显式类型标注来消除歧义",
            "对类型类歧义，限制/提供作用域内的实例",
            "检查是否打开了太多 namespace 导致冲突",
        ],
    },

    ErrorCategory.MISSING_ALTERNATIVE: {
        "title": "缺少分支（match 分支未提供）",
        "what": "`match`/`cases`/模式匹配缺少一个未处理的情况——Lean 期望有一个没被提供的分支。",
        "why": [
            "类型的所有构造子/模式没有被完全覆盖",
            "引用了具名分支（如 `isFalse`）但没写出来",
            "match 缺少必需的分支",
        ],
        "fix": [
            "补上缺失的分支（查看类型的构造子）",
            "如果缺具名分支，补上（如 `| isFalse => ...`）",
            "用 `match ... with` 覆盖所有情况，或加兜底 `| _ =>`",
        ],
    },

    ErrorCategory.DEPRECATED: {
        "title": "已废弃（deprecated）",
        "what": "你用的名字已被废弃——它还能用但不推荐，请用建议的替代名。",
        "why": ["API/名字被重命名或取代", "用了旧拼写"],
        "fix": ["用报错建议的替代名（如 'Use `...` instead'）"],
    },

    ErrorCategory.UNUSED: {
        "title": "未使用（unused）",
        "what": "你声明的函数或参数没有被使用。Lean 提示它可能可以删除。",
        "why": ["函数从未被调用", "参数在函数体里从未被引用"],
        "fix": ["删掉未使用的声明", "如果是参数，删掉或用 `_` 忽略"],
    },

    ErrorCategory.INVALID_TARGET: {
        "title": "归纳目标无效（索引出现多次）",
        "what": (
            "使用 `induction`（或依赖模式匹配）时，Lean 需要对目标做「泛化」。"
            "这个错误表示你要归纳的变量在目标（或其他假设的类型）中出现了多次，"
            "导致 Lean 无法干净地泛化它。这是初学者最容易懵的 Lean 报错之一。"
        ),
        "why": [
            "归纳变量在目标中出现了不止一次",
            "要归纳的假设带有索引，且该索引在其他地方也出现",
            "其实需要依赖模式匹配，但你用了普通的 `induction`/`cases`",
        ],
        "fix": [
            "先对出问题的变量用 `generalize`，或 `revert` 其他提到它的假设",
            "试试给 `induction` 显式指定 motive",
            "有时用 `rcases` / 直接对构造子做模式匹配，比 `induction` 更有效",
        ],
    },

    ErrorCategory.CALC_ERROR: {
        "title": "calc 步骤无效",
        "what": (
            "在 `calc` 块中，每一步的右侧必须与链式推导要求的值定义相等。"
            "Lean 发现你写的这一步没有正确衔接上链条（步与步之间类型不匹配）。"
        ),
        "why": [
            "`calc` 中间表达式与链条要求的不一致",
            "某一步 `by ...` 的证明其实证的是另一个等式",
            "链条期望的值（来自上一步）和你声称的不一样",
        ],
        "fix": [
            "看报错的 'right-hand side is'（你写的）vs 'but is expected to be'（链条需要的）",
            "检查每一步的左侧是否等于上一步的右侧",
            "确保 `:=` 后面的证明恰好证明显示的那个等式",
        ],
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
        "fix": ["如果它经常出现，欢迎到仓库提 issue，我们会补充模板。"],
    },
}
