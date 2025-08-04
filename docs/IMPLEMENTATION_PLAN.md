# Claude Code Benchmark Implementation Plan

## Executive Summary
- **Objective**: Benchmark Claude Code vs aider on Exercism exercises to compare pass rates
- **Target**: Beat aider's 85% pass rate on Python exercises (MVP), then expand to all languages
- **Duration**: 3 phases - MVP in 3-4 days, full implementation in 1-2 weeks
- **Core Solution**: Claude Code provides official Python SDK for programmatic integration

## Repository Context Analysis

### Core Architecture Discovery
- **Project Structure**: Fork of aider's benchmark infrastructure with cc-benchmark adaptations
- **Exercise Repository**: `polyglot-benchmark/` - Curated Exercism exercises (Python, JS, Go, Rust, C++, Java)
- **Benchmark Framework**: Built on aider's proven testing harness with Docker containerization

### Critical Files and Components
- **Benchmark Engine**:
  - `/benchmark/benchmark.py` - Main orchestrator using aider's Coder class, handles test execution flow
    - `run_test_real()` - Core function that runs individual exercises with model/format configs
    - `run_unit_tests()` - Language-specific test runner (pytest, cargo test, go test, etc.)
- **Test Configuration**:
  - `/benchmark/prompts.py` - Minimal prompt templates for exercise instructions and test failures
  - `/benchmark/Dockerfile` - Multi-language environment (Python 3.11, Go 1.21.5, Rust, Node.js 20, Java 21)
  - Test commands mapped by file extension (.py → pytest, .rs → cargo test, etc.)
- **Data Management**:
  - Results stored as JSON in `.aider.results.json` per test
  - Benchmark directories organized by timestamp under `tmp.benchmarks/`
  - Git-based change tracking for code modifications

### Technology Stack Analysis
- **Languages**: Python 3.12+ development environment, exercises in 6 languages
- **Dependencies**: 
  - aider framework (models, coders, sendchat modules)
  - claude-code-sdk: Official Python SDK for Claude Code integration
  - Testing: pytest, cargo, go test, jest, gradle
  - Infrastructure: Docker, git-python, pandas for analysis
- **Execution Model**: Single-threaded with optional sleep between tests
- **Model Support**: Configurable model selection (default: gpt-3.5-turbo)

### Integration Points for Claude Code
- **Replace**: Lines 822-863 in `benchmark.py` where `Coder` class is used
- **Key Insight**: Minimal changes to existing infrastructure - just swap the AI engine
- **SDK Advantages**:
  - Native Python async interface with structured message types
  - Built-in session management (no manual `--continue` handling)
  - Typed responses eliminate JSON parsing complexity
  - Automatic error handling and retry logic

## Simplified Architecture

### Core Approach
- **Minimal Changes**: Reuse 95% of aider's benchmark infrastructure
- **Single Integration Point**: Replace `Coder` class with `ClaudeCodeWrapper`
- **SDK Integration**: Use `claude-code-sdk` Python package for clean API
- **Session Management**: SDK handles continuity automatically

## Project Structure (Minimal MVP)

```
cc-benchmark/
├── polyglot-benchmark/           # EXISTING: Exercism exercises
├── benchmark/                    # EXISTING: Aider benchmark
│   ├── benchmark.py             # MODIFY: Add Claude Code support
│   ├── cc_wrapper.py            # NEW: Claude Code CLI wrapper (only new file!)
│   ├── prompts.py               # EXISTING: Works as-is
│   └── Dockerfile               # EXISTING: Works as-is
└── tmp.benchmarks/              # EXISTING: Results directory
```

That's it. One new file, one modified file.

## Execution Plan

### Phase 1: MVP - Test the Hypothesis (Day 1-2)

**Day 1: SDK Setup & Validation (3 hours)**
1. Install Claude Code SDK:
   ```bash
   pip install claude-code-sdk
   npm install -g @anthropic-ai/claude-code  # CLI prerequisite
   ```
2. Test SDK on one exercise:
   ```python
   from claude_code_sdk import query, ClaudeCodeOptions
   options = ClaudeCodeOptions(max_turns=3, permission_mode="bypassPermissions")
   async for message in query(prompt="Solve this exercise", options=options):
       print(message)
   ```
3. Verify message structure and file modifications

**Day 2: Create Wrapper & Integrate (4 hours)**
1. Create `cc_wrapper.py` using SDK
2. Add `--use-claude-code` flag to benchmark.py
3. Run 10 Python exercises
4. Compare pass rate to aider's 85%

### Phase 2: Full Benchmark (Day 3-5)

**Day 3-4: Python Complete**
- Run all Python exercises
- Fix any integration issues
- Document results

**Day 5: All Languages**
- Expand to JS, Go, Rust, C++, Java
- Handle language-specific quirks
- Generate comparison report

### Phase 3: Analysis & Sharing (Day 6-7)
- Statistical analysis of results
- Create visualizations
- Prepare findings for sharing

## Technical Implementation Details

