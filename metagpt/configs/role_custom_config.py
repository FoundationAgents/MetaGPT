#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/4/22 16:33
@Author  : Justin
@File    : role_custom_config.py
"""
from typing import Optional
from pydantic import Field
from metagpt.configs.llm_config import LLMConfig
from metagpt.utils.yaml_model import YamlModel


class RoleCustomConfig(YamlModel):
    """custom config for roles
    role: role's className or role's role_id
    To be expanded
    """

    role: str = ""
    llm: Optional[LLMConfig] = None
    config: dict = Field(default_factory=dict)
