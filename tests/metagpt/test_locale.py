#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.locale import init_locale, set_language, t
from metagpt.locale.messages import normalize_language


def test_normalize_language_persian_aliases():
    for alias in ("fa", "fa-IR", "Persian", "Farsi", "فارسی"):
        assert normalize_language(alias) == "Persian"


def test_normalize_language_english():
    assert normalize_language("English") == "English"
    assert normalize_language("en") == "English"


def test_persian_cli_messages():
    set_language("fa")
    assert "IDEA" in t("missing_idea")
    assert "پیکربندی" in t("config_initialized", path="/tmp/x")


def test_init_locale_from_env(monkeypatch):
    monkeypatch.setenv("METAGPT_LANG", "fa")
    assert init_locale() == "Persian"
