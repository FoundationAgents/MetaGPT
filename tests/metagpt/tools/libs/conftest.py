#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Local conftest that overrides the global autouse llm_mock fixture.

The sandbox_executor tests load modules via exec() in complete isolation and
do not need the LLM mock patching.  The global llm_mock fixture triggers
httpx proxy initialization which fails in some CI environments, so we
replace it with a no-op here.
"""
import pytest


@pytest.fixture(scope="function", autouse=True)
def llm_mock():
    """No-op override — sandbox executor tests don't touch LLM providers."""
    yield
