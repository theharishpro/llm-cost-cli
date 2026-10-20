from llmcost import tokens


def test_empty_text_is_zero():
    count, _ = tokens.count_tokens("")
    assert count == 0


def test_heuristic():
    assert tokens.heuristic_count("abcd" * 10) == 10


def test_fallback_when_tokenizer_unavailable(monkeypatch):
    monkeypatch.setattr(tokens, "_get_encoding", lambda name: None)
    count, used = tokens.count_tokens("hello world, this is a test")
    assert used is False
    assert count > 0
