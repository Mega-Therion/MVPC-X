# Rule: Prefer `linarith` or dedicated lemmas for simple numeric inequalities

When proving statements such as `a < b`, `a ≤ b`, or `a ≠ b` where `a` and `b` are concrete real numbers:

- **Avoid** the `decide` tactic – it may encounter undecidable instances (e.g., `2 ≠ 1`).
- **Use** one of:
  - `linarith` – works for linear arithmetic over ℝ and ℚ.
  - Library lemmas like `Real.log_lt_sub_one_of_pos`, `Real.exp_pos`, `Real.log_pos`, etc.

This guidance reduces proof failures and speeds up formalization of physics‑related inequalities.
