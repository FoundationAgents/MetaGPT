#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A request the provider rejects as malformed or unauthorized is not sent again."""
import httpx
import openai
import pytest
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_none

from metagpt.utils.common import is_retryable_llm_error


def _openai_error(cls, status: int):
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return cls("rejected", response=httpx.Response(status, request=request), body=None)


@pytest.mark.parametrize(
    ("cls", "status"),
    [
        (openai.BadRequestError, 400),
        (openai.AuthenticationError, 401),
        (openai.PermissionDeniedError, 403),
        (openai.NotFoundError, 404),
        (openai.UnprocessableEntityError, 422),
    ],
)
def test_client_errors_are_not_retryable(cls, status):
    assert is_retryable_llm_error(_openai_error(cls, status)) is False


@pytest.mark.parametrize(
    ("cls", "status"),
    [(openai.RateLimitError, 429), (openai.InternalServerError, 500), (openai.ConflictError, 409)],
)
def test_transient_status_errors_are_retryable(cls, status):
    assert is_retryable_llm_error(_openai_error(cls, status)) is True


@pytest.mark.parametrize(
    "exc",
    [
        ValueError("could not parse the code block"),
        openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")),
        KeyError("Code Review Result"),
    ],
)
def test_parse_and_network_errors_stay_retryable(exc):
    assert is_retryable_llm_error(exc) is True


def test_httpx_status_error_uses_response_status():
    request = httpx.Request("POST", "https://example.com")
    exc = httpx.HTTPStatusError("bad", request=request, response=httpx.Response(401, request=request))
    assert is_retryable_llm_error(exc) is False


@pytest.mark.asyncio
async def test_bad_request_is_sent_once_under_the_action_retry_policy():
    calls = 0

    @retry(wait=wait_none(), stop=stop_after_attempt(6), retry=retry_if_exception(is_retryable_llm_error))
    async def aask():
        nonlocal calls
        calls += 1
        raise _openai_error(openai.BadRequestError, 400)

    with pytest.raises(openai.BadRequestError):
        await aask()
    assert calls == 1


@pytest.mark.asyncio
async def test_parse_failure_is_still_retried_under_the_action_retry_policy():
    calls = 0

    @retry(wait=wait_none(), stop=stop_after_attempt(6), retry=retry_if_exception(is_retryable_llm_error))
    async def aask():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("no code block")
        return "ok"

    assert await aask() == "ok"
    assert calls == 3
