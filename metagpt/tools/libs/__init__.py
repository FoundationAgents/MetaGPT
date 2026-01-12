#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/16 16:32
# @Author  : lidanyang
# @File    : __init__.py
# @Desc    :
try:
    from metagpt.tools.libs import data_preprocess
except ImportError:
    data_preprocess = None

try:
    from metagpt.tools.libs import feature_engineering
except ImportError:
    feature_engineering = None

try:
    from metagpt.tools.libs import sd_engine
except ImportError:
    sd_engine = None

try:
    from metagpt.tools.libs import gpt_v_generator
except ImportError:
    gpt_v_generator = None

try:
    from metagpt.tools.libs import web_scraping
except ImportError:
    web_scraping = None

# email_login,

try:
    from metagpt.tools.libs import terminal
except ImportError:
    terminal = None

try:
    from metagpt.tools.libs import editor
except ImportError:
    editor = None

try:
    from metagpt.tools.libs import browser
except ImportError:
    browser = None

try:
    from metagpt.tools.libs import deployer
except ImportError:
    deployer = None

try:
    from metagpt.tools.libs import git
except ImportError:
    git = None
from metagpt.tools.libs.env import get_env, set_get_env_entry, default_get_env, get_env_description, get_env_default

_ = (
    data_preprocess,
    feature_engineering,
    sd_engine,
    gpt_v_generator,
    web_scraping,
    # email_login,
    terminal,
    editor,
    browser,
    deployer,
    git,
    get_env,
    get_env_default,
    get_env_description,
    set_get_env_entry,
    default_get_env,
)  # Avoid pre-commit error
