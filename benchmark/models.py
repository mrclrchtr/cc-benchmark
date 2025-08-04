"""Claude Code model definitions and utilities."""
from enum import Enum, unique
from typing import Dict, List, Optional


@unique
class ClaudeModel(Enum):
    """Claude Code model identifiers."""

    SONNET_4 = "claude-sonnet-4-0"
    SONNET_3_5_LATEST = "claude-3-5-sonnet-latest"
    HAIKU_3_5_LATEST = "claude-3-5-haiku-latest"
    OPUS_3_LATEST = "claude-3-opus-latest"

    @classmethod
    def get_default(cls) -> 'ClaudeModel':
        return cls.SONNET_4

    @classmethod
    def from_string(cls, model_name: str) -> Optional['ClaudeModel']:
        for model in cls:
            if model.value == model_name:
                return model
        return None

    @classmethod
    def from_common_name(cls, name: str) -> Optional['ClaudeModel']:
        name_lower = name.lower()
        if name_lower == "sonnet":
            return cls.SONNET_4
        elif name_lower == "haiku":
            return cls.HAIKU_3_5_LATEST
        elif name_lower == "opus":
            return cls.OPUS_3_LATEST
        return None

    @classmethod
    def lookup_any(cls, model_name: str) -> Optional['ClaudeModel']:
        model = cls.from_string(model_name)
        if model:
            return model
        model = cls.from_common_name(model_name)
        if model:
            return model
        return None

    @classmethod
    def list_all_ids(cls) -> List[str]:
        return [model.value for model in cls]

    def __str__(self) -> str:
        return self.value


def lookup_model(model_name: str) -> str:
    model = ClaudeModel.lookup_any(model_name)
    if model:
        return model.value

    if model_name.startswith("claude-"):
        return model_name
    available_models = ClaudeModel.list_all_ids() + ["sonnet", "haiku", "opus"]
    raise ValueError(f"Unknown model identifier: {model_name}. Available models: {available_models}")


def get_available_models() -> Dict[str, str]:
    mappings = {}

    # Add full model IDs
    for model in ClaudeModel:
        mappings[model.value] = model.value

    # Add common name aliases
    mappings["sonnet"] = ClaudeModel.SONNET_4.value
    mappings["haiku"] = ClaudeModel.HAIKU_3_5_LATEST.value
    mappings["opus"] = ClaudeModel.OPUS_3_LATEST.value

    return mappings


def print_available_models() -> None:
    """Print all available model mappings in a user-friendly format."""
    print("Available Claude Code Models:")
    print("=" * 50)

    models = get_available_models()

    families = {
        "Sonnet Models": [],
        "Haiku Models": [],
        "Opus Models": [],
    }

    for original, resolved in models.items():
        if "sonnet" in original.lower():
            families["Sonnet Models"].append((original, resolved))
        elif "haiku" in original.lower():
            families["Haiku Models"].append((original, resolved))
        elif "opus" in original.lower():
            families["Opus Models"].append((original, resolved))

    for family, mappings in families.items():
        if mappings:
            print(f"\n{family}:")
            for original, resolved in mappings:
                print(f"  {original:<30} -> {resolved}")


if __name__ == "__main__":
    print_available_models()
