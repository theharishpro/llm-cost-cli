import json

from typer.testing import CliRunner

from llmcost.cli import app

runner = CliRunner()


def test_estimate_json_with_text():
    result = runner.invoke(app, ["estimate", "--text", "Hello there", "-m", "openai", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["results"]
    costs = [r["total_cost"] for r in data["results"]]
    assert costs == sorted(costs)


def test_requests_multiplies_cost():
    one = json.loads(runner.invoke(app, ["estimate", "-t", "hi", "-m", "gpt-4o", "--json"]).output)
    many = json.loads(runner.invoke(app, ["estimate", "-t", "hi", "-m", "gpt-4o", "-n", "1000", "--json"]).output)
    assert many["results"][0]["total_cost"] == round(one["results"][0]["cost_per_request"] * 1000, 8)


def test_estimate_from_file(tmp_path):
    f = tmp_path / "prompt.txt"
    f.write_text("Summarise this document.")
    result = runner.invoke(app, ["estimate", str(f), "-m", "anthropic"])
    assert result.exit_code == 0, result.output


def test_missing_file():
    result = runner.invoke(app, ["estimate", "nope.txt"])
    assert result.exit_code == 1


def test_unknown_model():
    result = runner.invoke(app, ["estimate", "-t", "hi", "-m", "fake-model"])
    assert result.exit_code == 1


def test_models_lists():
    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "gpt-4o" in result.output
