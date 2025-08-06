# Development Tests

This directory contains tests for validating Claude Code integration during development.

## Current Tests

### `test_claude_code_integration.py`
**Primary test suite** - Comprehensive validation of Claude Code integration:

1. **SDK Direct Test**: Validates SDK authentication and basic functionality
2. **Wrapper Test**: Tests cc_wrapper.py functionality and metrics extraction  
3. **Integration Test**: End-to-end simulation of benchmark.py usage
4. **Metrics Test**: Validates metrics accuracy and accumulation

**Usage:**
```bash
# Run all integration tests
uv run python dev-tests/test_claude_code_integration.py

# Expected output: All 4 tests should PASS
```

**When to use:**
- After environment changes (Docker, authentication, dependencies)
- Before running full benchmarks
- When modifying cc_wrapper.py
- To debug metrics or SDK issues

## Legacy Files (can be removed)

The following files were consolidated into `test_claude_code_integration.py`:

- `simple_test.py` - Basic wrapper test (superseded by Wrapper Test)
- `test_sdk.py` - Basic SDK test (superseded by SDK Direct Test)  
- `test_benchmark_metrics_flow.py` - End-to-end test (superseded by Integration Test)
- `test_metrics_debug_fix.py` - Metrics debugging (superseded by Metrics Test)
- `test_metrics_minimal.py` - Minimal metrics test (superseded by Integration Test)
- `test_wrapper_debug.py` - Wrapper debugging (superseded by all tests)
- `test_wrapper_metrics.py` - Wrapper metrics test (superseded by Wrapper + Metrics Test)

## Test Output Interpretation

### ✅ All PASS
- Claude Code integration working correctly
- Safe to run benchmarks
- Metrics extraction functioning

### ❌ SDK Direct FAIL
- Authentication issues
- Check CLAUDE_CODE_OAUTH_TOKEN in .env
- Verify claude CLI is installed and authenticated

### ❌ Wrapper FAIL  
- cc_wrapper.py issues
- Check import paths and dependencies
- Review wrapper initialization

### ❌ Integration FAIL
- End-to-end flow broken
- May indicate benchmark.py compatibility issues
- Check file permissions and working directory

### ❌ Metrics FAIL
- Metrics extraction or accumulation broken
- Critical for benchmark validity
- Review _update_metrics_from_message() logic

## Development Workflow

1. **After environment changes**: Run integration tests
2. **Before code changes**: Run tests to establish baseline  
3. **After code changes**: Run tests to verify no regression
4. **Before benchmark runs**: Ensure all tests pass

This ensures reliable Claude Code integration throughout development.