#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lightweight localization for MetaGPT CLI and user-facing messages."""

import os
from typing import Optional

from metagpt.locale.messages import MESSAGES, normalize_language

_current_language = normalize_language(os.environ.get("METAGPT_LANG", "English"))


def set_language(lang: Optional[str]) -> str:
    """Set active UI language and return the canonical name."""
    global _current_language
    _current_language = normalize_language(lang)
    return _current_language


def get_language() -> str:
    return _current_language


def init_locale(lang: Optional[str] = None) -> str:
    """Initialize locale from explicit arg, env var, or config.language."""
    if lang:
        return set_language(lang)
    env_lang = os.environ.get("METAGPT_LANG")
    if env_lang:
        return set_language(env_lang)
    try:
        from metagpt.config2 import config

        if config.language and config.language != "English":
            return set_language(config.language)
    except Exception:
        pass
    return _current_language


def t(key: str, **kwargs) -> str:
    """Translate a message key for the active language."""
    lang = normalize_language(_current_language)
    catalog = MESSAGES.get(lang, MESSAGES["English"])
    text = catalog.get(key, MESSAGES["English"].get(key, key))
    return text.format(**kwargs) if kwargs else text


__all__ = ["init_locale", "set_language", "get_language", "normalize_language", "t"]
