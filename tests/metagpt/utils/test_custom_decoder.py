#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/8 11:38
@Author  : femto Zheng
@File    : test_custom_decoder.py
"""

import pytest

from metagpt.utils.custom_decoder import CustomDecoder


def test_parse_single_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = """{'a"
    b':'"title": "Reach and engagement of campaigns",
            "x-axis": "Low Reach --> High Reach",
            "y-axis": "Low Engagement --> High Engagement",
            "quadrant-1": "We should expand",
            "quadrant-2": "Need to promote",
            "quadrant-3": "Re-evaluate",
            "quadrant-4": "May be improved",
            "Campaign: A": [0.3, 0.6],
            "Campaign B": [0.45, 0.23],
            "Campaign C": [0.57, 0.69],
            "Campaign D": [0.78, 0.34],
            "Campaign E": [0.40, 0.34],
            "Campaign F": [0.35, 0.78],
            "Our Target Product": [0.5, 0.6]
            '
        }
    """
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert 'a"\n    b' in parsed_data

    input_data = """{
    'a': "
    b
"
}
"""
    # Before the fix this raised at the key boundary because the single-quoted
    # key was rejected; it now parses the same way as the double-quoted key
    # variant in test_parse_double_quote.
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "\n    b\n"

    input_data = """{
    'a': '
    b
'
}
"""
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "\n    b\n"


def test_parse_double_quote():
    decoder = CustomDecoder(strict=False)

    input_data = """{
    "a": "
    b
"
}
"""
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "\n    b\n"

    input_data = """{
    "a": '
    b
'
}
"""
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "\n    b\n"


def test_parse_triple_double_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = '{"""a""":"b"}'
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert "a" in parsed_data

    input_data = '{"""a""":"""b"""}'
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"

    input_data = "{\"\"\"a\"\"\": '''b'''}"
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"


def test_parse_triple_single_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = "{'''a''':'b'}"
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert "a" in parsed_data

    input_data = "{'''a''':'''b'''}"
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"


def test_single_quoted_keys_after_comma():
    """Regression for https://github.com/FoundationAgents/MetaGPT/issues/2187:
    a single-quoted key after a comma (and after leading whitespace) must be
    accepted, consistent with the first-key handling."""
    decoder = CustomDecoder()

    assert decoder.decode("{'name': 'MetaGPT', 'role': 'Engineer'}") == {
        "name": "MetaGPT",
        "role": "Engineer",
    }
    assert decoder.decode("{ 'step': 1 }") == {"step": 1}
    # mixed quote delimiters keep working
    assert decoder.decode('{"a": 1, \'b\': "two"}') == {"a": 1, "b": "two"}
    # nested objects
    assert decoder.decode("{'outer': {'inner': 'v'}, 'n': 2}") == {
        "outer": {"inner": "v"},
        "n": 2,
    }
    # invalid key boundaries still raise
    with pytest.raises(Exception):
        decoder.decode("{name: 1}")
    with pytest.raises(Exception):
        decoder.decode("{'a': 1, name: 2}")
