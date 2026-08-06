import Verbose.Tactics.By
import Verbose.Tactics.We
import Verbose.Chinese.Common

/-!
# Verbose Lean 中文语言层（v0.1）

基于 verbose-lean4 的多语言机制（`register_endpoint` / `implement_endpoint`），
定义一套**中文自然语言战术**。设计目标：

1. 不重新实现机制——复用 `Verbose.Tactics.*` 的通用逻辑；
2. 只做**高频精选子集**（v0.1）：覆盖最常见的证明动作；
3. 语法与数学教育通用说法对齐（「我们由 h 得到」「只需证明」「设」「取」「反证」）。

用法（在 Lean 文件里）：
```lean
import Verbose.Chinese.Tactics

example (P Q : Prop) (h : P ∧ Q) : Q := by
  我们由 h 得到 (hQ : Q)
  恰有 hQ
```

中文关键字依赖 Lean 的 Unicode 标识符支持，`syntax` 字符串可直接包含中文。
-/

namespace Verbose.Chinese

open Lean Elab Parser Tactic

/-! ## 我们由 ... 得到 ...（分解假设，对应英文 By ... we get ...） -/

/-- `我们由 h 得到 (h₁ : A) (h₂ : B)`：分解假设 h。 -/
elab "我们由 " e:maybeAppliedZH " 得到 " colGt news:newStuffZH : tactic => do
  obtainTac (← maybeAppliedZHToMaybeApplied e) (newStuffZHToNewStuff news)

/-- `我们由 h 选取 ...`：选择函数（对应英文 By ... we choose ...）。 -/
elab "我们由 " e:maybeAppliedZH " 选取 " colGt news:newStuffZH : tactic => do
  chooseTac (← maybeAppliedZHToMaybeApplied e) (newStuffZHToNewStuff news)

/-- `我们由 h 只需证明 P`：把 h 应用到目标上（对应英文 By ... it suffices to prove）。 -/
elab "我们由 " e:maybeAppliedZH " 只需证明 " "that "? colGt arg:term : tactic => do
  bySufficesTac (← maybeAppliedZHToMaybeApplied e) #[arg]

/-- `我们由 h 只需证明 P 且 Q`：多目标版本。 -/
elab "我们由 " e:maybeAppliedZH " 只需证明 " "that "? colGt args:sepBy(term, " 且 ") : tactic => do
  bySufficesTac (← maybeAppliedZHToMaybeApplied e) args.getElems

/-! ## 我们得以 / 我们计算（对应英文 We conclude / We compute） -/

/-- `我们得以 h`：用 h 结束当前目标（exact 的自然语言版）。 -/
elab "我们得以 " e:maybeAppliedZH : tactic => do
  concludeTac (← maybeAppliedZHToMaybeApplied e)

/-- `我们计算`：计算化简（对应 We compute）。 -/
elab "我们计算" loc:(location)? : tactic => do
  computeTac loc

/-! ## 设 / 先证 / 固定（对应英文 Let's / Set / Fix） -/

/-- `设 x := v`：定义局部记号（let）。 -/
elab "设 " n:maybeTypedIdent " := " val:term : tactic => do
  evalTactic (← `(tactic| let $n:maybeTypedIdent := $val))

/-- `先证 P`：先证明一个中间断言（have）。 -/
elab "先证 " stmt:term : tactic => do
  evalTactic (← `(tactic| have $stmt))

/-- `固定 x`：引入一个 ∀ 变量（intro）。 -/
elab "固定 " x:ident : tactic => do
  evalTactic (← `(tactic| intro $x))

/-! ## 反证 / 分类讨论（对应英文 We contrapose / We discuss） -/

/-- `反证`：反证法。 -/
elab "反证" : tactic => do
  contraposeTac true

/-- `分类讨论 P 或 Q`：按命题分情况（by_cases）。 -/
elab "分类讨论 " factL:term " 或 " factR:term : tactic => do
  evalTactic (← `(tactic| by_cases h : $factL))

/-! ## 终结命令（对应英文 exact / trivial / assumption） -/

/-- `恰有 t`：用 t 精确结束目标（exact）。 -/
elab "恰有 " t:term : tactic => do
  evalTactic (← `(tactic| exact $t))

/-- `平凡`：平凡目标（trivial）。 -/
elab "平凡" : tactic => do
  evalTactic (← `(tactic| trivial))

/-- `假设成立`：直接尝试用假设解决（assumption 强化版，对应英文 hypothesis）。 -/
macro "假设成立" : term => `(by strg_assumption)

end Verbose.Chinese
