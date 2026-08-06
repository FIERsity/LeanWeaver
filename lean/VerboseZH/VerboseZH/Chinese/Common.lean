import Verbose.English.Common

/-!
# 中文语法类别（对应英文 Common.lean 里的 maybeApplied / newStuff / facts）

verbose-lean4 的机制层（Verbose.Tactics.*）依赖英文语法类别
（`maybeApplied`、`newStuff`、`facts`）。中文词表不能直接复用——
因为「应用到」「使用」「得到」这些词是中文的，必须声明自己的语法类别，
再把中文语法解析成机制层能理解的 term / Array。

设计对齐 verbose 原版：
- `maybeAppliedZHToTerm : maybeAppliedZH → Term`（对应英文 `maybeAppliedToTerm`）
- `newStuffZHToArray : newStuffZH → Array MaybeTypedIdent`（对应英文 `newStuffToArray`）
- `factsZHToArray : factsZH → Array Term`（对应英文 `factsToArray`）
-/

namespace VerboseZH.Chinese

open Lean

/-- 中文版「可能被应用的项」：
  `h` / `h 应用到 x` / `h 应用到 x 使用 y` / `h 应用到 x 使用已知 y` -/
declare_syntax_cat maybeAppliedZH
syntax term : maybeAppliedZH
syntax term " 应用到 " term : maybeAppliedZH
syntax term " 应用到 " term " 使用 " term : maybeAppliedZH
syntax term " 应用到 " term " 使用已知 " term : maybeAppliedZH

/-- 把中文 maybeAppliedZH 语法解析成一个 Lean 项。 -/
def maybeAppliedZHToTerm : TSyntax `maybeAppliedZH → MetaM (TSyntax `term)
  | `(maybeAppliedZH| $e:term) => pure e
  | `(maybeAppliedZH| $e:term 应用到 $x:term) => `($e $x)
  | `(maybeAppliedZH| $e:term 应用到 $x:term 使用 $y:term) => `($e $x $y)
  | `(maybeAppliedZH| $e:term 应用到 $x:term 使用已知 $y:term) =>
      `($e $x (strongAssumption% $y))
  | _ => pure ⟨Syntax.missing⟩

/-- 中文版「新东西」：`(h₁ : A) (h₂ : B)` 或 `x 使得 H`。 -/
declare_syntax_cat newStuffZH
syntax (ppSpace colGt maybeTypedIdent)* : newStuffZH
syntax maybeTypedIdent " 使得 " ppSpace colGt maybeTypedIdent : newStuffZH
syntax maybeTypedIdent " 使得 " ppSpace colGt maybeTypedIdent " 且 "
       ppSpace colGt maybeTypedIdent : newStuffZH

/-- 把中文 newStuffZH 语法解析成 `Array MaybeTypedIdent`。 -/
def newStuffZHToArray : TSyntax `newStuffZH → Array MaybeTypedIdent
  | `(newStuffZH| $news:maybeTypedIdent*) => Array.map toMaybeTypedIdent news
  | `(newStuffZH| $x:maybeTypedIdent 使得 $news:maybeTypedIdent) =>
      Array.map toMaybeTypedIdent #[x, news]
  | `(newStuffZH| $x:maybeTypedIdent 使得 $y:maybeTypedIdent 且 $z:maybeTypedIdent) =>
      Array.map toMaybeTypedIdent #[x, y, z]
  | _ => #[]

/-- 中文「事实」列表：`P` / `P 且 Q` / `P，Q 且 R`。 -/
declare_syntax_cat factsZH
syntax term : factsZH
syntax term " 且 " term : factsZH
syntax term "， " term " 且 " term : factsZH

/-- 把中文 factsZH 语法解析成 `Array Term`。 -/
def factsZHToArray : TSyntax `factsZH → Array Term
  | `(factsZH| $x:term) => #[x]
  | `(factsZH| $x:term 且 $y:term) => #[x, y]
  | `(factsZH| $x:term， $y:term 且 $z:term) => #[x, y, z]
  | _ => #[]

end VerboseZH.Chinese
