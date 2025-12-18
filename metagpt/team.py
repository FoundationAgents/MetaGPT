#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : team.py
@Modified By: mashenquan, 2023/11/27. Add an archiving operation after completing the project, as specified in
        Section 2.2.3.3 of RFC 135.
"""

import warnings
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from metagpt.const import SERDESER_PATH
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import (
    NoMoneyException,
    read_json_file,
    serialize_decorator,
    write_json_file,
)


class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a env for instant messaging,
    dedicated to env any multi-agent activity, such as collaboratively writing executable code.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    env: Optional[Environment] = None
    investment: float = Field(default=10.0)
    idea: str = Field(default="")
    use_mgx: bool = Field(default=True)

    def __init__(self, context: Context = None, **data: Any):
        super(Team, self).__init__(**data)
        ctx = context or Context()
        if not self.env and not self.use_mgx:
            self.env = Environment(context=ctx)
        elif not self.env and self.use_mgx:
            self.env = MGXEnv(context=ctx)
        else:
            self.env.context = ctx  # The `env` object is allocated by deserialization
        if "roles" in data:
            self.hire(data["roles"])
        if "env_desc" in data:
            self.env.desc = data["env_desc"]

    def serialize(self, stg_path: Path = None):
        stg_path = SERDESER_PATH.joinpath("team") if stg_path is None else stg_path
        team_info_path = stg_path.joinpath("team.json")
        serialized_data = self.model_dump()
        serialized_data["context"] = self.env.context.serialize()

        write_json_file(team_info_path, serialized_data)

    @classmethod
    def deserialize(cls, stg_path: Path, context: Context = None) -> "Team":
        """stg_path = ./storage/team"""
        # recover team_info
        team_info_path = stg_path.joinpath("team.json")
        if not team_info_path.exists():
            raise FileNotFoundError(
                "recover storage meta file `team.json` not exist, " "not to recover and please start a new project."
            )

        team_info: dict = read_json_file(team_info_path)
        ctx = context or Context()
        ctx.deserialize(team_info.pop("context", None))
        team = Team(**team_info, context=ctx)
        return team

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.env.add_roles(roles)

    @property
    def cost_manager(self):
        """Get cost manager"""
        return self.env.context.cost_manager

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        self.cost_manager.max_budget = investment
        logger.info(f"Investment: ${investment}.")

    def _check_balance(self):
        if self.cost_manager.total_cost >= self.cost_manager.max_budget:
            raise NoMoneyException(self.cost_manager.total_cost, f"Insufficient funds: {self.cost_manager.max_budget}")

    def run_project(self, idea, send_to: str = ""):
        """Run a project from publishing user requirement."""
        self.idea = idea

        # Human requirement.
        self.env.publish_message(Message(content=idea))

    def start_project(self, idea, send_to: str = ""):
        """
        Deprecated: This method will be removed in the future.
        Please use the `run_project` method instead.
        """
        warnings.warn(
            "The 'start_project' method is deprecated and will be removed in the future. "
            "Please use the 'run_project' method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.run_project(idea=idea, send_to=send_to)

    @serialize_decorator
    async def run(self, n_round=3, idea="", send_to="", auto_archive=True):
        """Run company until target round or no money"""
        
        # Start tracing if enabled
        trace_collector = None
        if self.env.context.config.trace.enabled:
            from metagpt.trace import TraceCollector
            
            trace_collector = TraceCollector.get_instance(self.env.context.config.trace.level)
            project_name = self.env.context.config.project_name or "unnamed_project"
            trace_collector.start_project(project_name=project_name, idea=idea)

        # Initialize Meta-Org Agent if enabled
        meta_org_agent = None
        if self.env.context.config.meta_org.enabled:
            from metagpt.meta_org.agent import MetaOrgAgent
            from metagpt.meta_org.collector import SignalCollector
            
            # Use singleton collector
            signal_collector = SignalCollector.get_instance(project_id=self.env.context.config.project_name or "default")
            meta_org_agent = MetaOrgAgent(self, signal_collector)
            logger.info("Meta-Org Agent initialized and active.")
        
        try:
            if idea:
                self.run_project(idea=idea, send_to=send_to)

            original_round = n_round
            while n_round > 0:
                if self.env.is_idle:
                    logger.debug("All roles are idle.")
                    break
                n_round -= 1
                self._check_balance()
                
                try:
                    await self.env.run()
                except ValueError as e:
                    # Handle HITL rejection
                    if "rejected by human" in str(e):
                        logger.warning(f"[HITL] Workflow stopped by human: {e}")
                        break
                    raise

                # Meta-Org analysis cycle
                if meta_org_agent and (original_round - n_round) % self.env.context.config.meta_org.interval_round == 0:
                    logger.info("[MetaOrg] Starting periodic organization analysis...")
                    try:
                        await meta_org_agent.analyze_and_adapt()
                    except Exception as e:
                        logger.error(f"[MetaOrg] Analysis failed: {e}")

                logger.debug(f"max {n_round=} left.")
            
            self.env.archive(auto_archive)
            return self.env.history
            
        finally:
            if meta_org_agent:
                await meta_org_agent.postmortem()

            # End tracing and save if enabled
            if trace_collector and self.env.context.config.trace.enabled:
                trace_collector.end_project()
                
                if self.env.context.config.trace.save_on_complete:
                    try:
                        from metagpt.trace import TraceReporter
                        
                        trace_path = trace_collector.save()
                        report_path = TraceReporter.save_report(trace_collector.project_trace)
                        logger.info(f"[TRACE] Trace saved: {trace_path}")
                        logger.info(f"[TRACE] Report saved: {report_path}")
                    except Exception as e:
                        logger.warning(f"[TRACE] Failed to save trace: {e}")
