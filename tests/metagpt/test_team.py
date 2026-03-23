#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of team

from metagpt.const import TEAMLEADER_NAME
from metagpt.roles.project_manager import ProjectManager
from metagpt.team import Team


def test_team():
    company = Team()
    company.hire([ProjectManager()])

    assert len(company.env.roles) == 1


def test_run_project_with_send_to():
    company = Team()
    company.hire([ProjectManager()])

    company.run_project("Build a todo app", send_to=TEAMLEADER_NAME)
    published = company.env.history.get()[-1]

    assert TEAMLEADER_NAME in published.send_to
