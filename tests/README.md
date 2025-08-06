# Tests

This directory contains all test files for the cc-benchmark project.

## Running Tests

### Quick Commands (using Makefile)
```bash
make test-unit        # Fast unit tests only
make test-integration # Slower integration tests
make test-models      # Model sync test (standalone)
make test-all         # All tests
```

### Direct pytest Commands
```bash
# All tests
python -m pytest tests/ -v

# By category
python -m pytest tests/ -m "unit" -v
python -m pytest tests/ -m "integration" -v
python -m pytest tests/ -m "requires_anthropic" -v

# Specific test file
python -m pytest tests/test_model_sync.py -v

# Standalone CLI test
python tests/test_model_sync.py
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests
- No external dependencies
- Test internal logic and data validation

### Integration Tests (`@pytest.mark.integration`) 
- Test interactions between components
- May require external dependencies (like Anthropic SDK)
- Slower but more comprehensive

### Model Sync Tests (`@pytest.mark.model_sync`)
- Verify our model constants match Anthropic SDK
- Critical for keeping benchmark current with latest models

### Special Markers
- `@pytest.mark.requires_anthropic`: Needs Anthropic SDK installed
- `@pytest.mark.slow`: Tests that take longer to run

## Test Structure

```
tests/
├── __init__.py           # Test package marker
├── conftest.py           # Shared pytest configuration
├── test_model_sync.py    # Model synchronization tests
└── README.md            # This file
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run unit tests
  run: make test-unit

- name: Run integration tests  
  run: make test-integration
```

### Exit Codes
- `0`: All tests passed
- `1`: One or more tests failed
- Uses standard pytest exit codes

## Development Testing Commands

### Quick Validation & Debugging
```bash
# Quick metrics validation (create a test script)
uv run python -c "from benchmark.cc_wrapper import ClaudeCodeWrapper; w=ClaudeCodeWrapper(verbose=True); print(w.run('What is 2+2?')); print(f'Cost: ${w.total_cost:.6f}, Tokens: {w.total_tokens_sent}/{w.total_tokens_received}')"

# Monitor benchmark progress in real-time
tail -f logs/benchmark.log

# Check benchmark results
find tmp.benchmarks -name "*.aider.results.json" -exec jq '.cost, .prompt_tokens, .completion_tokens' {} \;

# Test model sync with Anthropic SDK
make test-models                                    # Using Makefile
uv run python tests/test_model_sync.py            # Direct execution
uv run python -m pytest tests/test_model_sync.py  # Using pytest

# Check for model sync manually  
uv run python tests/model_sync_checker.py --verbose

# Show available models  
uv run python benchmark/models.py
```

### Test Infrastructure Details

**Test Commands** (mapped by file extension):
- `.py` → `pytest`
- `.rs` → `cargo test -- --include-ignored`
- `.go` → `go test ./...`
- `.js` → `/aider/benchmark/npm-test.sh`
- `.cpp` → `/aider/benchmark/cpp-test.sh`
- `.java` → `./gradlew test`

**Docker Benchmarking Rule**: Always run benchmarks in Docker containers for consistent environments - never run benchmarks directly with local Python!

### Testing Integration Changes

When modifying core integration:
1. Create isolated test scripts first (outside main codebase)
2. Validate metrics show real values (> 0) not hardcoded
3. Test end-to-end flow before full benchmark runs
4. Clean up test files after validation

## Configuration

Test behavior is configured in:
- `pytest.ini`: Main pytest configuration
- `tests/conftest.py`: Shared fixtures and hooks
- `Makefile`: Convenient test commands