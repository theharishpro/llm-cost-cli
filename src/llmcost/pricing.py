"""Load model pricing and compute costs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Optional

PER_MILLION = 1_000_000


@dataclass(frozen=True)
class Model:
    name: str
    provider: str
    input_per_m: float
    output_per_m: float
    encoding: str = "o200k_base"
    exact: bool = False  # True when tiktoken matches the provider's tokenizer


@dataclass(frozen=True)
class PricingTable:
    models: dict[str, Model]
    last_updated: str
    currency: str = "USD"


class PricingError(ValueError):
    pass


def _parse(data: dict) -> PricingTable:
    try:
        models = {
            m["name"]: Model(
                name=m["name"],
                provider=m["provider"],
                input_per_m=float(m["input"]),
                output_per_m=float(m["output"]),
                encoding=m.get("encoding", "o200k_base"),
                exact=bool(m.get("exact", False)),
            )
            for m in data["models"]
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise PricingError(f"Invalid pricing file: {exc}") from exc
    if not models:
        raise PricingError("Pricing file has no models.")
    return PricingTable(
        models=models,
        last_updated=str(data.get("last_updated", "unknown")),
        currency=data.get("currency", "USD"),
    )


def load_pricing(path: Optional[Path] = None) -> PricingTable:
    """Load the bundled pricing table, or a custom JSON file."""
    if path is not None:
        raw = Path(path).read_text(encoding="utf-8")
    else:
        raw = resources.files("llmcost").joinpath("data/pricing.json").read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PricingError(f"Pricing file is not valid JSON: {exc}") from exc
    return _parse(data)


def estimate_cost(model: Model, input_tokens: int, output_tokens: int) -> float:
    """Cost of one request in the table's currency."""
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts cannot be negative.")
    return (input_tokens * model.input_per_m + output_tokens * model.output_per_m) / PER_MILLION


def select_models(table: PricingTable, names: list[str]) -> list[Model]:
    """Resolve model names. 'all' selects everything; a provider name selects its models."""
    if not names or "all" in names:
        return list(table.models.values())
    selected: list[Model] = []
    for name in names:
        if name in table.models:
            selected.append(table.models[name])
            continue
        by_provider = [m for m in table.models.values() if m.provider == name]
        if not by_provider:
            raise PricingError(f"Unknown model or provider: {name!r}. Run 'llmcost models' to see options.")
        selected.extend(by_provider)
    # Keep order, drop duplicates.
    return list(dict.fromkeys(selected))
