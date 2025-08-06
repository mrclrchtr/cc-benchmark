"""Claude Code model definitions and utilities."""
from enum import Enum, unique
from typing import Dict, List, Optional

# Model validation moved to tests/model_sync_checker.py


@unique
class ClaudeModel(Enum):
    """Claude Code model identifiers sourced from official Anthropic SDK."""
    
    # Claude 4 Sonnet Models (newest)
    SONNET_4 = "claude-sonnet-4-0"
    SONNET_4_LATEST = "claude-sonnet-4-20250514"
    SONNET_4_ALT = "claude-4-sonnet-20250514"  # Alternative naming
    
    # Claude 3.7 Sonnet Models (newer)  
    SONNET_3_7_LATEST = "claude-3-7-sonnet-latest"
    SONNET_3_7_20250219 = "claude-3-7-sonnet-20250219"
    
    # Claude 3.5 Sonnet Models  
    SONNET_3_5_LATEST = "claude-3-5-sonnet-latest"
    SONNET_3_5_20241022 = "claude-3-5-sonnet-20241022"
    SONNET_3_5_20240620 = "claude-3-5-sonnet-20240620"
    
    # Claude 3.5 Haiku Models
    HAIKU_3_5_LATEST = "claude-3-5-haiku-latest"
    HAIKU_3_5_20241022 = "claude-3-5-haiku-20241022"
    
    # Claude 3 Legacy Models
    HAIKU_3_20240307 = "claude-3-haiku-20240307"
    OPUS_3_LATEST = "claude-3-opus-latest"
    OPUS_3_20240229 = "claude-3-opus-20240229"
    
    # Claude 4 Opus Models
    OPUS_4 = "claude-opus-4-0"
    OPUS_4_LATEST = "claude-opus-4-20250514"
    OPUS_4_ALT = "claude-4-opus-20250514"  # Alternative naming
    OPUS_4_1_20250805 = "claude-opus-4-1-20250805"

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
        """Resolve common model names to specific model instances."""
        name_lower = name.lower()
        
        # Map common names to preferred models (using latest versions)
        if name_lower == "sonnet":
            return cls.SONNET_4  # Default to Claude 4 Sonnet
        elif name_lower in ("sonnet-4", "sonnet4"):
            return cls.SONNET_4
        elif name_lower in ("sonnet-3.5", "sonnet3.5"):
            return cls.SONNET_3_5_LATEST
        elif name_lower == "haiku":
            return cls.HAIKU_3_5_LATEST  # Default to 3.5 Haiku
        elif name_lower in ("haiku-3.5", "haiku3.5"):
            return cls.HAIKU_3_5_LATEST
        elif name_lower == "opus":
            return cls.OPUS_4  # Default to Claude 4 Opus
        elif name_lower in ("opus-4", "opus4"):
            return cls.OPUS_4
        elif name_lower in ("opus-3", "opus3"):
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

    # Add common name aliases (pointing to latest/recommended versions)
    mappings["sonnet"] = ClaudeModel.SONNET_4.value
    mappings["sonnet-4"] = ClaudeModel.SONNET_4.value
    mappings["sonnet-3.5"] = ClaudeModel.SONNET_3_5_LATEST.value
    mappings["haiku"] = ClaudeModel.HAIKU_3_5_LATEST.value
    mappings["haiku-3.5"] = ClaudeModel.HAIKU_3_5_LATEST.value
    mappings["opus"] = ClaudeModel.OPUS_4.value
    mappings["opus-4"] = ClaudeModel.OPUS_4.value
    mappings["opus-3"] = ClaudeModel.OPUS_3_LATEST.value

    return mappings


def print_available_models() -> None:
    """Print all available model mappings in a user-friendly format."""
    print("Available Claude Code Models:")
    print("=" * 50)

    models = get_available_models()

    families = {
        "Claude 4 Sonnet Models (Latest)": [],
        "Claude 3.7 Sonnet Models": [],
        "Claude 3.5 Sonnet Models": [],
        "Claude 3.5 Haiku Models": [],
        "Claude 3 Legacy Models": [],
        "Claude 4 Opus Models": [],
        "Common Name Aliases": [],
    }

    for original, resolved in models.items():
        original_lower = original.lower()
        
        # Categorize by model family and generation
        if original_lower.startswith("claude-sonnet-4") or original_lower == "sonnet":
            families["Claude 4 Sonnet Models (Latest)"].append((original, resolved))
        elif "sonnet" in original_lower and ("3.7" in original_lower or "3-7" in original_lower):
            families["Claude 3.7 Sonnet Models"].append((original, resolved))  
        elif "sonnet" in original_lower and ("3.5" in original_lower or "3-5" in original_lower):
            families["Claude 3.5 Sonnet Models"].append((original, resolved))
        elif "haiku" in original_lower and ("3.5" in original_lower or "3-5" in original_lower):
            families["Claude 3.5 Haiku Models"].append((original, resolved))
        elif ("haiku" in original_lower and "3-" in original_lower) or ("opus" in original_lower and "3-" in original_lower):
            families["Claude 3 Legacy Models"].append((original, resolved))
        elif "opus" in original_lower and ("4" in original_lower or original_lower == "opus"):
            families["Claude 4 Opus Models"].append((original, resolved))
        elif original_lower in ["sonnet", "haiku", "opus", "sonnet-4", "sonnet-3.5", "haiku-3.5", "opus-4", "opus-3"]:
            families["Common Name Aliases"].append((original, resolved))

    for family, mappings in families.items():
        if mappings:
            print(f"\n{family}:")
            for original, resolved in mappings:
                print(f"  {original:<30} -> {resolved}")


if __name__ == "__main__":
    print_available_models()
