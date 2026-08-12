-- Contradictory binder hypotheses (vacuous if both required)
theorem vacuous_trap (x : Nat) (h1 : x > 5) (h2 : x < 2) : 1 = 0 := by
  sorry
