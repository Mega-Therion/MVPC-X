Theorem add_comm : forall n m : nat, n + m = m + n.
Proof.
  intros n m.
  induction n as [| n' IHn'].
  - simpl. rewrite Nat.add_0_r. reflexivity.
  - simpl. rewrite IHn'. rewrite Nat.add_succ_r. reflexivity.
Qed.
