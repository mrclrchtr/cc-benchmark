#!/usr/bin/env python3
"""Test that our model constants are in sync with Anthropic SDK."""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from typing import Set, List

from tests.model_sync_checker import ModelSyncChecker


@pytest.mark.model_sync
class TestModelSync:
    """Test cases for model synchronization with Anthropic SDK."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ModelSyncChecker()
    
    @pytest.mark.requires_anthropic
    def test_anthropic_sdk_available(self):
        """Test that Anthropic SDK is available for comparison."""
        anthropic_models = self.checker._get_anthropic_models()
        assert anthropic_models is not None, "Anthropic SDK should be available"
        assert isinstance(anthropic_models, list), "Should return a list of models"
        assert len(anthropic_models) > 0, "Should have at least some models"
    
    @pytest.mark.unit
    def test_our_models_exist(self):
        """Test that our model constants are properly defined."""
        our_models = self.checker._get_our_models()
        
        assert isinstance(our_models, list), "Should return a list of models"
        assert len(our_models) > 0, "Should have at least some models"
        
        # Check that all models follow Claude naming convention
        for model in our_models:
            assert model.startswith("claude-"), f"Model {model} should start with 'claude-'"
            assert len(model) > 10, f"Model {model} seems too short"
    
    @pytest.mark.integration
    @pytest.mark.requires_anthropic
    def test_models_in_sync(self):
        """Test that our models are in sync with Anthropic SDK."""
        result = self.checker.check_for_changes(verbose=False)
        
        # Skip if Anthropic SDK not available
        if not result["anthropic_available"]:
            pytest.skip("Anthropic SDK not available - cannot test sync")
        
        # Assert no changes detected
        assert not result["changes_detected"], self._format_sync_error(result)
    
    @pytest.mark.unit
    def test_no_duplicate_models(self):
        """Test that we don't have duplicate model definitions."""
        our_models = self.checker._get_our_models()
        model_set = set(our_models)
        
        assert len(our_models) == len(model_set), f"Duplicate models found: {[m for m in our_models if our_models.count(m) > 1]}"
    
    @pytest.mark.unit
    def test_model_format_consistency(self):
        """Test that all model IDs follow consistent naming patterns."""
        our_models = self.checker._get_our_models()
        
        for model in our_models:
            # Check basic format: claude-{family}-{version}-{date} or claude-{family}-{version}
            parts = model.split('-')
            assert len(parts) >= 3, f"Model {model} should have at least 3 parts separated by dashes"
            assert parts[0] == "claude", f"Model {model} should start with 'claude'"
            assert parts[1] in ["3", "sonnet", "haiku", "opus", "4"], f"Model {model} has unknown family: {parts[1]}"
    
    
    def _format_sync_error(self, result: dict) -> str:
        """Format a helpful error message when models are out of sync."""
        error_lines = [
            "❌ Models are OUT OF SYNC with Anthropic SDK!",
            f"   Our models: {result['our_models_count']}",
            f"   Anthropic models: {result['anthropic_models_count']}",
            ""
        ]
        
        if result["new_models"]:
            error_lines.extend([
                f"🆕 NEW MODELS ({len(result['new_models'])}):",
                *[f"   + {model}" for model in result["new_models"]],
                ""
            ])
        
        if result["removed_models"]:
            error_lines.extend([
                f"🗑️  REMOVED MODELS ({len(result['removed_models'])}):",
                *[f"   - {model}" for model in result["removed_models"]],
                ""
            ])
        
        if result["recommendations"]:
            error_lines.extend([
                "💡 TO FIX:",
                *[f"   {i+1}. {rec}" for i, rec in enumerate(result["recommendations"])]
            ])
        
        return "\n".join(error_lines)


# Standalone test runner for CI/CD integration
@pytest.mark.integration
@pytest.mark.requires_anthropic
def test_model_sync_cli():
    """Standalone function that can be called from CLI or pytest."""
    checker = ModelSyncChecker()
    result = checker.check_for_changes(verbose=True)
    
    if not result["anthropic_available"]:
        print("⚠️  Anthropic SDK not available - skipping model sync test")
        print("   Install with: uv add anthropic")
        pytest.skip("Anthropic SDK not available")
    
    if result["changes_detected"]:
        print("\n" + "="*60)
        print("❌ MODEL SYNC TEST FAILED")
        print("="*60)
        pytest.fail("Models are out of sync with Anthropic SDK")
    else:
        print("\n" + "="*60)
        print("✅ MODEL SYNC TEST PASSED")
        print("="*60)


if __name__ == "__main__":
    """Run as standalone test for CI/CD pipelines."""
    import sys
    
    try:
        checker = ModelSyncChecker()
        result = checker.check_for_changes(verbose=True)
        
        if not result["anthropic_available"]:
            print("⚠️  Anthropic SDK not available - skipping model sync test")
            print("   Install with: uv add anthropic")
            sys.exit(0)  # Don't fail if optional dependency missing
        
        if result["changes_detected"]:
            print("\n" + "="*60)
            print("❌ MODEL SYNC TEST FAILED")
            print("="*60)
            sys.exit(1)
        else:
            print("\n" + "="*60)
            print("✅ MODEL SYNC TEST PASSED")
            print("="*60)
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error running model sync test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)