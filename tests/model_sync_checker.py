#!/usr/bin/env python3
"""Model synchronization checker to detect changes in Anthropic SDK models."""
from typing import Dict, List, Set, Optional
from datetime import datetime

# Required dependency for model synchronization
from anthropic.types import Model

# Import our local models for comparison
from benchmark.models import ClaudeModel


class ModelSyncChecker:
    """Checks for changes between our model constants and Anthropic SDK."""
    
    def _get_anthropic_models(self) -> Optional[List[str]]:
        """Extract model identifiers from Anthropic SDK."""
            
        try:
            # Get all model constants from Model type
            # This is a union type, so we need to extract the literal values
            import typing
            
            # Get the union arguments (model string literals)
            if hasattr(Model, '__args__'):
                model_literals = []
                for arg in Model.__args__:
                    if hasattr(arg, '__args__'):  # Literal type
                        model_literals.extend(arg.__args__)
                    elif isinstance(arg, str):
                        model_literals.append(arg)
                return sorted(list(set(model_literals)))
            else:
                # Fallback: try to get from type annotations
                return None
                
        except Exception as e:
            print(f"⚠️  Could not extract Anthropic models: {e}")
            return None
    
    def _get_our_models(self) -> List[str]:
        """Get our current model constants from ClaudeModel enum."""
        return sorted([model.value for model in ClaudeModel])
    
    
    def check_for_changes(self, verbose: bool = True) -> Dict:
        """Check for changes in model lists."""
        check_time = datetime.now().isoformat()
        result = {
            "timestamp": check_time,
            "anthropic_available": True,
            "changes_detected": False,
            "new_models": [],
            "removed_models": [],
            "our_models_count": len(self._get_our_models()),
            "anthropic_models_count": 0,
            "recommendations": []
        }
        
        if verbose:
            print("🔍 MODEL SYNC CHECK")
            print("=" * 30)
            print(f"Timestamp: {check_time}")
        
        our_models = set(self._get_our_models())
        anthropic_models = self._get_anthropic_models()
        
        if anthropic_models is None:
            if verbose:
                print("⚠️  Anthropic SDK not available - cannot check for changes")
                print("   Install with: uv add anthropic")
            result["recommendations"].append("Install Anthropic SDK to enable model sync checking")
            return result
        
        anthropic_models_set = set(anthropic_models)
        result["anthropic_models_count"] = len(anthropic_models)
        
        if verbose:
            print(f"📊 Our models: {len(our_models)}")
            print(f"📊 Anthropic models: {len(anthropic_models)}")
        
        # Check for changes
        new_models = anthropic_models_set - our_models
        removed_models = our_models - anthropic_models_set
        
        result["new_models"] = sorted(list(new_models))
        result["removed_models"] = sorted(list(removed_models))
        result["changes_detected"] = bool(new_models or removed_models)
        
        if verbose:
            if result["changes_detected"]:
                print("🚨 CHANGES DETECTED!")
                
                if new_models:
                    print(f"\n✅ NEW MODELS ({len(new_models)}):")
                    for model in sorted(new_models):
                        print(f"   + {model}")
                        
                if removed_models:
                    print(f"\n❌ REMOVED MODELS ({len(removed_models)}):")
                    for model in sorted(removed_models):
                        print(f"   - {model}")
                        
                result["recommendations"].extend([
                    "Add new enum members to ClaudeModel class in models.py",
                    "Update cost estimation logic if needed",
                    "Test updated models with cc_wrapper"
                ])
                
            else:
                print("✅ No changes detected - models are in sync!")
        
        if verbose:
            if result["recommendations"]:
                print(f"\n💡 RECOMMENDATIONS:")
                for i, rec in enumerate(result["recommendations"], 1):
                    print(f"   {i}. {rec}")
        
        return result
    
    def get_sync_status(self) -> Dict:
        """Get current sync status without checking for changes."""
        our_models = self._get_our_models()
        return {
            "our_models_count": len(our_models),
            "anthropic_available": True
        }
    
    def generate_update_guide(self) -> str:
        """Generate a guide for updating models after changes are detected."""
        guide = """
# Model Update Guide

When new models are detected in Anthropic SDK:

## 1. Add new enum members
Add new models directly to the ClaudeModel enum in models.py:
```python
class ClaudeModel(Enum):
    # Add new models here
    NEW_MODEL_NAME = "claude-new-model-id"
```

## 2. Update cost estimation
Check if new models need different pricing in cc_wrapper.py:
```python
def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
    # Add pricing for new model families
```

## 3. Update common name mappings
Add user-friendly aliases in from_common_name() and get_available_models().

## 4. Test the changes
Run the model sync checker again to verify sync:
```bash
python tests/model_sync_checker.py
```
"""
        return guide


def main():
    """Main CLI interface for model sync checking."""
    # Validate Anthropic models dependency
    from benchmark.deps import validate_anthropic_models
    validate_anthropic_models()
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Check for changes in Anthropic model list")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--status", "-s", action="store_true", help="Show sync status only")
    parser.add_argument("--guide", "-g", action="store_true", help="Show update guide")
    
    args = parser.parse_args()
    
    checker = ModelSyncChecker()
    
    if args.guide:
        print(checker.generate_update_guide())
        return
    
    if args.status:
        status = checker.get_sync_status()
        print(f"Our models: {status['our_models_count']}")
        print(f"Anthropic SDK: {'Available' if status['anthropic_available'] else 'Not available'}")
        return
    
    # Run full check
    result = checker.check_for_changes(verbose=args.verbose)
    
    if result["changes_detected"]:
        exit_code = 1  # Non-zero exit for CI/CD detection
    else:
        exit_code = 0
        
    return exit_code


if __name__ == "__main__":
    exit(main())