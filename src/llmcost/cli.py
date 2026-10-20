"""Command-line interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .pricing import PricingError, estimate_cost, load_pricing, select_models
from .tokens import count_tokens

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Estimate token counts and API cost for a prompt across LLM providers.",
)
console = Console()
err = Console(stderr=True)


def _read_input(file: Optional[str], text: Optional[str]) -> str:
    if text is not None:
        return text
    if file and file != "-":
        path = Path(file)
        if not path.is_file():
            err.print(f"[red]File not found:[/red] {file}")
            raise typer.Exit(1)
        return path.read_text(encoding="utf-8", errors="replace")
    if file == "-" or not sys.stdin.isatty():
        return sys.stdin.read()
    err.print("[red]No input.[/red] Pass a file, '-' for stdin, or --text.")
    raise typer.Exit(1)


SYMBOLS = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥"}


def _money(value: float, currency: str = "USD") -> str:
    sym = SYMBOLS.get(currency, f"{currency} ")
    if value == 0:
        return f"{sym}0"
    if value < 0.01:
        return f"{sym}{value:.6f}"
    return f"{sym}{value:,.4f}" if value < 100 else f"{sym}{value:,.2f}"


def _resolve_currency(base: str, currency: Optional[str], rate: Optional[float]) -> tuple[str, float]:
    """Return (display_currency, multiplier) for converting from the pricing currency."""
    if currency is None or currency.upper() == base.upper():
        return base, 1.0
    if rate is None:
        err.print(f"[red]--currency {currency.upper()} needs --rate[/red] (1 {base} = RATE {currency.upper()}).")
        raise typer.Exit(1)
    return currency.upper(), rate


@app.command()
def estimate(
    file: Optional[str] = typer.Argument(None, help="Prompt file, or '-' to read stdin."),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Prompt text instead of a file."),
    model: List[str] = typer.Option(["all"], "--model", "-m", help="Model or provider name. Repeat for several. Default: all."),
    output_tokens: int = typer.Option(500, "--output-tokens", "-o", min=0, help="Expected output tokens per request."),
    requests: int = typer.Option(1, "--requests", "-n", min=1, help="Number of requests, e.g. per month."),
    pricing: Optional[Path] = typer.Option(None, "--pricing", help="Custom pricing JSON file."),
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Show costs in another currency, e.g. INR. Needs --rate."),
    rate: Optional[float] = typer.Option(None, "--rate", min=0.000001, help="Exchange rate: 1 pricing-currency unit = RATE units."),
    as_json: bool = typer.Option(False, "--json", help="Print JSON instead of a table."),
) -> None:
    """Estimate cost for a prompt."""
    prompt = _read_input(file, text)
    try:
        table = load_pricing(pricing)
        models = select_models(table, model)
    except (PricingError, OSError) as exc:
        err.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    display_currency, fx = _resolve_currency(table.currency, currency, rate)

    rows = []
    for m in models:
        tokens, used_tokenizer = count_tokens(prompt, m.encoding)
        per_request = estimate_cost(m, tokens, output_tokens) * fx
        rows.append(
            {
                "model": m.name,
                "provider": m.provider,
                "input_tokens": tokens,
                "output_tokens": output_tokens,
                "approximate": not (m.exact and used_tokenizer),
                "cost_per_request": round(per_request, 8),
                "total_cost": round(per_request * requests, 8),
            }
        )
    rows.sort(key=lambda r: r["total_cost"])

    if as_json:
        payload = {"requests": requests, "currency": display_currency,
                   "pricing_updated": table.last_updated, "results": rows}
        if fx != 1.0:
            payload["fx_rate"] = {"from": table.currency, "to": display_currency, "rate": fx}
        print(json.dumps(payload, indent=2))
        return

    out = Table(title=f"LLM cost estimate · {requests:,} request(s)", title_justify="left")
    out.add_column("Model")
    out.add_column("Provider")
    out.add_column("Input tok", justify="right")
    out.add_column("Output tok", justify="right")
    out.add_column("Per request", justify="right")
    out.add_column("Total", justify="right", style="bold")
    for r in rows:
        approx = "≈" if r["approximate"] else ""
        out.add_row(r["model"], r["provider"], f"{approx}{r['input_tokens']:,}", f"{r['output_tokens']:,}",
                    _money(r["cost_per_request"], display_currency), _money(r["total_cost"], display_currency))
    console.print(out)
    note = f" · converted at 1 {table.currency} = {fx:g} {display_currency}" if fx != 1.0 else ""
    console.print(f"[dim]≈ approximate token count · prices per 1M tokens, updated {table.last_updated}"
                  f"{note} · verify against provider pricing pages[/dim]")


@app.command()
def models(
    pricing: Optional[Path] = typer.Option(None, "--pricing", help="Custom pricing JSON file."),
) -> None:
    """List models and prices."""
    try:
        table = load_pricing(pricing)
    except (PricingError, OSError) as exc:
        err.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    out = Table(title=f"Prices per 1M tokens ({table.currency}) · updated {table.last_updated}", title_justify="left")
    out.add_column("Model")
    out.add_column("Provider")
    out.add_column("Input", justify="right")
    out.add_column("Output", justify="right")
    for m in sorted(table.models.values(), key=lambda m: (m.provider, m.input_per_m)):
        out.add_row(m.name, m.provider, f"${m.input_per_m:g}", f"${m.output_per_m:g}")
    console.print(out)


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"llmcost {__version__}")


if __name__ == "__main__":  # pragma: no cover
    app()
