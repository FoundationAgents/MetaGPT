import pytest

from metagpt.actions.talk_action import TalkAction
from metagpt.configs.models_config import ModelsConfig
from metagpt.const import METAGPT_ROOT, TEST_DATA_PATH
from metagpt.utils.common import aread, awrite


@pytest.mark.asyncio
async def test_models_configs(context):
    default_model = ModelsConfig.default()
    assert default_model is not None

    models = ModelsConfig.from_yaml_file(TEST_DATA_PATH / "config/config2.yaml")
    assert models

    default_models = ModelsConfig.default()
    backup = ""
    if not default_models.models:
        backup = await aread(filename=METAGPT_ROOT / "config/config2.yaml")
        test_data = await aread(filename=TEST_DATA_PATH / "config/config2.yaml")
        await awrite(filename=METAGPT_ROOT / "config/config2.yaml", data=test_data)

    try:
        action = TalkAction(context=context, i_context="who are you?", llm_name_or_type="YOUR_MODEL_NAME_1")
        assert action.private_llm.config.model == "YOUR_MODEL_NAME_1"
        assert context.config.llm.model != "YOUR_MODEL_NAME_1"
    finally:
        if backup:
            await awrite(filename=METAGPT_ROOT / "config/config2.yaml", data=backup)


def test_models_config_get_by_name_or_api_type():
    models = ModelsConfig(
        models={
            "my-claude": {"api_type": "anthropic", "api_key": "sk-ant", "model": "claude-sonnet"},
            "my-gpt": {"api_type": "openai", "api_key": "sk-oai", "model": "gpt-4o"},
        }
    )

    # Lookup by model name
    assert models.get("my-claude").model == "claude-sonnet"
    assert models.get("my-gpt").model == "gpt-4o"

    # Lookup by API type, as documented for `Action.llm_name_or_type`
    assert models.get("anthropic").model == "claude-sonnet"
    assert models.get("openai").model == "gpt-4o"

    # Unknown names/types and empty input still return None
    assert models.get("does-not-exist") is None
    assert models.get("") is None
    assert models.get(None) is None


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
