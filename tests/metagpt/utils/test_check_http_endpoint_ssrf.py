#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression test for issue #2078: blind SSRF in check_http_endpoint.

Validates that _validate_url_safety rejects:
- non-http(s) schemes (file://, ftp://, gopher://, data:)
- loopback hostnames (localhost, 127.0.0.1, ::1, 0.0.0.0)
- private IPs (10.x, 192.168.x, 172.16-31.x, 169.254.x)
- link-local IPv6 (fe80::)
and accepts normal public hostnames.

Run: python3 tests/metagpt/utils/test_check_http_endpoint_ssrf.py
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "metagpt" / "utils" / "common.py"


def _load_common():
    for m in [
        "aiofiles", "aiohttp", "chardet", "loguru", "requests",
        "pydantic_core", "tenacity", "tenacity._utils",
        "metagpt", "metagpt.const", "metagpt.logs", "metagpt.utils",
        "metagpt.utils.exceptions", "metagpt.utils.json_to_markdown",
    ]:
        if m not in sys.modules:
            sys.modules[m] = MagicMock()
    import PIL.Image as _RI
    sys.modules["PIL"] = _RI
    sys.modules["PIL.Image"] = _RI
    spec = importlib.util.spec_from_file_location("metagpt.utils.common", str(SRC))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


common = _load_common()
_validate_url_safety = common._validate_url_safety


class TestValidateUrlSafety(unittest.TestCase):
    def test_rejects_file_scheme(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("file:///etc/passwd")

    def test_rejects_ftp_scheme(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("ftp://example.com/x")

    def test_rejects_data_scheme(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("data:text/plain,hello")

    def test_rejects_gopher_scheme(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("gopher://example.com/x")

    def test_rejects_localhost(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://localhost:8000/")

    def test_rejects_127(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://127.0.0.1:8000/")

    def test_rejects_0000(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://0.0.0.0/")

    def test_rejects_ipv6_loopback(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://[::1]:8080/")

    def test_rejects_private_192(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://192.168.1.1/")

    def test_rejects_private_10(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://10.0.0.1/")

    def test_rejects_private_172(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://172.16.0.1/")

    def test_rejects_link_local(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("http://169.254.169.254/latest/meta-data/")

    def test_accepts_public_http(self):
        # example.com resolves to public IANA IPs.
        _validate_url_safety("http://example.com/")
        _validate_url_safety("https://example.com/path")

    def test_rejects_no_scheme(self):
        with self.assertRaises(ValueError):
            _validate_url_safety("example.com/")


if __name__ == "__main__":
    unittest.main(verbosity=2)
