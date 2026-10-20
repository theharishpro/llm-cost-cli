import json

import pytest

from llmcost.pricing import Model, PricingError, estimate_cost, load_pricing, select_models


def test_bundled_pricing_loads():
    table = load_pricing()
    assert table.models
    assert all(m.input_per_m >= 0 and m.output_per_m >= 0 for m in table.models.values())


def test_estimate_cost_math():
    m = Model("x", "p", input_per_m=2.0, output_per_m=8.0)
    # 1M input at $2 + 500k output at $8 = 2 + 4
    assert estimate_cost(m, 1_000_000, 500_000) == pytest.approx(6.0)


def test_estimate_cost_rejects_negative():
    m = Model("x", "p", 1, 1)
    with pytest.raises(ValueError):
        estimate_cost(m, -1, 0)


def test_select_by_provider_and_all():
    table = load_pricing()
    openai = select_models(table, ["openai"])
    assert openai and all(m.provider == "openai" for m in openai)
    assert len(select_models(table, ["all"])) == len(table.models)


def test_select_unknown_raises():
    with pytest.raises(PricingError):
        select_models(load_pricing(), ["no-such-model"])


def test_custom_pricing_file(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"last_updated": "test",
                             "models": [{"name": "m1", "provider": "p", "input": 1, "output": 2}]}))
    table = load_pricing(f)
    assert list(table.models) == ["m1"]
    assert table.last_updated == "test"


def test_invalid_pricing_file(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text('{"models": [{"name": "m1"}]}')
    with pytest.raises(PricingError):
        load_pricing(f)
