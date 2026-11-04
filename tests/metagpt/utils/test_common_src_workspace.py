#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/11/4
@Author  : DZH166
@File    : test_common_src_workspace.py
@Desc    : Regression tests for the .src_workspace marker-file encoding contract.
"""
from pathlib import Path

import pytest


@pytest.mark.parametrize("src_name", ["中文src", "src_src"])
def test_get_project_srcs_path_reads_utf8_marker(tmp_path, src_name):
    """.src_workspace is written by awrite() with encoding="utf-8" (metagpt/actions/import_repo.py),
    so get_project_srcs_path must read it back as UTF-8. Reading with the platform default
    encoding mangles non-ASCII src directory names on hosts with a legacy ANSI code page
    (cp936/cp1252) and returns a path to a nonexistent directory."""
    from metagpt.utils.common import get_project_srcs_path

    (tmp_path / ".src_workspace").write_bytes(src_name.encode("utf-8"))
    (tmp_path / src_name).mkdir()

    result = get_project_srcs_path(tmp_path)

    assert result == Path(tmp_path) / src_name


def test_get_project_srcs_path_falls_back_to_workdir_name(tmp_path):
    from metagpt.utils.common import get_project_srcs_path

    assert get_project_srcs_path(tmp_path) == Path(tmp_path) / tmp_path.name
