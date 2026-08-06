import Verbose.Tactics.Common

/-!
# 中文语法类别（对应英文 Common.lean 里的 maybeApplied / newStuff / facts）

verbose-lean4 的机制层（Verbose.Tactics.*）依赖英文语法类别
（`maybeApplied`、`newStuff`、`facts` 等）。中文词表不能直接复用——
因为「应用到」「使用」「得到」这些词是中文的，必须声明自己的语法类别，
再把中文语法解析成机制层能理解的形式。
-/

namespace Verbose.Chinese

open Lean

/-- 中文版「可能被应用的项」：
  `h` / `h 应用到 x` / `h 应用到 x 使用 y` / `h 应用到 x 使用已知 y` -/
declare_syntax_cat maybeAppliedZH
syntax term : maybeAppliedZH
syntax term " 应用到 " term : maybeAppliedZH
syntax term " 应用到 " term " 使用 " term : maybeAppliedZH
syntax term " 应用到 " term " 使用已知 " term : maybeAppliedZH

/-- 把中文 maybeAppliedZH 语法转成机制层能用的英文 maybeApplied 语法。 -/
def maybeAppliedZHToMaybeApplied : TSyntax `maybeAppliedZH → MacroM (TSyntax `maybeApplied)
  | `(maybeAppliedZH| $e:term) => `(maybeApplied| $e:term)
  | `(maybeAppliedZH| $e:term 应用到 $x:term) => `(maybeApplied| $e:term applied to $x:term)
  | `(maybeAppliedZH| $e:term 应用到 $x:term 使用 $y:term) =>
      `(maybeApplied| $e:term applied to $x:term using $y:term)
  | `(maybeAppliedZH| $e:term 应用到 $x:term 使用已知 $y:term) =>
      `(maybeApplied| $e:term applied to $x:term using that $y:term)
  | _ => pure ⟨Syntax.missing⟩

/-- 中文版「新东西」：`(h₁ : A) (h₂ : B)` 或 `x 使得 H`。 -/
declare_syntax_cat newStuffZH
syntax (ppSpace colGt maybeTypedIdent)* : newStuffZH
syntax maybeTypedIdent " 使得 " ppSpace colGt maybeTypedIdent : newStuffZH
syntax maybeTypedIdent " 使得 " ppSpace colGt maybeTypedIdent " 且 "
       ppSpace colGt maybeTypedIdent : newStuffZH

/-- 中文 newStuffZH → 英文 newStuff。 -/
def newStuffZHToNewStuff : TSyntax `newStuffZH → MacroM (TSyntax `newStuff)
  | `(newStuffZH| $news:maybeTypedIdent*) => `(newStuff| $news:maybeTypedIdent*)
  | `(newStuffZH| $x:maybeTypedIdent 使得 $news:maybeTypedIdent) =>
      `(newStuff| $x:maybeTypedIdent such that $news:maybeTypedIdent)
  | `(newStuffZH| $x:maybeTypedIdent 使得 $y:maybeTypedIdent 且 $z:maybeTypedIdent) =>
      `(newStuff| $x:maybeTypedIdent such that $y:maybeTypedIdent and $z:maybeTypedIdent)
  | _ => pure ⟨Syntax.missing⟩

/-- 中文「事实」列表：`P` / `P 且 Q` / `P，Q 且 R`。 -/
declare_syntax_cat factsZH
syntax term : factsZH
syntax term " 且 " term : factsZH
syntax term "， " term " 且 " term : factsZH

/-- 中文 factsZH → 英文 facts。 -/
def factsZHToFacts : TSyntax `factsZH → MacroM (TSyntax `facts)
  | `(factsZH| $x:term) => `(facts| $x:term)
  | `(factsZH| $x:term 且 $y:term) => `(facts| $x:term and $y:term)
  | `(factsZH| $x:term， $y:term 且 $z:term) => `(facts| $x:term, $y:term and $z:term)
  | _ => pure ⟨Syntax.missing⟩

end Verbose.Chinese