### The Only New Code You Need (cc_wrapper.py)
```python
import asyncio
import os
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions, Message

class ClaudeCodeWrapper:
    def __init__(self, model="claude-sonnet-4-0", verbose=False):
        self.model = model
        self.verbose = verbose
        self.session_id = None
        self.messages = []
        self._verify_authentication()
        
    def _verify_authentication(self):
        """Verify Claude Code is logged in by testing a simple query"""
        try:
            # Test authentication with a minimal query
            asyncio.run(self._test_auth())
        except Exception as e:
            raise RuntimeError(f"Claude Code authentication failed. Please run 'claude' to log in. Error: {e}")
    
    async def _test_auth(self):
        """Test authentication with minimal query"""
        options = ClaudeCodeOptions(
            max_turns=1,
            permission_mode="bypassPermissions",
            output_format="json"
        )
        async for message in query(prompt="test", options=options):
            if message.get("type") == "system" and message.get("subtype") == "init":
                if not message.get("apiKeySource"):
                    raise RuntimeError("No API key source found")
                break
        
    def run(self, with_message, preproc=False):
        """Mimics aider's Coder.run() interface"""
        # Run async code in sync context
        return asyncio.run(self._async_run(with_message))
        
    async def _async_run(self, prompt):
        """Async implementation of run method"""
        options = ClaudeCodeOptions(
            max_turns=1,  # One response per call
            model=self.model,
            permission_mode="bypassPermissions",  # Equivalent to --dangerously-skip-permissions
            cwd=Path(os.getcwd()),
            allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
            output_format="stream-json" if self.verbose else "json"
        )
        
        # Use continue if we have an active session
        if self.session_id:
            options.continue_conversation = True
            
        response_text = ""
        try:
            async for message in query(prompt=prompt, options=options):
                self.messages.append(message)
                
                # Extract session ID from init message
                if message.get("type") == "system" and message.get("subtype") == "init":
                    self.session_id = message.get("session_id")
                
                # Extract assistant response text
                elif message.get("type") == "assistant":
                    content = message.get("message", {}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            response_text += block.get("text", "")
                
                # Handle result message
                elif message.get("type") == "result":
                    if message.get("subtype") == "success":
                        self.total_cost += message.get("total_cost_usd", 0)
                    elif self.verbose:
                        print(f"Claude Code error: {message.get('subtype')}")
                        
        except Exception as e:
            if self.verbose:
                print(f"Claude Code SDK error: {e}")
            return str(e)
            
        return response_text
    
    # Stub out other Coder methods that benchmark.py might call
    def apply_updates(self): pass
    @property
    def partial_response_content(self): return ""
    @partial_response_content.setter
    def partial_response_content(self, value): pass
    @property
    def last_keyboard_interrupt(self): return False
    total_cost = 0
    num_exhausted_context_windows = 0
    num_malformed_responses = 0
    total_tokens_sent = 0
    total_tokens_received = 0
    chat_completion_call_hashes = []
    chat_completion_response_hashes = []
```

### Integration Changes to benchmark.py
```python
# Around line 822, add:
if use_claude_code:  # New CLI flag
    coder = ClaudeCodeWrapper(model=model_name, verbose=verbose)
else:
    # Original aider Coder creation
    coder = Coder.create(...)
```

## Technical Prerequisites

### Required Installations
```bash
# Install Claude Code CLI (required by SDK)
npm install -g @anthropic-ai/claude-code

# Install Python SDK
pip install claude-code-sdk

# Verify installations
claude --version
python -c "import claude_code_sdk; print('SDK installed')"
```

### Environment Setup
- Python 3.10+ (SDK requirement)
- Node.js (for Claude Code CLI)
- Docker (for benchmark isolation)
- Logged-in Claude Code instance (uses existing user subscription)

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| SDK async/sync conversion | Medium | asyncio.run() handles conversion |
| Session management complexity | Low | SDK handles continuity automatically |
| Docker compatibility | Medium | Use existing aider Docker setup |
| Rate limiting | Low | Single-threaded execution |

## Quick Start

### Day 1: SDK Test
```bash
# Install prerequisites
npm install -g @anthropic-ai/claude-code
pip install claude-code-sdk

# Test SDK on one exercise
cd polyglot-benchmark/python/exercises/practice/two-fer
python -c "
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions
from pathlib import Path

async def test():
    options = ClaudeCodeOptions(
        max_turns=1,
        permission_mode='bypassPermissions',
        cwd=Path.cwd()
    )
    async for msg in query('Solve this Python exercise', options=options):
        print(msg)

asyncio.run(test())
"

# Verify it modifies the files correctly
pytest
```

### Day 2: MVP Implementation
```bash
# Create wrapper
vim benchmark/cc_wrapper.py  # Copy code from above

# Modify benchmark.py to add --use-claude-code flag
# Run MVP test
cd benchmark
python benchmark.py python-10 --use-claude-code --model claude-sonnet-4-0
```

### Day 3-5: Full Run
```bash
# Run all Python exercises
python benchmark.py python-all --use-claude-code

# Run all languages
python benchmark.py all-exercises --use-claude-code
```

## Success Criteria

### MVP (Day 2)
- [ ] Claude Code SDK integrated successfully
- [ ] Session management works automatically
- [ ] 10 Python exercises complete
- [ ] Pass rate calculated and compared to aider's 85%

### Full Benchmark (Day 5)
- [ ] All Python exercises tested
- [ ] Pass rate > 85% to beat aider
- [ ] All languages tested
- [ ] Results stored in same format as aider

### Critical Questions to Answer
1. **Does Claude Code beat aider's 85% pass rate?**
2. **Which exercises does Claude Code fail that aider passes?**
3. **Is there a pattern to the failures?**

## Summary

This SDK-based implementation provides:
- **One new file** (`cc_wrapper.py`) using official SDK
- **Minimal changes** to existing code
- **Faster implementation** (MVP in 2 days, full benchmark in 5 days)
- **Better reliability** with SDK's structured messages and error handling
- **Clear success metric** (beat 85% pass rate)

The SDK eliminates complexity around subprocess management, JSON parsing, and session continuity, allowing focus on the actual benchmarking comparison.