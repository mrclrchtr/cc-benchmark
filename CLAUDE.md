# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is cc-benchmark - a benchmarking tool to compare Claude Code against aider on Exercism programming exercises.
The project forks aider's proven benchmark infrastructure and adapts it to test Claude Code's performance.

## CLAUDE.md rules
- No tracking of changes or project state → it is tracked in `docs/MILESTONE_MANAGER.md`
- New or changed commands/scripts? → Update "Development Commands"
- New or changed test/build procedures? → Update "Test Infrastructure" section  
- Changed integration points? → Update "Key Architecture" section
- New or changed patterns AI should follow? → Document the pattern
- BUT: Don't duplicate from docs/ → Use summary + reference instead

**Keep it as small as possible**

## Key Architecture

### Core Components
- **Benchmark Engine**: `/benchmark/benchmark.py` - Main orchestrator that runs exercises through AI models
  - `run_test_real()` - Executes individual exercises with model/format configs
  - `run_unit_tests()` - Language-specific test runner supporting Python, Go, Rust, JavaScript, C++, and Java
- **Exercise Repository**: `polyglot-benchmark/` - Curated Exercism exercises in multiple languages
- **Integration Point**: Lines 877-898 in `benchmark.py` where `Coder` class instantiation occurs - this is where Claude Code integration happens

### Test Infrastructure
- **Docker Environment**: Multi-language container defined in `/benchmark/Dockerfile`
  - **Authentication**: Uses `.env` file with `CLAUDE_CODE_OAUTH_TOKEN`
  - **Setup**: `cp .env.example .env` and add token
  - **Usage**: `./docker/docker.sh` automatically loads `.env` via `--env-file`
- **Logging System**: Comprehensive structured logging for benchmark monitoring
  - **Log File**: `logs/benchmark.log` (auto-created, rotated at 10MB, 5 backups)
  - **Docker Integration**: Logs mounted via `-v $(pwd)/logs:/logs` volume
  - **Real-time Monitoring**: `tail -f logs/benchmark.log` while benchmarks run
  - **Log Levels**: INFO (progress), WARNING (issues), ERROR (failures), DEBUG (details)
- **Test Commands** (mapped by file extension):
  - `.py` → `pytest`
  - `.rs` → `cargo test -- --include-ignored`
  - `.go` → `go test ./...`
  - `.js` → `/aider/benchmark/npm-test.sh`
  - `.cpp` → `/aider/benchmark/cpp-test.sh`
  - `.java` → `./gradlew test`

## Development Commands

### Benchmark Execution
```bash
# Run benchmark with Claude Code (requires authentication)
python benchmark/benchmark.py python --use-claude-code --languages python --num-tests 10 --new

# Key flags:
# --use-claude-code: Use Claude Code instead of aider
# --languages: Specify language(s) to test (python, go, rust, javascript, cpp, java)
# --num-tests: Number of exercises to run
# --new: Start fresh benchmark run (avoids "prior runs exist" warning)
# --tries: Number of attempts per exercise (default: 3)
# --verbose: Enable detailed logging
```

### Testing & Validation
```bash
# Quick metrics validation (create a test script)
python -c "from benchmark.cc_wrapper import ClaudeCodeWrapper; w=ClaudeCodeWrapper(verbose=True); print(w.run('What is 2+2?')); print(f'Cost: ${w.total_cost:.6f}, Tokens: {w.total_tokens_sent}/{w.total_tokens_received}')"

# Monitor benchmark progress in real-time
tail -f logs/benchmark.log

# Check benchmark results
find tmp.benchmarks -name "*.aider.results.json" -exec jq '.cost, .prompt_tokens, .completion_tokens' {} \;
```

### Dependencies
- **uv**: Use `uv` to install dependencies and run tests
- **claude-code-sdk**: Official Python SDK for Claude Code integration

## Claude Code Integration Strategy

The implementation integrates Claude Code via the official Python SDK using a wrapper approach:

1. **`benchmark/cc_wrapper.py`**: Complete wrapper class mimicking aider's `Coder` interface using `claude-code-sdk`
2. **`benchmark/benchmark.py`**: Added `--use-claude-code` flag with integration at lines 877-898
3. **SDK Usage**: Leverages SDK's structured message types, async/sync conversion, and session management

**Key Integration Points**:
- **Permission Handling**: Uses `permission_mode="acceptEdits"` for automated file modifications
- **Authentication**: `.env` file approach with `CLAUDE_CODE_OAUTH_TOKEN`
- **Metrics Tracking**: Real cost and token tracking (no more hardcoded values)
  - `total_cost`: Actual API costs from Claude Code responses
  - `total_tokens_sent/received`: Real token counts from API usage
  - `total_thinking_tokens`: Claude's internal thinking token usage
  - Error tracking: Context window exhaustions and malformed responses
- **Results Format**: Generates aider-compatible `.aider.results.json` files with real metrics
- **Session Management**: Automatic continuity with proper conversation tracking

**Usage**:
```bash
# Python benchmark with Claude Code
python benchmark/benchmark.py python --use-claude-code --languages python --num-tests 10

# All languages benchmark
python benchmark/benchmark.py python --use-claude-code
```

## Important Files and Locations

- **Results Storage**: `.aider.results.json` files in each test directory
- **Benchmark Output**: `tmp.benchmarks/` directory organized by timestamp
- **Prompts**: `/benchmark/prompts.py` - Minimal templates for exercise instructions
- **Milestone Documentation**: `/docs/milestones/` - Project planning and progress tracking
  - **Naming Convention**: `M{major}-{Short_Title}.md` (main milestones), `M{major}_{sub}-{Short_Title}.md` (sub-milestones)
- **Development Tests**: `/dev-tests/` - Contains `simple_test.py` and `test_sdk.py` for testing Claude Code integration during development

## Documentation Reference

For detailed project context, refer to these key documentation files:

- **Project Vision**: `docs/VISION.md` - Project goals, scope, and success criteria
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md` - Technical roadmap and integration strategy
- **Milestone Management**: `docs/MILESTONE_MANAGER.md` - Project tracking and milestone definitions
- **Tool Documentation**: 
  - `docs/tools/cc-cli.md` - Claude Code CLI usage and capabilities
  - `docs/tools/cc-sdk.md` - Python SDK integration details (`claude_code_sdk`)
  - `docs/tools/cc-models.md` - Claude Code models overview
- **Architecture Documentation**:
  - `docs/architecture/logging.md` - Comprehensive logging system guide


## Implementation Patterns & Lessons

### Metrics Tracking Pattern
When implementing metrics tracking in wrapper classes:
1. Initialize tracking variables in `__init__`
2. Update metrics after each API call
3. Use rough estimates when exact data unavailable (e.g., `len(text.split())` for token counting)
4. Track both successful and error cases
5. Implement session tracking with hashes for debugging

### Testing Integration Changes
When modifying core integration:
1. Create isolated test scripts first (outside main codebase)
2. Validate metrics show real values (> 0) not hardcoded
3. Test end-to-end flow before full benchmark runs
4. Clean up test files after validation

### Documentation Synchronization
When code changes affect documentation:
1. Update line number references immediately
2. Use `grep -n "pattern"` to find current line numbers
3. Keep CLAUDE.md focused on essential info (reference docs/ for details)
4. Update milestone status in both individual files and MILESTONE_MANAGER.md

# Programming Principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)
- YAGNI (You Ain't Gonna Need It)
