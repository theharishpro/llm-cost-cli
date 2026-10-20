"""Token counting with tiktoken, falling back to a character heuristic."""

from __future__ import annotations

from functools import lru_cache

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None

CHARS_PER_TOKEN = 4


@lru_cache(maxsize=None)
def _get_encoding(name: str):
    if tiktoken is None:
        return None
    try:
        return tiktoken.get_encoding(name)
    except Exception:
        # Encoding files are downloaded on first use; offline machines land here.
        return None


def heuristic_count(text: str) -> int:
    """Rough estimate: about 4 characters per token for English text."""
    if not text:
        return 0
    return max(1, round(len(text) / CHARS_PER_TOKEN))


def count_tokens(text: str, encoding: str = "o200k_base") -> tuple[int, bool]:
    """Return (token_count, used_tokenizer).

    used_tokenizer is False when the heuristic fallback was used.
    """
    enc = _get_encoding(encoding)
    if enc is None:
        return heuristic_count(text), False
    return len(enc.encode(text)), True
