# Examples

| File | Use case | Try |
|---|---|---|
| `prompt.txt` | Support assistant | `llmcost estimate examples/prompt.txt -n 10000` |
| `summarize.txt` | Article summary | `llmcost estimate examples/summarize.txt -o 150` |
| `code_review.txt` | Code review bot | `llmcost estimate examples/code_review.txt -m openai -m anthropic` |
| `invoice_extraction.txt` | GST invoice → JSON | `llmcost estimate examples/invoice_extraction.txt -o 200 -n 50000` |
| `custom_pricing.json` | Your own models/prices | `llmcost estimate examples/prompt.txt --pricing examples/custom_pricing.json` |

Pipe and script:

```bash
cat examples/summarize.txt | llmcost estimate - --json | jq '.results[0]'
```
