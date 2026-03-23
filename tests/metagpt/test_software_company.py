#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/15 11:40
@Author  : alexanderwu
@File    : test_software_company.py
"""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from metagpt.const import TEAMLEADER_NAME
from metagpt.logs import logger
from metagpt.software_company import app, generate_repo
from metagpt.team import Team
from metagpt.utils.project_repo import ProjectRepo

runner = CliRunner()


@pytest.mark.asyncio
async def test_empty_team(new_filename):
    # FIXME: we're now using "metagpt" cli, so the entrance should be replaced instead.
    company = Team()
    history = await company.run(idea="Build a simple search system. I will upload my files later.")
    logger.info(history)


def test_software_company(new_filename, tmp_path, mocker):
    project_root = tmp_path / "snake_game"
    captured = {}

    async def fake_run(self, n_round=3, idea="", send_to="", auto_archive=True):
        captured["idea"] = idea
        captured["send_to"] = send_to
        root = Path(self.env.context.kwargs.project_path)
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
        return self.env.history

    mocker.patch("metagpt.team.Team.run", new=fake_run)

    args = ["Make a cli snake game", "--project-path", str(project_root)]
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert (project_root / "src" / "main.py").exists()
    assert captured["send_to"] == TEAMLEADER_NAME
    assert str(project_root) in captured["idea"]
    assert "must be persisted as files" in captured["idea"]


def test_generate_repo_returns_project_repo(tmp_path, mocker):
    project_root = tmp_path / "repo_return_case"

    async def fake_run(self, n_round=3, idea="", send_to="", auto_archive=True):
        root = Path(self.env.context.kwargs.project_path)
        (root / "app").mkdir(parents=True, exist_ok=True)
        (root / "app" / "server.py").write_text("print('ok')\n", encoding="utf-8")
        return self.env.history

    mocker.patch("metagpt.team.Team.run", new=fake_run)

    repo = generate_repo("Build a tiny API", project_path=str(project_root))
    assert isinstance(repo, ProjectRepo)
    assert repo.workdir == project_root
    assert (project_root / "app" / "server.py").exists()


def test_generate_repo_fails_when_no_files_persisted(tmp_path, mocker):
    project_root = tmp_path / "empty_case"

    async def fake_run(self, n_round=3, idea="", send_to="", auto_archive=True):
        return self.env.history

    mocker.patch("metagpt.team.Team.run", new=fake_run)

    with pytest.raises(RuntimeError, match="without persisted files"):
        generate_repo("Make a cli snake game", project_path=str(project_root), implement=True)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
