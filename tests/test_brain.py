from mvpc.brain.goal_cache import GoalCache
from mvpc.brain.planner import plan_subgoals
from mvpc.brain.pucb import SearchNode, pucb_score, select_child
from mvpc.brain.solver import try_solve_subgoal


def test_pucb_prefers_promising_child():
    parent = SearchNode(name="root", q_value=0, prior=1, visits=10, children=[])
    a = SearchNode(name="a", q_value=0.2, prior=0.1, visits=1)
    b = SearchNode(name="b", q_value=0.9, prior=0.5, visits=1)
    parent.children = [a, b]
    assert select_child(parent).name == "b"
    assert pucb_score(b, 10) > pucb_score(a, 10)


def test_plan_and_cache():
    steps = plan_subgoals("theorem t : True", "Show truth. Then close.")
    assert len(steps) >= 1
    cache = GoalCache()
    r1 = try_solve_subgoal("True", [], cache=cache)
    r2 = try_solve_subgoal("True", [], cache=cache)
    assert r2.cached
    assert r1.success is False
