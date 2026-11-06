#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the accessibility tree parser used by the Browser tool."""
from metagpt.utils.a11y_tree import parse_accessibility_tree


def _cdp_node(node_id: int, role: str, name: str, child_ids: tuple = (), **extra):
    """Build a node shaped like the CDP `Accessibility.getFullAXTree` payload.

    `get_accessibility_tree` stores these raw nodes in `Browser.accessibility_tree`, so this is
    exactly what `parse_accessibility_tree` receives at runtime.
    """
    node = {
        "nodeId": str(node_id),
        "backendDOMNodeId": node_id,
        "role": {"value": role},
        "name": {"value": name},
        "properties": [],
        "childIds": [str(child_id) for child_id in child_ids],
    }
    node.update(extra)
    return node


def test_parse_accessibility_tree_keeps_node_hierarchy():
    tree = [
        _cdp_node(1, "RootWebArea", "Example", child_ids=(2,)),
        _cdp_node(2, "button", "Submit", child_ids=(3,)),
        _cdp_node(3, "StaticText", "OK"),
    ]

    text, node_info = parse_accessibility_tree(tree)

    assert text.splitlines() == [
        "[1] RootWebArea 'Example'",
        "\t[2] button 'Submit'",
        "\t\t[3] StaticText 'OK'",
    ]
    assert node_info == {
        "1": {"backend_id": 1, "union_bound": None, "text": "[1] RootWebArea 'Example'"},
        "2": {"backend_id": 2, "union_bound": None, "text": "[2] button 'Submit'"},
        "3": {"backend_id": 3, "union_bound": None, "text": "[3] StaticText 'OK'"},
    }


def test_parse_accessibility_tree_reads_union_bound_when_present():
    tree = [_cdp_node(1, "button", "Submit", union_bound=[0, 0, 10, 10])]

    _, node_info = parse_accessibility_tree(tree)

    assert node_info["1"]["union_bound"] == [0, 0, 10, 10]


def test_parse_accessibility_tree_skips_empty_generic_nodes():
    tree = [
        _cdp_node(1, "RootWebArea", "Example", child_ids=(2, 3)),
        _cdp_node(2, "generic", ""),
        _cdp_node(3, "button", "Submit"),
    ]

    _, node_info = parse_accessibility_tree(tree)

    assert set(node_info) == {"1", "3"}
