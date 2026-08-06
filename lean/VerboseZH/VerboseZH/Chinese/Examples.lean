import VerboseZH.Chinese.All

/-!
# 中文战术示例

每个示例对照一段"论文式中文证明"，展示中文战术的用法。
-/

namespace VerboseZH.Chinese.Examples

example (P Q : Prop) (h : P ∧ Q) : Q := by
  -- 证明：由 h 我们得到 Q。
  我们由 h 得到 (hQ : Q)
  恰有 hQ

example (n : Nat) (h : ∃ k, n = 2*k) : True := by
  -- 证明：由 h 我们得到 k，使得 n = 2*k。
  我们由 h 得到 k 使得 (H : n = 2*k)
  平凡

example (P Q : Prop) (h : P → Q) (h' : P) : Q := by
  -- 证明：由 h 只需证明 P；这由 h' 成立。
  我们由 h 只需证明 P
  恰有 h'

example (P Q R : Prop) (h : P → R → Q) (hP : P) (hR : R) : Q := by
  -- 证明：由 h 只需证明 P 且 R。
  我们由 h 只需证明 P 且 R
  恰有 hP
  恰有 hR

example (P Q : Prop) (h : P ∨ Q) : True := by
  -- 证明：分类讨论。
  分类讨论 P
  · 恰有 h
    平凡
  · 平凡

example (P : Prop) (h : P) : P := by
  -- 证明：恰有 h。
  恰有 h

example (a b : Nat) : a + b = b + a := by
  -- 证明：改写（使用加法交换律）。
  我们改写 Nat.add_comm

example (P : Prop) : P → P := by
  -- 证明：固定 h，恰有 h。
  固定 h
  恰有 h

end VerboseZH.Chinese.Examples
