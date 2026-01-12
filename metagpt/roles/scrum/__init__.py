#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRUM Agent Roles following MetaGPT framework patterns.
Based on examples/build_customized_multi_agents.py
"""

from metagpt.roles.scrum.product_owner import ProductOwner
from metagpt.roles.scrum.scrum_master import ScrumMaster
from metagpt.roles.scrum.architect import Architect
from metagpt.roles.scrum.engineer import Engineer
from metagpt.roles.scrum.qa_engineer import QAEngineer

__all__ = [
    "ProductOwner",
    "ScrumMaster",
    "Architect",
    "Engineer",
    "QAEngineer",
]
