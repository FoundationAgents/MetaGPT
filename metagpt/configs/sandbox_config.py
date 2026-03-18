#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/18
@File    : sandbox_config.py
"""
from typing import Dict, List, Optional

from metagpt.utils.yaml_model import YamlModel


class SandboxConfig(YamlModel):
    """Config for OpenSandbox integration."""

    enabled: bool = False
    domain: str = ""
    api_key: str = ""
    image: str = "opensandbox/code-interpreter:v1.0.2"
    entrypoint: List[str] = ["/opt/opensandbox/code-interpreter.sh"]
    timeout: int = 600
    resource: Dict[str, str] = {"cpu": "1", "memory": "2Gi"}
    env: Dict[str, str] = {}
    network_policy: Optional[Dict] = None
