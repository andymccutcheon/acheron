from acheron.ranking import fuse, rank_by_model


def _cands(*titles):
    return [{"title": t, "entity": t.lower(), "path": t.lower(), "snippet": "", "project": "p"} for t in titles]


def test_native_order_without_model_scores():
    cands = _cands("A", "B", "C")
    fused = fuse(cands, None)
    assert [c["title"] for c in fused] == ["A", "B", "C"]
    assert all(c["model_score"] is None for c in fused)


def test_model_demoted_native_leader_loses_top_slot():
    cands = _cands("A", "B", "C", "D", "E")
    # The model strongly prefers B and heavily demotes A
    scores = [0.0, 3.0, 2.0, 1.0, 0.1]
    fused = fuse(cands, scores)
    assert [c["title"] for c in fused][:2] == ["B", "C"]
    assert fused[0]["native_rank"] == 2
    assert fused[-1]["title"] == "E"


def test_fusion_rewards_strength_on_both_lists():
    cands = _cands("A", "B", "C", "D")
    scores = [None, None, 0.0, 2.0]  # D scored best, C scored worst
    fused = fuse(cands, scores)
    # A (native 1, model 3) tops; D (native 4, model 1) rises to 2;
    # the model cannot push the native leaders below the weakest.
    assert [c["title"] for c in fused] == ["A", "D", "C", "B"]


def test_rank_by_model_orders_by_score_only():
    cands = _cands("A", "B", "C")
    scores = [1.0, 3.0, 2.0]
    ranked = rank_by_model(cands, scores)
    assert [c["title"] for c in ranked] == ["B", "C", "A"]
    assert ranked[0]["model_rank"] == 1
    assert ranked[0]["native_rank"] == 2
    assert ranked[0]["fused_score"] is None


def test_empty_input():
    assert fuse([], None) == []
    assert fuse([], []) == []
