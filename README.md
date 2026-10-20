# llm-cost-cli

[![CI](https://github.com/theharishpro/llm-cost-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/theharishpro/llm-cost-cli/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Know what a prompt will cost before you ship it.**
`llmcost` counts tokens in a prompt and compares API cost across OpenAI, Anthropic and Google models in one table, for one request or a whole month of traffic.

```text
$ llmcost estimate examples/prompt.txt -n 10000

LLM cost estimate · 10,000 request(s)
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Model            ┃ Provider  ┃ Input tok ┃ Output tok ┃ Per request ┃    Total ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ gemini-2.0-flash │ google    │       ≈72 │        500 │   $0.000207 │  $2.0720 │
│ gpt-4o-mini      │ openai    │        66 │        500 │   $0.000310 │  $3.0990 │
│ ...              │           │           │            │             │          │
│ claude-opus-4    │ anthropic │       ≈72 │        500 │     $0.0386 │  $385.80 │
└──────────────────┴───────────┴───────────┴────────────┴─────────────┴──────────┘
```

## Install

```bash
pip install git+https://github.com/theharishpro/llm-cost-cli.git
```

From source:

```bash
git clone https://github.com/theharishpro/llm-cost-cli.git
cd llm-cost-cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# Compare all models for a prompt file
llmcost estimate prompt.txt

# Pipe from another command
cat prompt.txt | llmcost estimate -

# Inline text, specific models or providers
llmcost estimate -t "Summarise this article..." -m gpt-4o -m anthropic

# Monthly cost: 50k requests, ~800 output tokens each
llmcost estimate prompt.txt -n 50000 -o 800

# JSON output for scripts and CI
llmcost estimate prompt.txt --json

# List models and prices
llmcost models

# Use your own pricing file
llmcost estimate prompt.txt --pricing my_prices.json

# Show cost in INR (1 USD = 84 INR)
llmcost estimate prompt.txt -n 10000 -c INR --rate 84
```

| Option | Meaning | Default |
|---|---|---|
| `-m, --model` | Model name or provider (`openai`, `anthropic`, `google`, `all`). Repeatable. | `all` |
| `-o, --output-tokens` | Expected output tokens per request | `500` |
| `-n, --requests` | Number of requests to price | `1` |
| `-t, --text` | Prompt text instead of a file | none |
| `--pricing` | Custom pricing JSON | bundled |
| `--json` | Machine-readable output | off |
| `-c, --currency` / `--rate` | Show cost in another currency at the given rate | USD |

## How it works

- **Token counting:** uses [tiktoken](https://github.com/openai/tiktoken). Counts are exact for OpenAI models. Anthropic and Google use different tokenizers, so their counts are marked `≈` as estimates. With no tokenizer available (e.g. offline on first run), it falls back to ~4 characters per token.
- **Pricing:** stored in [`src/llmcost/data/pricing.json`](src/llmcost/data/pricing.json), in USD per 1M tokens. Override it with `--pricing`.

```json
{
  "last_updated": "2025-06",
  "models": [
    {"name": "my-model", "provider": "custom", "input": 1.0, "output": 4.0, "encoding": "o200k_base", "exact": false}
  ]
}
```

> ⚠️ Prices change often. Always check the provider's pricing page before budgeting. PRs that update prices are welcome.

## Project structure

```
src/llmcost/
├── cli.py          # Typer commands: estimate, models, version
├── pricing.py      # load pricing, select models, compute cost
├── tokens.py       # tiktoken counting + fallback
└── data/pricing.json
tests/              # pytest suite (runs in GitHub Actions)
```

## Development

```bash
pytest -q
```

## Roadmap

- [ ] Exact token counts via the Anthropic and Gemini token-count APIs (optional API key)
- [ ] Prompt caching and batch-API discounts
- [ ] Count tokens for chat-format JSON (`messages` arrays)
- [x] INR / other currency output
- [ ] Publish to PyPI

## License

MIT © Harish M
