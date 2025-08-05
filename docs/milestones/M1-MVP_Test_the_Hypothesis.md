# Milestone: MVP - Test the Hypothesis

## Overview
The MVP milestone aims to validate the core hypothesis that Claude Code can outperform aider's 85% pass rate on Python exercises using the existing benchmark infrastructure. This involves minimal integration work - creating a single wrapper file and testing Claude Code SDK on a subset of exercises to prove the concept before full implementation.

## Deliverables
- [x] **Claude Code SDK Integration** (Day 1)
  - ✅ Install and verify Claude Code CLI and Python SDK
  - ✅ Validate SDK functionality on one sample exercise
  - ✅ Confirm message structure and file modification capabilities
- [x] **ClaudeCodeWrapper Implementation** (Day 2)
  - ✅ Create `benchmark/cc_wrapper.py` using the official Claude Code SDK
  - ✅ Implement async-to-sync interface mimicking aider's Coder class
  - ✅ Add session management with automatic continuity
- [x] **Benchmark Integration** (Day 2)
  - ✅ Add `--use-claude-code` flag to `benchmark/benchmark.py`
  - ✅ Integrate wrapper with existing benchmark infrastructure
  - ✅ Maintain compatibility with existing results format
- [ ] **MVP Validation** (Day 2) - INCOMPLETE
  - ✅ Execute Python exercises using Claude Code (only 2/10 tested)
  - ✅ Generate pass/fail results in aider-compatible format
  - ❌ Calculate and compare pass rate against aider's 85% baseline (insufficient data)

## Acceptance Criteria
1. ✅ Claude Code SDK integrated successfully
2. ✅ Session management works automatically (no manual `--continue` handling)
3. ⚠️ Python exercises complete without integration errors (only 2/10 tested)
4. ❌ Pass rate calculated and compared to aider's 85% benchmark (insufficient sample)
5. ✅ Results stored in same JSON format as aider (`.aider.results.json`)
6. ❓ Docker environment compatibility maintained (not verified)

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
    def __init__(self, model="claude-sonnet-4-0", verbose=False)
    def _verify_authentication(self)  # Check if Claude Code is logged in
    def run(self, with_message, preproc=False)  # Mimics aider's Coder.run()
    async def _async_run(self, prompt)  # Async implementation using SDK
```

**SDK Configuration:**
```python
options = ClaudeCodeOptions(
    model=self.model,
    permission_mode="bypassPermissions",
    cwd=Path(os.getcwd()),
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

## Status Summary (Current)

### ✅ Completed Work
1. **SDK Integration**: Successfully installed and validated Claude Code SDK functionality
2. **Wrapper Implementation**: Created `benchmark/cc_wrapper.py` with:
   - Async-to-sync interface mimicking aider's `Coder.run()`
   - Authentication verification using CLI commands
   - Session management and working directory support
3. **Benchmark Integration**: Added `--use-claude-code` flag to `benchmark/benchmark.py` with:
   - Conditional coder creation (line 843-866)
   - Parameter passing through all call chains
   - Error handling and availability checks
4. **Dependencies**: Optimized pyproject.toml dependencies, removing unnecessary `importlib-resources`
5. **Testing**: Validated basic SDK functionality with simple test script

### ⚠️ MVP Results - INCOMPLETE
1. **Integration Success**: Claude Code SDK integrated with benchmark infrastructure
2. **Test Execution**: Only 2 exercises tested instead of promised 10:
   - `go-counting`: FAILED (0/2 tests passed)
   - `grade-school`: PASSED (1/1 tests passed)
3. **Pass Rate Results**: **50% pass rate (1/2 exercises)** - insufficient sample size for validation
4. **Missing Deliverables**:
   - Did NOT run full python-10 benchmark suite as specified
   - Did NOT achieve statistically meaningful comparison to aider's 85% baseline
   - Did NOT investigate go-counting failure
5. **Hypothesis Assessment**: **NOT VALIDATED** - Insufficient testing (only 2 exercises)

### 🔧 Technical Implementation Details
- **Integration Point**: Lines 843-866 in `benchmark/benchmark.py`
- **Wrapper Location**: `benchmark/cc_wrapper.py` (247 lines)
- **Dependencies**: 7 core packages (claude-code-sdk, aider-chat, typer, pandas, lox, matplotlib, imgcat)
- **Authentication**: Uses `claude --version` and test query for verification
- **Model Support**: Configurable model selection (defaults to claude-sonnet-4-0)
- **Results Tracking**: Cost and token counts hardcoded to 0 (not properly implemented)

### 🔍 Key Findings
**Configuration Issue Resolved**: Removed `max_turns=1` parameter that was limiting Claude Code to single responses.

**Actual Test Results**:
- Total exercises tested: 2 (not 10 as required)
- Passed: 1 (grade-school)
- Failed: 1 (go-counting)
- Pass rate: 50%

### ❌ Outstanding Work Required
1. Run complete python-10 benchmark suite
2. Document all test results transparently
3. Investigate failures and root causes
4. Achieve minimum 10 exercise sample size for statistical validity
5. Compare results meaningfully against aider's 85% baseline

### 🚨 Technical Debt - Concerning Implementations
1. **Hardcoded Metrics**: Cost tracking hardcoded to 0.0 - no actual cost calculation
2. **Missing Token Tracking**: All token counts (sent/received/thinking) hardcoded to 0
3. **Incomplete Error Handling**: No proper handling for authentication failures beyond basic check
4. **Stub Implementations**: Multiple wrapper attributes initialized but never properly updated:
   - `num_exhausted_context_windows` always 0
   - `num_malformed_responses` always 0
   - `chat_completion_call_hashes` empty list
   - `chat_completion_response_hashes` empty list
5. **No Performance Metrics**: Missing implementation for tracking actual API performance
6. **Compatibility Issues**: Wrapper mimics aider interface but doesn't implement most functionality properly
