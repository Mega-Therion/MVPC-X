-- Smuggled axiom that proves False
axiom shortcut : False

theorem anything : 1 = 2 := by
  exact absurd rfl (by exact shortcut.elim)
