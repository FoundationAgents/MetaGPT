import pytest

from metagpt.utils import text


@pytest.mark.timeout(2)
@pytest.mark.parametrize("remaining_tokens", [0, -1, 1])
def test_generate_prompt_chunk_rejects_insufficient_budget(monkeypatch, remaining_tokens):
    model = "test-model"
    monkeypatch.setitem(text.TOKEN_MAX, model, 128)
    monkeypatch.setattr(text, "count_output_tokens", lambda content, model_name: len(content) * 2)
    prompt_template = "Prompt: {}"
    system_text = "System"
    reserved = 128 - len(prompt_template + system_text) * 2 - 100 - remaining_tokens
    with pytest.raises(ValueError, match="token budget"):
        list(text.generate_prompt_chunk("Content to summarize.", prompt_template, model, system_text, reserved))


@pytest.mark.parametrize("content", ["", "fits"])
def test_generate_prompt_chunk_preserves_content_that_fits(monkeypatch, content):
    monkeypatch.setitem(text.TOKEN_MAX, "test-model", 128)
    monkeypatch.setattr(text, "count_output_tokens", lambda content, model_name: len(content) * 2)
    assert list(text.generate_prompt_chunk(content, "{}", "test-model", "", 16)) == ([content] if content else [])
