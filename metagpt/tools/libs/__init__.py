#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/16 16:32
# @Author  : lidanyang
# @File    : __init__.py
# @Desc    :
from importlib import import_module

from metagpt.logs import logger
from metagpt.tools.libs.env import get_env, set_get_env_entry, default_get_env, get_env_description, get_env_default

_REGISTER_MODULES = [
    "data_preprocess",
    "feature_engineering",
    "sd_engine",
    "gpt_v_generator",
    "web_scraping",
    "terminal",
    "editor",
    "browser",
    "deployer",
    "git",
]

_loaded_modules = []
for _name in _REGISTER_MODULES:
    try:
        _loaded_modules.append(import_module(f"metagpt.tools.libs.{_name}"))
    except (ImportError, ModuleNotFoundError) as err:
        logger.warning(f"Skip loading tools module `{_name}` due to missing dependency: {err}")

_ = (
    _loaded_modules,
    get_env,
    get_env_default,
    get_env_description,
    set_get_env_entry,
    default_get_env,
)  # Avoid pre-commit error
