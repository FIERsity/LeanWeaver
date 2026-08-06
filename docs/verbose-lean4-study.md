# verbose-lean4 学习笔记

> 来源：https://github.com/PatrickMassot/verbose-lean4（ITP2024 论文）
> 定位：用"受控自然语言"写 Lean 证明，目标是 **让 Lean 代码更容易转化成传统论文证明**。
> 意义：它是"形式化证明 → 自然语言"的一种**确定性、可验证**的实现路线——正是 LeanWeaver 阶段② 的参照系之一。

## 一、架构精髓：机制与语言完全分离

```
Verbose/Tactics/*.lean   ← 通用机制（tactic 逻辑，语言无关）
Verbose/English/*.lean   ← 语言层：自然语言语法 + 错误文案
Verbose/French/*.lean    ← 同一套机制，换一套词
```

翻译一种新语言 = **复制 English 文件夹，替换用户可见的英文词**。
作者明确说：他不维护自己不懂的语言，但**欢迎别人单独做自己的语言版**——中文版是空白机会。

## 二、三大技术支柱

### 1. 语法扩展（syntax + elab）——定义"自然语言命令"
```lean
elab "By " e:maybeApplied " we get " colGt news:newStuff : tactic => do
  obtainTac (← maybeAppliedToTerm e) (newStuffToArray news)
```
- 用 `declare_syntax_cat` 定义中间语法类（如 `maybeApplied`、`newStuff`、`facts`）
- 用 `elab` 把自然语言短语绑定到通用 tactic
- 语法类名也按语言翻译（如 `maybeAppliedFR`），方便同一文档里同时 import 多语言

### 2. register_endpoint / implement_endpoint——错误信息按语言注册
```lean
-- 机制层：声明"这里需要一句话"
register_endpoint cannotGet : CoreM String

-- 语言层：提供文案
implement_endpoint (lang := en) cannotGet : CoreM String := pure "Cannot get this."
implement_endpoint (lang := fr) cannotGet : CoreM String := pure "Impossible d'obtenir cela."
```
> 💡 **这和我们 LeanWeaver 的 locales 设计理念完全一致**（我们是用 Python dict + 回退英文，它是用 Lean 元编程）。殊途同归。

### 3. 面向教学的整体环境
不只是 tactic——还有一整套教学 DSL：
```lean
Exercise "Continuity implies sequential continuity"
  Given: (f : ℝ → ℝ) (u : ℕ → ℝ) (x₀ : ℝ)
  Assume: (hu : u converges to x₀) ...
  Conclusion: ...
Proof:
  Let's prove that ∀ ε > 0, ∃ N, ∀ n ≥ N, ...
  By hf applied to ε using that ε > 0 we get δ such that ...
  ...
QED
```
- `help` tactic：根据当前假设**推荐下一步**（点按界面，见 verbose_widget_test_en.gif）
- 这就是"AI 建议"的**确定性版本**——规则式的 `suggestion`，而不是 LLM 猜测

## 三、自然语言命令清单（English 层）

| 短语 | 底层行为 |
|---|---|
| `We proceed using ...` | 引入/使用 |
| `We conclude by ...` | exact / close goal |
| `By h applied to x using that P we get y such that Q` | 应用假设 + 分解 |
| `By h we get (a : A) (b : B)` | rcases 分解 |
| `By h it suffices to prove P and Q` | apply + 拆目标 |
| `It suffices to prove that ...` | 目标转换 |
| `Since P and Q we conclude that R` | 前向推理 |
| `We discuss depending on whether P or Q` | by_cases |
| `Let's prove that ...` / `Let's first prove that ...` | have |
| `We compute` / `Calc ... from ...` | 计算证明 |
| `We contrapose` / `push the negation` | 反证/否定推进 |
| `Set x := ...` | let |
| `Fix ε > 0` | 引入 ∀ 变量 |
| `hypothesis` | assumption 强化版 |

## 四、对 LeanWeaver 的启示

1. **路线互补**：verbose-lean4 是"受控自然语言"（确定性、可验证、覆盖面有限）；
   我们的证明翻译器用 LLM（灵活、覆盖广、但不可验证）。
   **最佳实践 = 混合**：高频模式化步骤用 verbose 式规则，自由解释用 LLM。
   （与 README"分层架构"原则完全一致）

2. **中文词表 = 彩蛋方向**：可做 `Verbose/Chinese/`，即 verbose-lean4 的中文版。
   词表示例：`我们由 h 得到` / `只需证明` / `于是` / `设 x := ...` / `对 ε > 0 固定` / `反证` / `分类讨论`。
   注意：Lean 支持 Unicode 标识符，中文可直接作 tactic 关键字（syntax 字符串可含中文）。

3. **教学 DSL 是更大的机会**：`Exercise/Given/Assume/Proof/QED` 这套东西 + 中文，
   可以直接服务中文数学教育（高考/考研/竞赛的形式化入门）。

## 五、关键技术备忘

- 依赖：mathlib（v4.31.0）+ Lean 4.31.0（本项目用 stable = 4.32.2，做中文版时对齐版本）
- 参考库：verbose-lean-demo（最小示例）、proofs_with_lean（练习题全集）、MDD154（法语版）
- 许可：Apache-2.0（LICENSE 11KB，需注意与 MIT 的兼容）
