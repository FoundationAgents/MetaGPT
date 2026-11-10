#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for metagpt.utils.parse_docstring."""

from metagpt.utils.parse_docstring import GoogleDocstringParser


def test_parse_docstring_with_args_mentioned_in_the_description():
    """A docstring that mentions "Args:" in prose as well as in the section header must still parse."""
    docstring = (
        "Score a candidate answer.\n\n"
        "Args: the model may mention Args: in prose.\n\n"
        "Args:\n"
        "    answer: the candidate answer to score.\n"
        "    reference: the reference answer.\n"
    )

    overall_desc, param_desc = GoogleDocstringParser.parse(docstring)

    assert "Score a candidate answer." in overall_desc
    assert param_desc.startswith("Args:")
    assert "answer: the candidate answer to score." in param_desc
    assert "reference: the reference answer." in param_desc


def test_parse_docstring_without_args_section():
    overall_desc, param_desc = GoogleDocstringParser.parse("Just a description.")

    assert overall_desc == "Just a description."
    assert param_desc == ""
