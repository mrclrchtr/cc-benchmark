# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is cc-benchmark - a benchmarking tool to compare Claude Code against aider on Exercism programming exercises.
The project forks aider's proven benchmark infrastructure and adapts it to test Claude Code's performance.

## CLAUDE.md rules
- No tracking of changes or project state → it is tracked in `docs/MILESTONE_MANAGER.md`
- Keep it as small as possible

## Key Architecture

### Core Components
- **Benchmark Engine**: `/benchmark/benchmark.py` - Main orchestrator that runs exercises through AI models
  - `run_test_real()` - Executes individual exercises with model/format configs
  - `run_unit_tests()` - Language-specific test runner supporting Python, Go, Rust, JavaScript, C++, and Java
- **Exercise Repository**: `polyglot-benchmark/` - Curated Exercism exercises in multiple languages
- **Integration Point**: Lines 822-863 in `benchmark.py` where `Coder` class instantiation occurs - this is where Claude Code integration should happen

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
- **uv**: use `uv` to install dependencies and run tests

## Claude Code Integration Strategy

The implementation plan (docs/IMPLEMENTATION_PLAN.md) outlines integrating Claude Code via the official Python SDK:

1. **Create `cc_wrapper.py`**: A wrapper class that mimics aider's `Coder` interface using the `claude-code-sdk` Python package
2. **Modify `benchmark.py`**: Add a `--use-claude-code` flag to switch between aider and Claude Code
3. **SDK Usage**: Leverage SDK's structured message types, session management, and error handling

Key integration points:
- Replace `Coder.create()` call around line 822 in `benchmark.py`
- Use SDK's `query()` function with `ClaudeCodeOptions` for configuration
- Handle async/sync conversion with `asyncio.run()`

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


# Programming Principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)
- YAGNI (You Ain't Gonna Need It)
