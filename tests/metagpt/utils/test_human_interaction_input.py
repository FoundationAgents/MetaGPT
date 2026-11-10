#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression test for `HumanInteraction.multilines_input`."""
from metagpt.utils.human_interaction import HumanInteraction


def test_multilines_input_keeps_line_breaks(mocker):
    """A multi-line answer must keep its line breaks instead of being glued together."""
    lines = iter(["first line", "second line"])

    def multiline_input(*args, **kwargs):
        try:
            return next(lines)
        except StopIteration:  # Ctrl-D / Ctrl-Z ends the input
            raise EOFError

    mocker.patch("builtins.input", multiline_input)

    assert HumanInteraction().multilines_input() == "first line\nsecond line"
