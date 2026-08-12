theory Clean
  imports Main
begin

lemma add_comm_nat: "a + b = (b + a :: nat)"
  by simp

end
