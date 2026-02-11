#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:19
@Author  : alexanderwu
@File    : test_common.py
@Modified by: mashenquan, 2023/11/21. Add unit tests.
"""
import importlib
import os
import platform
import uuid
from pathlib import Path
from typing import Any, Set

import pytest
from pydantic import BaseModel

from metagpt.actions import RunCode
from metagpt.const import get_metagpt_root
from metagpt.roles.tutorial_assistant import TutorialAssistant
from metagpt.schema import Message
from metagpt.utils.common import (
    NoMoneyException,
    OutputParser,
    any_to_str,
    any_to_str_set,
    aread,
    awrite,
    check_cmd_exists,
    concat_namespace,
    extract_and_encode_images,
    extract_image_paths,
    import_class_inst,
    is_safe_url,
    parse_recipient,
    print_members,
    read_file_block,
    read_json_file,
    require_python_version,
    split_namespace,
)


class TestGetProjectRoot:
    def change_etc_dir(self):
        # current_directory = Path.cwd()
        abs_root = "/etc"
        os.chdir(abs_root)

    def test_get_project_root(self):
        project_root = get_metagpt_root()
        src_path = project_root / "metagpt"
        assert src_path.exists()

    def test_get_root_exception(self):
        self.change_etc_dir()
        project_root = get_metagpt_root()
        assert project_root

    def test_any_to_str(self):
        class Input(BaseModel):
            x: Any = None
            want: str

        inputs = [
            Input(x=TutorialAssistant, want="metagpt.roles.tutorial_assistant.TutorialAssistant"),
            Input(x=TutorialAssistant(), want="metagpt.roles.tutorial_assistant.TutorialAssistant"),
            Input(x=RunCode, want="metagpt.actions.run_code.RunCode"),
            Input(x=RunCode(), want="metagpt.actions.run_code.RunCode"),
            Input(x=Message, want="metagpt.schema.Message"),
            Input(x=Message(content=""), want="metagpt.schema.Message"),
            Input(x="A", want="A"),
        ]
        for i in inputs:
            v = any_to_str(i.x)
            assert v == i.want

    def test_any_to_str_set(self):
        class Input(BaseModel):
            x: Any = None
            want: Set

        inputs = [
            Input(
                x=[TutorialAssistant, RunCode(), "a"],
                want={"metagpt.roles.tutorial_assistant.TutorialAssistant", "metagpt.actions.run_code.RunCode", "a"},
            ),
            Input(
                x={TutorialAssistant, "a"},
                want={"metagpt.roles.tutorial_assistant.TutorialAssistant", "a"},
            ),
            Input(
                x=(TutorialAssistant, RunCode(), "a"),
                want={"metagpt.roles.tutorial_assistant.TutorialAssistant", "metagpt.actions.run_code.RunCode", "a"},
            ),
            Input(
                x={"a": TutorialAssistant, "b": RunCode(), "c": "a"},
                want={"a", "metagpt.roles.tutorial_assistant.TutorialAssistant", "metagpt.actions.run_code.RunCode"},
            ),
        ]
        for i in inputs:
            v = any_to_str_set(i.x)
            assert v == i.want

    def test_check_cmd_exists(self):
        class Input(BaseModel):
            command: str
            platform: str

        inputs = [
            {"command": "cat", "platform": "linux"},
            {"command": "ls", "platform": "linux"},
            {"command": "mspaint", "platform": "windows"},
        ]
        plat = "windows" if platform.system().lower() == "windows" else "linux"
        for i in inputs:
            seed = Input(**i)
            result = check_cmd_exists(seed.command)
            if plat == seed.platform:
                assert result == 0
            else:
                assert result != 0

    @pytest.mark.parametrize(("filename", "want"), [("1.md", "File list"), ("2.md", "Language"), ("3.md", "# TODOs")])
    @pytest.mark.asyncio
    async def test_parse_data_exception(self, filename, want):
        pathname = Path(__file__).parent.parent.parent / "data/output_parser" / filename
        assert pathname.exists()
        data = await aread(filename=pathname)
        result = OutputParser.parse_data(data=data)
        assert want in result

    @pytest.mark.parametrize(
        ("ver", "want", "err"), [((1, 2, 3, 4), False, True), ((2, 3, 9), True, False), ((3, 10, 18), False, False)]
    )
    def test_require_python_version(self, ver, want, err):
        try:
            res = require_python_version(ver)
            assert res == want
        except ValueError:
            assert err

    def test_no_money_exception(self):
        val = NoMoneyException(3.10)
        assert "Amount required:" in str(val)

    @pytest.mark.parametrize("module_path", ["tests.metagpt.utils.test_common"])
    def test_print_members(self, module_path):
        module = importlib.import_module(module_path)
        with pytest.raises(Exception) as info:
            print_members(module)
            assert info is None

    @pytest.mark.parametrize(
        ("words", "want"), [("", ""), ("## Send To: Engineer", "Engineer"), ("Send To: \nNone", "None")]
    )
    def test_parse_recipient(self, words, want):
        res = parse_recipient(words)
        assert want == res

    def test_concat_namespace(self):
        assert concat_namespace("a", "b", "c") == "a:b:c"
        assert concat_namespace("a", "b", "c", "e") == "a:b:c:e"
        assert concat_namespace("a", "b", "c", "e", "f") == "a:b:c:e:f"

    @pytest.mark.parametrize(
        ("val", "want"),
        [
            (
                "tests/metagpt/test_role.py:test_react:Input:subscription",
                ["tests/metagpt/test_role.py", "test_react", "Input", "subscription"],
            ),
            (
                "tests/metagpt/test_role.py:test_react:Input:goal",
                ["tests/metagpt/test_role.py", "test_react", "Input", "goal"],
            ),
        ],
    )
    def test_split_namespace(self, val, want):
        res = split_namespace(val, maxsplit=-1)
        assert res == want

    def test_read_json_file(self):
        assert read_json_file(str(Path(__file__).parent / "../../data/ut_writer/yft_swaggerApi.json"), encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            read_json_file("not_exists_file", encoding="utf-8")
        with pytest.raises(ValueError):
            read_json_file(__file__, encoding="utf-8")

    def test_import_class_inst(self):
        rc = import_class_inst("RunCode", "metagpt.actions.run_code", name="X")
        assert rc.name == "X"

    @pytest.mark.asyncio
    async def test_read_file_block(self):
        assert await read_file_block(filename=__file__, lineno=6, end_lineno=6) == "@File    : test_common.py\n"

    @pytest.mark.asyncio
    async def test_read_write(self):
        pathname = Path(__file__).parent / f"../../../workspace/unittest/{uuid.uuid4().hex}" / "test.tmp"
        await awrite(pathname, "ABC")
        data = await aread(pathname)
        assert data == "ABC"
        pathname.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_read_write_error_charset(self):
        pathname = Path(__file__).parent / f"../../../workspace/unittest/{uuid.uuid4().hex}" / "test.txt"
        content = "中国abc123\u27f6"
        await awrite(filename=pathname, data=content)
        data = await aread(filename=pathname)
        assert data == content

        content = "GB18030 是中国国家标准局发布的新一代中文字符集标准，是 GBK 的升级版，支持更广泛的字符范围。"
        await awrite(filename=pathname, data=content, encoding="gb2312")
        data = await aread(filename=pathname, encoding="utf-8")
        assert data == content


def test_extract_image_paths():
    content = """
    Here are some image paths /home/user/images/photo1.jpg /home/user/images/photo2.png
    # /absolute/path/to/image.gif"""
    assert extract_image_paths(content) == [
        "/home/user/images/photo1.jpg",
        "/home/user/images/photo2.png",
        "/absolute/path/to/image.gif",
    ]

    content = "no image path"
    assert not extract_image_paths(content)


