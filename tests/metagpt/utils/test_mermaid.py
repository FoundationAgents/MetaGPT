#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_mermaid.py
"""

import os
import sys
from types import SimpleNamespace

import pytest

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.utils.common import check_cmd_exists, new_transaction_id
from metagpt.utils.mermaid import MMC1, mermaid_to_file


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("engine", "suffixes"), [("nodejs", None), ("nodejs", ["png", "svg", "pdf"]), ("ink", None)]
)  # TODO: playwright and pyppeteer
async def test_mermaid(engine, suffixes, context, mermaid_mocker):
    # nodejs prerequisites: npm install -g @mermaid-js/mermaid-cli
    # ink prerequisites: connected to internet
    # playwright prerequisites: playwright install --with-deps chromium
    assert check_cmd_exists("npm") == 0

    save_to = DEFAULT_WORKSPACE_ROOT / f"{new_transaction_id()}/{engine}/1"
    await mermaid_to_file(engine, MMC1, save_to, suffixes=suffixes)

    # ink does not support pdf
    exts = ["." + i for i in suffixes] if suffixes else [".png"]
    if engine == "ink":
        for ext in exts:
            assert save_to.with_suffix(ext).exists()
            save_to.with_suffix(ext).unlink(missing_ok=True)
    else:
        for ext in exts:
            assert save_to.with_suffix(ext).exists()
            save_to.with_suffix(ext).unlink(missing_ok=True)


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform.startswith("win"), reason="shell script fake mmdc is POSIX-only")
async def test_mermaid_to_file_rejects_path_injection(tmp_path):
    """Regression test for issue #2037: command-injection via config.mermaid.path.

    Drives mermaid_to_file with a malicious path containing shell metacharacters
    and asserts the smuggled command does NOT execute. Uses a fake mmdc binary
    so the test does not depend on the real Mermaid CLI being installed.
    """
    fake_mmdc = tmp_path / "mmdc"
    fake_mmdc.write_text("#!/usr/bin/env bash\nexit 0\n")
    os.chmod(fake_mmdc, 0o755)

    marker = tmp_path / "INJECTED"
    malicious_path = f"{fake_mmdc}; touch {marker} #"

    config = SimpleNamespace(
        mermaid=SimpleNamespace(path=malicious_path, puppeteer_config="", engine="nodejs")
    )

    rc = await mermaid_to_file(
        engine="nodejs",
        mermaid_code="graph TD; A-->B;",
        output_file_without_suffix=str(tmp_path / "out"),
        config=config,
        suffixes=["svg"],
    )

    # Either check_cmd_exists rejects the path (-1) or subprocess_exec raises
    # FileNotFoundError. In both cases the marker file must not exist.
    assert not marker.exists(), "shell injection executed — path was passed through a shell"
    assert rc != 0, "malicious path should not produce a successful rendering"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
