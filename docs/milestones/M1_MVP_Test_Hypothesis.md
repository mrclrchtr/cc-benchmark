# Milestone: M1 - MVP Test Hypothesis

## Overview
Create a minimal viable product to test the core hypothesis: Can Claude Code beat aider's 85% pass rate on Exercism exercises? This milestone focuses on rapid validation through manual testing, creating a Claude Code CLI wrapper, and integrating it with the existing benchmark infrastructure to test 10 Python exercises.

## Deliverables
- [ ] Manual validation of Claude Code on one Python exercise (two-fer)
- [ ] Claude Code CLI wrapper (`cc_wrapper.py`) with subprocess integration
- [ ] Modified `benchmark.py` with `--use-claude-code` flag support
- [ ] Successful execution of 10 Python exercises using Claude Code
- [ ] Pass rate calculation and comparison to aider's 85% baseline

## Acceptance Criteria
1. Claude Code successfully runs via subprocess in Docker environment
2. Session continuity works with `--continue` flag for error iterations
3. JSON output parsing correctly extracts file modifications
4. 10 Python exercises complete without integration failures
5. Pass rate is calculated and documented for comparison to aider's 85%
6. All file modifications are properly applied by the wrapper

## Dependencies
- Existing aider benchmark infrastructure
- Docker environment with multi-language support
- Claude Code CLI tool installed and accessible
- Exercism exercises in `polyglot-benchmark/python/exercises/practice/`
- Access to claude-3-5-sonnet-20241022 model

## Technical Specifications

### Core Integration Points
- **File Location**: `benchmark/cc_wrapper.py` (new file)
- **Modification Target**: `benchmark/benchmark.py` lines 822-863 (Coder class replacement)
- **Interface Compatibility**: Mimic aider's `Coder.run()` method signature

### Claude Code Wrapper Requirements
- Subprocess execution with proper error handling
- JSON response parsing and content extraction
- Session management using `--continue` for multi-turn conversations
- Working directory management with `--add-dir` flag
- Model configuration support (default: claude-3-5-sonnet-20241022)
- Required flags: `--output-format json`, `--dangerously-skip-permissions`, `--max-turns 1`

### Integration Changes
- Add `--use-claude-code` CLI flag to benchmark.py
- Conditional instantiation: `ClaudeCodeWrapper` vs original `Coder` class
- Maintain existing result storage format (`.aider.results.json`)
- Preserve Docker containerization and test execution flow

## Testing Requirements

### Manual Testing (Day 1)
- Execute Claude Code on `two-fer` exercise manually
- Verify JSON output structure and content
- Test `--continue` functionality for error handling
- Validate file modification and test passing

### Integration Testing (Day 2-3)
- Unit test `cc_wrapper.py` JSON parsing
- Test wrapper with 3 exercises manually before benchmark integration
- Integration test with modified `benchmark.py`
- End-to-end test with 10 Python exercises
- Verify result storage format compatibility

### Validation Testing
- Compare pass rates between Claude Code and aider baseline
- Verify Docker isolation works with `--dangerously-skip-permissions`
- Test session continuity across multiple error iterations

## Documentation Requirements
- Code documentation for `ClaudeCodeWrapper` class methods
- Integration notes for benchmark.py modifications
- Manual testing procedure documentation
- Pass rate comparison results and analysis
- Risk mitigation documentation for identified issues (JSON format, session continuity, Docker compatibility)

## Risk Mitigation
- **High Risk - Unknown JSON format**: Manual testing on Day 1 to verify structure
- **High Risk - Session continuity**: Verify `--continue` works across subprocess calls
- **Medium Risk - Docker compatibility**: Use existing aider Docker setup as baseline
- **Low Risk - Rate limiting**: Single-threaded execution maintains safe API usage