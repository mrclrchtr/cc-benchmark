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
- NEVER include specific line numbers → they get outdated fast, use function/class names instead

**Keep it as small as possible**

## Key Architecture

### Python
- **uv**: Use `uv` where possible, e.g. to install dependencies and run tests

### Core Components
- **Benchmark Engine**: `/benchmark/benchmark.py` - Main orchestrator that runs exercises through AI models
  - `run_test_real()` - Executes individual exercises with model/format configs
  - `run_unit_tests()` - Language-specific test runner supporting Python, Go, Rust, JavaScript, C++, and Java
- **Exercise Repository**: `polyglot-benchmark/` - Curated Exercism exercises in multiple languages
- **Integration Point**: `benchmark.py` main execution where `Coder` class instantiation occurs - this is where Claude Code integration happens

### Test Infrastructure
- **Docker Environment**: Multi-language container defined in `/benchmark/Dockerfile`
  - **Authentication**: Uses `.env` file with `CLAUDE_CODE_OAUTH_TOKEN`
  - **Setup**: `cp .env.example .env` and add token
  - **Usage**: `./docker/docker.sh` automatically loads `.env` via `--env-file`
- **Logging System**: Comprehensive structured logging for benchmark monitoring
  - **Log File**: `logs/benchmark.log` (auto-created, rotated at 10MB, 5 backups)
  - **Docker Integration**: Logs mounted via `-v $(pwd)/logs:/logs` volume
  - **Real-time Monitoring**: `tail -f logs/benchmark.log` while benchmarks run
- **Docker Benchmarking Rule**: Always run benchmarks in Docker containers for consistent environments - never run benchmarks directly with local Python!
- **Test Commands**: See `tests/README.md` for language-specific test command mappings

## Development Commands

### Benchmark Execution

**IMPORTANT**: Always run benchmarks in Docker containers for consistent environments. Never run benchmarks directly with local Python!

#### Quick Start with run-benchmark.sh
```bash
# Convenience wrapper for common benchmark scenarios
./run-benchmark.sh quick           # Quick test: 1 Python exercise
./run-benchmark.sh python          # Default: 10 Python exercises  
./run-benchmark.sh multi           # Multi-language: 5 exercises each (Python, JS, Go)
./run-benchmark.sh full            # Full suite: all languages, 25 tests each

# With options
./run-benchmark.sh python --tests 5 --model opus  # 5 Python tests with Opus
./run-benchmark.sh custom --languages rust --num-tests 3  # Custom configuration
```

#### Docker Setup
1. Copy environment file: `cp .env.example .env`
2. Get OAuth token: `claude setup-token` and copy to `.env` as `CLAUDE_CODE_OAUTH_TOKEN`
3. Use `./run-benchmark.sh` or see `docker/README.md` for direct Docker usage

#### Benchmark Flags
- `--use-claude-code`: Use Claude Code instead of aider
- `--languages`: Specify language(s) to test (python, go, rust, javascript, cpp, java)
- `--num-tests`: Number of exercises to run
- `--model`: Model to use (sonnet, opus, haiku, etc.)
- `--new`: Start fresh benchmark run (avoids "prior runs exist" warning)
- `--tries`: Number of attempts per exercise (default: 3)
- `--verbose`: Enable detailed logging

### Testing & Validation
```bash
# Run all tests using Makefile
make test-all     # Run all tests (unit, integration, model sync)
make test-unit    # Run unit tests only
make test-models  # Run model sync tests only

# Direct pytest execution
uv run python -m pytest tests/ -v  # All tests
uv run python -m pytest tests/ -m "unit" -v  # Unit tests only
```

See `tests/README.md` for comprehensive testing commands and validation procedures.

## Claude Code Integration Strategy

The implementation integrates Claude Code via the official Python SDK using a wrapper approach:

1. **`benchmark/cc_wrapper.py`**: Complete wrapper class mimicking aider's `Coder` interface using `claude-code-sdk`
2. **`benchmark/benchmark.py`**: Added `--use-claude-code` flag with integration in main execution

**Key Integration Points**:
- **Permission Handling**: Uses `permission_mode="acceptEdits"` for automated file modifications
- **Authentication**: `.env` file approach with `CLAUDE_CODE_OAUTH_TOKEN`
- **Metrics Tracking**: Real cost and token tracking with optional `ANTHROPIC_API_KEY` for enhanced accuracy
- **Results Format**: Generates aider-compatible `.aider.results.json` files with real metrics
- **Session Management**: Automatic continuity with proper conversation tracking

**Optional Enhancement**:
- **Enhanced Token Counting**: Set `ANTHROPIC_API_KEY` in `.env` for precise token counting via Anthropic SDK (fallback to character-based estimation)

## Key Files and Documentation

> IMPORTANT: Always read the related file, if you want to know more about the specific part.

### Core Files
- **Benchmark Engine**: `/benchmark/benchmark.py` - Main orchestrator and Claude Code integration point
- **Claude Code Wrapper**: `/benchmark/cc_wrapper.py` - SDK wrapper mimicking aider's `Coder` interface  
- **Exercise Prompts**: `/benchmark/prompts.py` - Minimal templates for exercise instructions
- **Development Tests**: `/dev-tests/` - Comprehensive Claude Code integration validation suite

### Output and Results
- **Benchmark Results**: `.aider.results.json` files in each test directory
- **Benchmark Runs**: `tmp.benchmarks/` directory organized by timestamp
- **Logs**: `logs/benchmark.log` (auto-created, rotated at 10MB, 5 backups)

### Documentation Structure
- **Project Planning**: 
  - `docs/VISION.md` - The general project vision
  - `docs/IMPLEMENTATION_PLAN.md` - Technical roadmap
  - `docs/IMPLEMENTATION_LOG.md` - Implementation history and decisions
  - `docs/MILESTONE_MANAGER.md` - Progress and status tracking - only here and in the specific milestone files
  - `docs/TECHNICAL_DEBT.md` - Technical debt tracking
  - `docs/milestones/` - Individual milestone files (`M{major}_{sub}-{Short_Title}.md` format)
- **Technical Reference**:
  - `docs/tools/cc-cli.md` - Claude Code CLI documentation
  - `docs/tools/cc-sdk.md` - Python SDK documentation (`claude_code_sdk`)
  - `docs/tools/cc-models.md` - Available Claude Code models
  - `docs/architecture/logging.md` - Logging system documentation
- **Testing**: `tests/README.md` - How to run and implement tests

# Available system commands
- `eza` - A modern, maintained replacement for `ls`
- `ls` - Alias for `eza`

# Programming Principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)
- YAGNI (You Ain't Gonna Need It)
