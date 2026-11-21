#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the implement of serialization and deserialization

import copy
import pickle
import re

from metagpt.utils.common import import_class


SCHEMA_TYPE_TO_PY_TYPE = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
}

PY_TYPE_TO_MAPPING_STR = {py_type.__name__: py_type for py_type in SCHEMA_TYPE_TO_PY_TYPE.values()}
BUILTIN_TYPE_MAPPING_PATTERN = re.compile(r"^\(<class '(?P<name>[A-Za-z_][A-Za-z0-9_]*)'>, Ellipsis\)$")


def actionoutout_schema_to_mapping(schema: dict) -> dict:
    """
    directly traverse the `properties` in the first level.
    schema structure likes
    ```
    {
        "title":"prd",
        "type":"object",
        "properties":{
            "Original Requirements":{
                "title":"Original Requirements",
                "type":"string"
            },
        },
        "required":[
            "Original Requirements",
        ]
    }
    ```
    """
    mapping = dict()
    for field, property in schema["properties"].items():
        type_ = property.get("type")
        if type_ == "array":
            item_type = property.get("items", {}).get("type")
            if item_type == "array":
                # here only consider the `list[list[str]]` situation
                mapping[field] = (list[list[str]], ...)
            elif item_type in SCHEMA_TYPE_TO_PY_TYPE:
                mapping[field] = (list[SCHEMA_TYPE_TO_PY_TYPE[item_type]], ...)
        elif type_ in SCHEMA_TYPE_TO_PY_TYPE:
            mapping[field] = (SCHEMA_TYPE_TO_PY_TYPE[type_], ...)
    return mapping


def actionoutput_mapping_to_str(mapping: dict) -> dict:
    new_mapping = {}
    for key, value in mapping.items():
        new_mapping[key] = str(value)
    return new_mapping


def actionoutput_str_to_mapping(mapping: dict) -> dict:
    new_mapping = {}
    for key, value in mapping.items():
        builtin_type = BUILTIN_TYPE_MAPPING_PATTERN.match(value)
        # `"(<class 'str'>, Ellipsis)"` is not valid python syntax, so resolve builtin types by name
        if builtin_type and builtin_type.group("name") in PY_TYPE_TO_MAPPING_STR:
            new_mapping[key] = (PY_TYPE_TO_MAPPING_STR[builtin_type.group("name")], ...)
        else:
            new_mapping[key] = eval(value)  # `"'(list[str], Ellipsis)"` to `(list[str], ...)`
    return new_mapping


def serialize_message(message: "Message"):
    message_cp = copy.deepcopy(message)  # avoid `instruct_content` value update by reference
    ic = message_cp.instruct_content
    if ic:
        # model create by pydantic create_model like `pydantic.main.prd`, can't pickle.dump directly
        schema = ic.model_json_schema()
        mapping = actionoutout_schema_to_mapping(schema)

        message_cp.instruct_content = {"class": schema["title"], "mapping": mapping, "value": ic.model_dump()}
    msg_ser = pickle.dumps(message_cp)

    return msg_ser


def deserialize_message(message_ser: str) -> "Message":
    message = pickle.loads(message_ser)
    if message.instruct_content:
        ic = message.instruct_content
        actionnode_class = import_class("ActionNode", "metagpt.actions.action_node")  # avoid circular import
        ic_obj = actionnode_class.create_model_class(class_name=ic["class"], mapping=ic["mapping"])
        ic_new = ic_obj(**ic["value"])
        message.instruct_content = ic_new

    return message
