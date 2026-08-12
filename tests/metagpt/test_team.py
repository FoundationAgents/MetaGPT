#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of team

from metagpt.const import MESSAGE_ROUTE_TO_ALL
from metagpt.roles.project_manager import ProjectManager
from metagpt.team import Team


def test_team():
    company = Team()
    company.hire([ProjectManager()])

    assert len(company.env.roles) == 1


def test_run_project_send_to():
    company = Team(use_mgx=False)

    company.run_project("A test idea", send_to="Alex")

    message = company.env.history.get(k=1)[0]
    assert message.content == "A test idea"
    assert message.send_to == {"Alex"}


def test_run_project_broadcast_by_default():
    company = Team(use_mgx=False)

    company.run_project("A test idea")

    message = company.env.history.get(k=1)[0]
    assert message.send_to == {MESSAGE_ROUTE_TO_ALL}
