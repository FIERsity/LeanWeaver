import Mathlib

theorem good_demo (P Q R : Prop) (h1 : P → Q) (h2 : Q → R) (hp : P) : R := by
  apply h2
  apply h1
  exact hp

theorem broken_demo (a : Nat) : a = 0 := by
  rfl
