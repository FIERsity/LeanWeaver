import Verbose.English.By
import Verbose.Tactics.We
import Verbose.Tactics.Set
import Verbose.Tactics.Common
import VerboseZH.Chinese.Common

/-!
# VerboseZH 中文语言层（v0.1）

基于 verbose-lean4 的多语言机制（`register_endpoint` / `implement_endpoint`），
定义一套**中文自然语言战术**。设计目标：

1. 不重新实现机制——复用 `Verbose.Tactics.*` 的通用逻辑；
2. 只做**高频精选子集**（v0.1）：覆盖最常见的证明动作；
3. 语法与数学教育通用说法对齐（「我们由 h 得到」「只需证明」「设」「反证」）。

用法（在 Lean 文件里）：
```lean
import VerboseZH.Chinese.Tactics

example (P Q : Prop) (h : P ∧ Q) : Q := by
  我们由 h 得到 (hQ : Q)
  恰有 hQ
```

中文关键字依赖 Lean 的 Unicode 标识符支持，`syntax` 字符串可直接包含中文。
-/

namespace VerboseZH.Chinese

open Lean Elab Parser Tactic

/-! ## 我们由 ... 得到 ...（分解假设，对应英文 By ... we get ...） -/

/-- `我们由 h 得到 (h₁ : A) (h₂ : B)`：分解假设 h。 -/
elab "我们由 " e:maybeAppliedZH " 得到 " colGt news:newStuffZH : tactic => do
  obtainTac (← maybeAppliedZHToTerm e) (newStuffZHToArray news)

/-- `我们由 h 选取 ...`：选择函数（对应英文 By ... we choose ...）。 -/
elab "我们由 " e:maybeAppliedZH " 选取 " colGt news:newStuffZH : tactic => do
  chooseTac (← maybeAppliedZHToTerm e) (newStuffZHToArray news)

/-- `我们由 h 只需证明 P`：把 h 应用到目标上（对应英文 By ... it suffices to prove）。 -/
elab "我们由 " e:maybeAppliedZH " 只需证明 " "that "? colGt arg:term : tactic => do
  bySufficesTac (← maybeAppliedZHToTerm e) #[arg]

/-- `我们由 h 只需证明 P 且 Q`：多目标版本。 -/
elab "我们由 " e:maybeAppliedZH " 只需证明 " "that "? colGt args:sepBy(term, " 且 ") : tactic => do
  bySufficesTac (← maybeAppliedZHToTerm e) args.getElems

/-! ## 我们得以 / 我们计算（对应英文 We conclude / We compute） -/

/-- `我们得以 h`：用 h 结束当前目标（exact 的自然语言版）。 -/
elab "我们得以 " e:maybeAppliedZH : tactic => do
  concludeTac (← maybeAppliedZHToTerm e)

/-- `我们计算`：计算化简（对应 We compute）。 -/
elab "我们计算" loc:(location)? : tactic => do
  computeTac loc

/-! ## 我们改写（对应英文 We rewrite using） -/

/-- `我们改写 h` / `我们改写 [h₁, h₂]`：用等式改写当前目标（rw）。
    复用 verbose 的 myRwRuleSeq 语法（h / [h₁,h₂] / ← h 均为 Lean 原生 rwRule，无英文词）。 -/
elab rw:"我们改写 " s:myRwRuleSeq : tactic => do
  rewriteTac rw s none none

/-! ## 设 / 先证 / 固定（对应英文 Let's / Set / Fix） -/

/-- `设 x := v` 或 `设 (x : T) := v`：定义局部记号（对应英文 Set）。
    复用 verbose 的 setTac（let 的底层实现）。 -/
elab "设 " n:maybeTypedIdent " := " val:term : tactic => do
  match n with
  | `(maybeTypedIdent| $N:ident) => setTac N none val
  | `(maybeTypedIdent| ($N : $TY)) => setTac N (some TY) val
  | _ => throwError "无效的 `设` 语法"



/-- `先证 P`：先证明中间断言 P（suffices 语义：先证 P，再用 P 推原目标）。
    P 必须是一个命题项。用法：`先证 P`，随后会有一个目标待证 P。 -/
elab "先证 " stmt:term : tactic => do
  evalTactic (← `(tactic| suffices h : $stmt by aesop))

/-- `固定 x`：引入一个 ∀ 变量（对应英文 Fix，底层是 intro）。 -/
elab "固定 " x:ident : tactic => do
  evalTactic (← `(tactic| intro $x:ident))

/-! ## 反证 / 分类讨论（对应英文 We contrapose / We discuss） -/

/-- `反证`：反证法。 -/
elab "反证" : tactic => do
  contraposeTac true

/-- `分类讨论 P`：按命题 P 分情况（by_cases）。 -/
elab "分类讨论 " factL:term : tactic => do
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

end VerboseZH.Chinese
