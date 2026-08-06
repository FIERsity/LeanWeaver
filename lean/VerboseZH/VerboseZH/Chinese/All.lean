import VerboseZH.Chinese.Tactics

/-!
# Verbose Lean 中文语言层汇总入口

用法：
```lean
import VerboseZH.Chinese.All

example (P Q : Prop) (h : P ∧ Q) : Q := by
  我们由 h 得到 (hQ : Q)
  恰有 hQ
```
-/

namespace VerboseZH.Chinese

open Lean

/-! ## 中文错误信息

对应 verbose-lean4 的 endpoint（英文版见 Verbose.English 各文件），
提供中文文案。这样用户用中文战术出错时，看到的是中文提示。 -/

implement_endpoint (lang := zh) cannotGet : CoreM String :=
  pure "无法由此得到。"

implement_endpoint (lang := zh) theName : CoreM String :=
  pure "该名称"

implement_endpoint (lang := zh) needName : CoreM String :=
  pure "你需要为选定的对象指定一个名称。"

implement_endpoint (lang := zh) wrongNbGoals : CoreM String :=
  pure "需要检查的命题数量不对。"

implement_endpoint (lang := zh) doesNotApply (fact : Format) : CoreM String :=
  pure s!"无法应用 {fact}。"

implement_endpoint (lang := zh) couldNotInferImplVal (val : Name) : CoreM String :=
  pure s!"无法推断隐式参数 {val} 的值。"

implement_endpoint (lang := zh) alsoNeedCheck (fact : Format) : CoreM String :=
  pure s!"你还需要检查 {fact}"

implement_endpoint (lang := zh) cannotConclude : CoreM String :=
  pure "这不能结束证明。"

implement_endpoint (lang := zh) nameAlreadyUsed (n : Name) : CoreM String :=
  pure s!"名称 {n} 已被使用"

end VerboseZH.Chinese
