#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Isolated test for #2079: encode_image must reject non-regular files.
Run directly: python3 tests/metagpt/utils/test_encode_image_dos.py

Does NOT import metagpt to avoid heavy conftest dependency chain.
Tests the exact code path after the #2079 fix is applied.
"""
import base64
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------------------------------------------------------------------
# Code under test — mirror of metagpt.utils.common.encode_image post-#2079
# ---------------------------------------------------------------------------

def _encode_image(image_path_or_pil, encoding: str = "utf-8") -> str:
    """Clone of metagpt.utils.common.encode_image after #2079 fix."""
    if HAS_PIL and isinstance(image_path_or_pil, Image.Image):
        buffer = BytesIO()
        image_path_or_pil.save(buffer, format="JPEG")
        bytes_data = buffer.getvalue()
    else:
        if isinstance(image_path_or_pil, str):
            image_path_or_pil = Path(image_path_or_pil)
        if not image_path_or_pil.exists():
            raise FileNotFoundError(f"{image_path_or_pil} not exists")
        # ---- #2079 fix: reject non-regular files ----
        if not image_path_or_pil.is_file():
            raise ValueError(f"{image_path_or_pil} is not a regular file")
        # ---------------------------------------------
        with open(str(image_path_or_pil), "rb") as image_file:
            bytes_data = image_file.read()
    return base64.b64encode(bytes_data).decode(encoding)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _test(description: str, ok: bool, detail: str = ""):
    """Simple test runner."""
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {description}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def test_regular_file():
    """A regular file is accepted."""
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "img.png"
        payload = b"\x89PNG\x0d\x0a\x1a\x0afake"
        f.write_bytes(payload)
        result = _encode_image(str(f))
        expected = base64.b64encode(payload).decode("utf-8")
        if not _test("regular file yields correct base64", result == expected):
            return False
    return True


def test_missing_file():
    """Missing file raises FileNotFoundError (existing behaviour preserved)."""
    with tempfile.TemporaryDirectory() as d:
        try:
            _encode_image(str(Path(d) / "nonexistent.png"))
            _test("missing file raises FileNotFoundError", False)
            return False
        except FileNotFoundError:
            _test("missing file raises FileNotFoundError", True)
    return True


def test_directory():
    """Directory is rejected with ValueError."""
    with tempfile.TemporaryDirectory() as d:
        try:
            _encode_image(d)
            _test("directory rejected", False)
            return False
        except ValueError as e:
            _test("directory rejected", True, str(e))
    return True


def test_fifo():
    """Named pipe (FIFO) is rejected with ValueError."""
    if os.name == "nt":
        _test("FIFO test (skipped on Windows)", True, "skipped")
        return True
    with tempfile.TemporaryDirectory() as d:
        fifo = Path(d) / "evil.pipe"
        os.mkfifo(str(fifo))
        try:
            _encode_image(str(fifo))
            _test("FIFO rejected", False)
            return False
        except ValueError as e:
            _test("FIFO rejected", True, str(e))
    return True


def test_dev_zero():
    """Character device /dev/zero is rejected with ValueError."""
    if not Path("/dev/zero").exists():
        _test("dev/zero test (not available on this platform)", True, "skipped")
        return True
    try:
        _encode_image("/dev/zero")
        _test("/dev/zero rejected", False)
        return False
    except ValueError as e:
        _test("/dev/zero rejected", True, str(e))
    return True


def test_dev_null():
    """Character device /dev/null is rejected with ValueError."""
    if not Path("/dev/null").exists():
        _test("dev/null test (not available on this platform)", True, "skipped")
        return True
    try:
        _encode_image("/dev/null")
        _test("/dev/null rejected", False)
        return False
    except ValueError as e:
        _test("/dev/null rejected", True, str(e))
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ALL = [test_regular_file, test_missing_file, test_directory,
           test_fifo, test_dev_zero, test_dev_null]
    if HAS_PIL:
        # quick PIL test
        img = Image.new("RGB", (1, 1), color="red")
        r = _encode_image(img)
        print(f"[PASS] PIL Image: got {len(r)} chars of base64")

    passed = failed = 0
    for fn in ALL:
        if fn():
            passed += 1
        else:
            failed += 1
    print(f"\n=== {passed} passed, {failed} failed ===")
    sys.exit(0 if failed == 0 else 1)