def test_extract_and_encode_images():
    assert not extract_and_encode_images("a non-existing.jpg")


class TestSSRFSecurity:
    """Test SSRF prevention in URL validation"""
    
    def test_is_safe_url_public_urls(self):
        """Test that legitimate public URLs are allowed"""
        safe_urls = [
            "https://example.com/image.jpg",
            "http://www.google.com/logo.png", 
            "https://github.com/user/repo/image.gif",
            "http://8.8.8.8/test.jpg",  # Public DNS
        ]
        for url in safe_urls:
            assert is_safe_url(url), f"Public URL should be safe: {url}"

    def test_is_safe_url_blocked_ips(self):
        """Test that internal/private IPs are blocked"""
        blocked_urls = [
            "http://127.0.0.1:8080/image.jpg",     # Localhost
            "http://localhost/test.png",           # Localhost hostname
            "http://10.0.0.1/secret.gif",          # Private network
            "http://192.168.1.1/admin.jpg",        # Private network
            "http://172.16.0.1/internal.png",      # Private network
            "http://169.254.169.254/metadata",     # Cloud metadata
            "http://[::1]/test.jpg",               # IPv6 localhost
        ]
        for url in blocked_urls:
            assert not is_safe_url(url), f"Internal/private URL should be blocked: {url}"

    def test_is_safe_url_invalid_schemes(self):
        """Test that non-HTTP(S) schemes are blocked"""
        invalid_schemes = [
            "ftp://example.com/file.jpg",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:image/png;base64,abc123",
        ]
        for url in invalid_schemes:
            assert not is_safe_url(url), f"Invalid scheme should be blocked: {url}"

    def test_is_safe_url_malformed_urls(self):
        """Test that malformed URLs are blocked"""
        malformed_urls = [
            "not-a-url",
            "http://",
            "",
            "https://",
        ]
        for url in malformed_urls:
            assert not is_safe_url(url), f"Malformed URL should be blocked: {url}"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
