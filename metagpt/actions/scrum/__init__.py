#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRUM-specific actions following MetaGPT framework patterns.
These actions use the standard _aask() method for LLM interactions.

Provides both new names (following MetaGPT patterns) and old names (backward compatibility).
"""

from metagpt.actions.scrum.refine_story import RefineStory
from metagpt.actions.scrum.design_system import DesignSystem
from metagpt.actions.scrum.write_feature import WriteFeature
from metagpt.actions.scrum.write_tests import WriteTests
from metagpt.actions.scrum.facilitate_scrum import FacilitateScrum

# Import existing ceremony actions for backward compatibility
from metagpt.actions.scrum.sprint_planning import SprintPlanningAction
from metagpt.actions.scrum.daily_standup import DailyStandupAction
from metagpt.actions.scrum.sprint_review import SprintReviewAction
from metagpt.actions.scrum.retrospective import RetrospectiveAction

__all__ = [
    # New MetaGPT-pattern actions
    "RefineStory",
    "DesignSystem",
    "WriteFeature", 
    "WriteTests",
    "FacilitateScrum",
    # Backward compatible ceremony actions
    "SprintPlanningAction",
    "DailyStandupAction",
    "SprintReviewAction",
    "RetrospectiveAction",
]
