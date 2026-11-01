from pathlib import Path

import pytest
import yaml

from metagpt.utils.yaml_model import YamlModel


class ExampleConfig(YamlModel):
    name: str = "default"


@pytest.mark.parametrize("content", ["", " \n  \n", "# No overrides\n", "---\n# No overrides\n"])
def test_empty_yaml_uses_model_defaults(tmp_path: Path, content: str):
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")

    assert ExampleConfig.read_yaml(path) == {}
    assert ExampleConfig.from_yaml_file(path).name == "default"


def test_missing_yaml_uses_model_defaults(tmp_path: Path):
    assert ExampleConfig.from_yaml_file(tmp_path / "missing.yaml").name == "default"


def test_yaml_values_override_model_defaults(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("name: configured\n", encoding="utf-8")

    assert ExampleConfig.from_yaml_file(path).name == "configured"


def test_invalid_yaml_is_not_treated_as_empty(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("name: [\n", encoding="utf-8")

    with pytest.raises(yaml.YAMLError):
        ExampleConfig.read_yaml(path)
