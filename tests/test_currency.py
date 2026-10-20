import json

from typer.testing import CliRunner

from llmcost.cli import _money, app

runner = CliRunner()


def _run(*args):
    result = runner.invoke(app, ["estimate", "-t", "hello world", "-m", "openai", "--json", *args])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_inr_conversion_multiplies_cost():
    usd = _run()
    inr = _run("--currency", "INR", "--rate", "80")
    assert inr["currency"] == "INR"
    assert inr["fx_rate"] == {"from": "USD", "to": "INR", "rate": 80.0}
    for u, i in zip(usd["results"], inr["results"]):
        assert abs(i["total_cost"] - u["total_cost"] * 80) < 1e-6


def test_same_currency_needs_no_rate():
    data = _run("--currency", "usd")
    assert data["currency"] == "USD"
    assert "fx_rate" not in data


def test_currency_without_rate_fails():
    result = runner.invoke(app, ["estimate", "-t", "hi", "--currency", "INR"])
    assert result.exit_code == 1


def test_money_symbols():
    assert _money(250, "INR").startswith("₹")
    assert _money(1.5, "XYZ").startswith("XYZ ")
