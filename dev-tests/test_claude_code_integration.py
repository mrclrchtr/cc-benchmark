#!/usr/bin/env python3
"""
Comprehensive test suite for Claude Code integration validation.

This script consolidates all dev-test functionality into essential tests:
1. SDK direct usage test
2. Wrapper functionality test
3. End-to-end benchmark integration test
4. Metrics validation test

Use this for:
- Validating Claude Code setup after environment changes
- Testing wrapper modifications
- Debugging metrics flow issues
- Regression testing before benchmark runs
"""

import asyncio
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add benchmark directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "benchmark"))

from claude_code_sdk import query, ClaudeCodeOptions
from cc_wrapper import ClaudeCodeWrapper


def test_sdk_direct():
    """Test 1: Direct SDK usage to verify authentication and basic functionality."""
    print("=== Test 1: SDK Direct Usage ===")
    
    async def run_sdk_test():
        options = ClaudeCodeOptions(
            max_turns=1,
            permission_mode="acceptEdits",
            cwd=Path.cwd()
        )
        
        message_count = 0
        cost = 0
        tokens = 0
        
        try:
            async for message in query(prompt="Calculate 10 + 15", options=options):
                message_count += 1
                msg_type = type(message).__name__
                
                if msg_type == 'ResultMessage':
                    cost = getattr(message, 'total_cost_usd', 0)
                    usage = getattr(message, 'usage', {})
                    tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                    
            success = cost > 0 and tokens > 0
            print(f"✅ SDK Test: {'PASS' if success else 'FAIL'}")
            print(f"   Messages: {message_count}, Cost: ${cost:.6f}, Tokens: {tokens}")
            return success
            
        except Exception as e:
            print(f"❌ SDK Test: FAIL - {e}")
            return False
    
    return asyncio.run(run_sdk_test())


def test_wrapper_functionality():
    """Test 2: Wrapper functionality and metrics extraction."""
    print("\n=== Test 2: Wrapper Functionality ===")
    
    try:
        wrapper = ClaudeCodeWrapper(verbose=False)
        
        # Test basic execution
        result = wrapper.run("What is 20 + 25?")
        
        success = (
            wrapper.total_cost > 0 and
            wrapper.total_tokens_sent > 0 and
            wrapper.total_tokens_received > 0 and
            len(result.strip()) > 0
        )
        
        print(f"✅ Wrapper Test: {'PASS' if success else 'FAIL'}")
        print(f"   Cost: ${wrapper.total_cost:.6f}")
        print(f"   Tokens: {wrapper.total_tokens_sent} in, {wrapper.total_tokens_received} out")
        print(f"   Result: {result[:50]}...")
        
        return success
        
    except Exception as e:
        print(f"❌ Wrapper Test: FAIL - {e}")
        return False


def test_benchmark_integration():
    """Test 3: End-to-end integration simulating benchmark.py usage."""
    print("\n=== Test 3: Benchmark Integration ===")
    
    try:
        # Create temporary test directory
        temp_dir = Path(tempfile.mkdtemp()) / "integration-test"
        temp_dir.mkdir()
        
        # Create simple Python exercise
        (temp_dir / "math_utils.py").write_text('''
def multiply(a, b):
    """Multiply two numbers."""
    pass  # TODO: implement
''')
        
        (temp_dir / "test_math_utils.py").write_text('''
from math_utils import multiply

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6
''')
        
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create wrapper and run exercise
            wrapper = ClaudeCodeWrapper(verbose=False)
            result = wrapper.run("Implement the multiply function in math_utils.py to make the tests pass")
            
            # Simulate benchmark.py results creation
            results = {
                "cost": wrapper.total_cost,
                "prompt_tokens": wrapper.total_tokens_sent,
                "completion_tokens": wrapper.total_tokens_received,
                "thinking_tokens": getattr(wrapper, 'total_thinking_tokens', 0),
                "model": "claude-sonnet-4-0",
                "test_outcome": "simulated"
            }
            
            # Write results JSON like benchmark does
            with open(".aider.results.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            # Validate integration
            success = (
                results["cost"] > 0 and
                results["prompt_tokens"] > 0 and
                results["completion_tokens"] > 0 and
                Path(".aider.results.json").exists()
            )
            
            print(f"✅ Integration Test: {'PASS' if success else 'FAIL'}")
            print(f"   JSON Results: cost=${results['cost']:.6f}, tokens={results['prompt_tokens']}+{results['completion_tokens']}")
            
            # Check if code was actually modified
            modified_code = (temp_dir / "math_utils.py").read_text()
            if "return a * b" in modified_code or "a*b" in modified_code:
                print("   ✅ Code modification detected")
            else:
                print("   ⚠️  Code modification not detected")
            
            return success
            
        finally:
            os.chdir(original_dir)
            shutil.rmtree(temp_dir.parent, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Integration Test: FAIL - {e}")
        return False


def test_metrics_validation():
    """Test 4: Metrics validation and accuracy."""
    print("\n=== Test 4: Metrics Validation ===")
    
    try:
        # Test 1: Single wrapper with multiple queries (should accumulate)
        wrapper = ClaudeCodeWrapper(verbose=False)
        
        # First query
        wrapper.run("Calculate 10 + 20")
        first_cost = wrapper.total_cost
        first_tokens = wrapper.total_tokens_sent + wrapper.total_tokens_received
        
        # Second query on same wrapper (should accumulate)
        wrapper.run("Calculate 15 + 25") 
        second_cost = wrapper.total_cost
        second_tokens = wrapper.total_tokens_sent + wrapper.total_tokens_received
        
        # Test 2: Fresh wrapper (should start from zero)
        fresh_wrapper = ClaudeCodeWrapper(verbose=False)
        fresh_wrapper.run("Calculate 5 + 8")
        fresh_cost = fresh_wrapper.total_cost
        fresh_tokens = fresh_wrapper.total_tokens_sent + fresh_wrapper.total_tokens_received
        
        # Validate metrics are reasonable
        all_positive = (first_cost > 0 and second_cost > 0 and fresh_cost > 0 and 
                       first_tokens > 0 and second_tokens > 0 and fresh_tokens > 0)
        costs_accumulate = second_cost > first_cost  # Should accumulate within wrapper
        fresh_starts_clean = fresh_cost < second_cost  # Fresh wrapper should start lower
        
        success = all_positive and costs_accumulate and fresh_starts_clean
        
        print(f"✅ Metrics Test: {'PASS' if success else 'FAIL'}")
        print(f"   First query: ${first_cost:.6f}, {first_tokens} tokens")
        print(f"   Second query: ${second_cost:.6f}, {second_tokens} tokens") 
        print(f"   Fresh wrapper: ${fresh_cost:.6f}, {fresh_tokens} tokens")
        print(f"   Accumulation: {'✅' if costs_accumulate else '❌'}")
        print(f"   Fresh isolation: {'✅' if fresh_starts_clean else '❌'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Metrics Test: FAIL - {e}")
        return False


def main():
    """Run all integration tests."""
    print("Claude Code Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("SDK Direct", test_sdk_direct),
        ("Wrapper", test_wrapper_functionality),
        ("Integration", test_benchmark_integration),
        ("Metrics", test_metrics_validation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} Test: ERROR - {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    passed = 0
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("✅ All tests passed - Claude Code integration is working correctly")
        return True
    else:
        print("❌ Some tests failed - check Claude Code setup and authentication")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)