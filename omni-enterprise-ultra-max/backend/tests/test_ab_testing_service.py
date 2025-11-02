import pytest
import asyncio
from backend.services.advanced_ai.ab_testing import ABTestingService


@pytest.mark.asyncio
async def test_create_experiment_and_get():
    svc = ABTestingService()
    exp = await svc.create_experiment(
        name="landing-page-cta",
        variants=["A", "B"],
        primary_metric="conversion_rate",
        owner="growth",
    )

    assert exp["name"] == "landing-page-cta"
    assert exp["primary_metric"] == "conversion_rate"
    assert exp["status"] == "running"
    assert sorted([v["name"] for v in exp["variants"]]) == ["a", "b"]
    for v in exp["variants"]:
        assert v["impressions"] == 0
        assert v["conversions"] == 0
        assert v["conversion_rate"] == 0
        assert v["average_value"] == 0


@pytest.mark.asyncio
async def test_record_impression_conversion_and_metrics():
    svc = ABTestingService()
    exp = await svc.create_experiment("cta", ["A", "B"], "conversion_rate")
    exp_id = exp["id"]

    # Record impressions
    await svc.record_event(exp_id, "A", "impression")
    await svc.record_event(exp_id, "A", "impression")
    await svc.record_event(exp_id, "B", "impression")

    # Record conversions with values
    await svc.record_event(exp_id, "A", "conversion", value=10.0)
    await svc.record_event(exp_id, "B", "conversion", value=20.0)
    await svc.record_event(exp_id, "B", "conversion", value=30.0)

    exp_view = await svc.get_experiment(exp_id)
    variants = {v["name"]: v for v in exp_view["variants"]}

    assert variants["a"]["impressions"] == 2
    assert variants["a"]["conversions"] == 1
    assert variants["a"]["conversion_rate"] == round(1/2, 4)
    assert variants["a"]["average_value"] == 10.0

    assert variants["b"]["impressions"] == 1
    assert variants["b"]["conversions"] == 2
    assert variants["b"]["conversion_rate"] == round(2/1, 4)
    assert variants["b"]["average_value"] == 25.0


@pytest.mark.asyncio
async def test_finalize_sets_winner_and_ignores_future_events():
    svc = ABTestingService()
    exp = await svc.create_experiment("subject", ["control", "treat"], "cr")
    exp_id = exp["id"]

    await svc.record_event(exp_id, "control", "impression")
    await svc.record_event(exp_id, "treat", "conversion", value=5)

    final = await svc.finalize_experiment(exp_id, winning_variant="treat", summary="Winner chosen")
    assert final["status"] == "completed"
    assert final["winner"] == "treat"
    assert any(n.get("event") == "summary" for n in final["notes"]) is True

    # Events after completion should be ignored (no changes to metrics)
    before = {v["name"]: (v["impressions"], v["conversions"]) for v in final["variants"]}
    await svc.record_event(exp_id, "control", "impression")
    await svc.record_event(exp_id, "treat", "conversion", value=10)
    after = await svc.get_experiment(exp_id)
    after_pairs = {v["name"]: (v["impressions"], v["conversions"]) for v in after["variants"]}
    assert after_pairs == before


@pytest.mark.asyncio
async def test_invalid_variant_raises():
    svc = ABTestingService()
    exp = await svc.create_experiment("exp", ["x"], "cr")
    with pytest.raises(KeyError):
        await svc.record_event(exp["id"], "y", "impression")
