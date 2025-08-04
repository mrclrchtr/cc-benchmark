# Milestone: MVP - Test the Hypothesis

## Overview
The MVP milestone aims to validate the core hypothesis that Claude Code can outperform aider's 85% pass rate on Python exercises using the existing benchmark infrastructure. This involves minimal integration work - creating a single wrapper file and testing Claude Code SDK on a subset of exercises to prove the concept before full implementation.

## Deliverables
- [ ] **Claude Code SDK Integration** (Day 1)
  - Install and verify Claude Code CLI and Python SDK
  - Validate SDK functionality on one sample exercise
  - Confirm message structure and file modification capabilities
- [ ] **ClaudeCodeWrapper Implementation** (Day 2)
  - Create `benchmark/cc_wrapper.py` using the official Claude Code SDK
  - Implement async-to-sync interface mimicking aider's Coder class
  - Add session management with automatic continuity
- [ ] **Benchmark Integration** (Day 2)
  - Add `--use-claude-code` flag to `benchmark/benchmark.py`
  - Integrate wrapper with existing benchmark infrastructure
  - Maintain compatibility with existing results format
- [ ] **MVP Validation** (Day 2)
  - Execute 10 Python exercises using Claude Code
  - Generate pass/fail results in aider-compatible format
  - Calculate and compare pass rate against aider's 85% baseline

## Acceptance Criteria
1. Claude Code SDK integrated successfully
2. Session management works automatically (no manual `--continue` handling)
3. 10 Python exercises complete without integration errors
4. Pass rate calculated and compared to aider's 85% benchmark
5. Results stored in same JSON format as aider (`.aider.results.json`)
6. Docker environment compatibility maintained

## Dependencies
- **Prerequisites:**
  - Node.js installed (for Claude Code CLI)
  - Python 3.10+ environment
  - Docker available for benchmark isolation
  - Logged-in Claude Code instance (existing user subscription)
- **Setup Requirements:**
  ```bash
  # CLI Installation
  npm install -g @anthropic-ai/claude-code
  # SDK Installation  
  pip install claude-code-sdk
  # Verification
  claude --version
  python -c "import claude_code_sdk; print('SDK installed')"
  ```
- **Repository Dependencies:**
  - Existing benchmark infrastructure (`benchmark/benchmark.py`)
  - Exercism exercise repository (`polyglot-benchmark/python/`)
  - Aider's testing harness and Docker setup

## Technical Specifications
**Core Integration Approach:**
- Minimal Changes: Reuse 95% of existing aider benchmark infrastructure
- Single Integration Point: Replace `Coder` class with `ClaudeCodeWrapper`
- SDK Advantages: Native async interface, structured responses, automatic session management

**ClaudeCodeWrapper Interface:**
```python
class ClaudeCodeWrapper:
    def __init__(self, model="claude-3-5-sonnet-20241022", verbose=False)
    def _verify_authentication(self)  # Check if Claude Code is logged in
    def run(self, with_message, preproc=False)  # Mimics aider's Coder.run()
    async def _async_run(self, prompt)  # Async implementation using SDK
```

**SDK Configuration:**
```python
options = ClaudeCodeOptions(
    max_turns=1,
    model=self.model,
    permission_mode="bypassPermissions",
    cwd=Path(os.getcwd()),
    allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
    continue_conversation=True  # For session continuity
)
```

**Integration Point in benchmark.py:**
```python
# Around line 822
if use_claude_code:  # New CLI flag
    coder = ClaudeCodeWrapper(model=model_name, verbose=verbose)
else:
    # Original aider Coder creation
    coder = Coder.create(...)
```

## Testing Requirements
- **SDK Validation Test:** Verify SDK can solve one exercise with proper file modifications
- **MVP Benchmark Run:** Execute `python benchmark.py python-10 --use-claude-code` 
- **Validation Checks:**
  - All 10 exercises execute without SDK errors
  - File modifications are properly applied
  - Test results are captured in JSON format
  - Pass rate calculation matches aider's methodology
  - Session continuity works across multiple exercise attempts

## Documentation Requirements
- **Technical Documentation:** Document SDK integration approach and any async/sync conversion issues
- **Results Documentation:** Pass/fail breakdown for all 10 test exercises with comparison to aider's 85% baseline
- **Minimal Scope:** No new README files; update implementation plan with actual results and lessons learned