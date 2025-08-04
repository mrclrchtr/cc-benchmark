# Claude Code Benchmark Implementation Plan

## Executive Summary
- **Objective**: Benchmark Claude Code vs aider on Exercism exercises to compare pass rates
- **Target**: Beat aider's 85% pass rate on Python exercises (MVP), then expand to all languages
- **Duration**: 3 phases - MVP in 1 week, full implementation in 2-3 weeks
- **Core Challenge**: Claude Code operates via CLI subprocess, not Python API

## Repository Context Analysis

### Core Architecture Discovery
- **Project Structure**: Fork of aider's benchmark infrastructure with cc-benchmark adaptations
- **Exercise Repository**: `polyglot-benchmark/` - Curated Exercism exercises (Python, JS, Go, Rust, C++, Java)
- **Benchmark Framework**: Built on aider's proven testing harness with Docker containerization

### Critical Files and Components
- **Benchmark Engine**:
  - `/benchmark/benchmark.py` - Main orchestrator using aider's Coder class, handles test execution flow
  - `/benchmark/run_test_real()` - Core function that runs individual exercises with model/format configs
  - `/benchmark/run_unit_tests()` - Language-specific test runner (pytest, cargo test, go test, etc.)
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
  - Testing: pytest, cargo, go test, jest, gradle
  - Infrastructure: Docker, git-python, pandas for analysis
- **Execution Model**: Single-threaded with optional sleep between tests
- **Model Support**: Configurable model selection (default: gpt-3.5-turbo)

### Integration Points for Claude Code
- **Replace**: Lines 822-863 in `benchmark.py` where `Coder` class is used
- **Key Insight**: Minimal changes to existing infrastructure - just swap the AI engine
- **Critical Requirements**:
  - Handle `--dangerously-skip-permissions` (requires Docker isolation)
  - Manage session continuity with `--continue` for error iterations
  - Parse Claude Code's JSON output to extract file modifications

## Simplified Architecture

### Core Approach
- **Minimal Changes**: Reuse 95% of aider's benchmark infrastructure
- **Single Integration Point**: Replace `Coder` class with `ClaudeCodeWrapper`
- **Docker Required**: `--dangerously-skip-permissions` mandates isolation
- **Session Continuity**: Use `--continue` to maintain context between error iterations

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

### Phase 1: MVP - Test the Hypothesis (Day 1-3)

**Day 1: Manual Validation (2 hours)**
1. Pick one Python exercise (e.g., `two-fer`)
2. Run Claude Code manually:
   ```bash
   cd polyglot-benchmark/python/exercises/practice/two-fer
   claude -p --output-format json --dangerously-skip-permissions "Solve this exercise"
   ```
3. Verify JSON output structure
4. Test `--continue` for error iterations

**Day 2: Create Wrapper (4 hours)**
1. Create `cc_wrapper.py`:
   - Subprocess calls to Claude Code
   - JSON response parsing
   - Session management for `--continue`
2. Test on 3 exercises manually

**Day 3: Integrate with benchmark.py (4 hours)**
1. Add `--use-claude-code` flag
2. Replace Coder instantiation (lines 822-834)
3. Replace run method (line 863)
4. Run 10 Python exercises
5. Compare pass rate to aider's 85%

### Phase 2: Full Benchmark (Day 4-7)

**Day 4-5: Python Complete**
- Run all Python exercises
- Fix any integration issues
- Document results

**Day 6-7: All Languages**
- Expand to JS, Go, Rust, C++, Java
- Handle language-specific quirks
- Generate comparison report

### Phase 3: Analysis & Sharing (Day 8-10)
- Statistical analysis of results
- Create visualizations
- Prepare findings for sharing

## Technical Implementation Details

### The Only New Code You Need (cc_wrapper.py)
```python
import subprocess
import json
import os
from pathlib import Path

class ClaudeCodeWrapper:
    def __init__(self, model="claude-3-5-sonnet-20241022", verbose=False):
        self.model = model
        self.verbose = verbose
        self.session_active = False
        
    def run(self, with_message, preproc=False):
        """Mimics aider's Coder.run() interface"""
        cmd = [
            "claude", "-p",
            "--model", self.model,
            "--output-format", "json",
            "--dangerously-skip-permissions",
            "--max-turns", "1"  # One response per call
        ]
        
        # Use --continue after first run
        if self.session_active:
            cmd.append("--continue")
        
        # Add working directory
        cmd.extend(["--add-dir", "."])
        
        # Execute
        result = subprocess.run(
            cmd + [with_message],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        self.session_active = True
        
        if result.returncode != 0:
            if self.verbose:
                print(f"Claude Code error: {result.stderr}")
            return result.stderr
            
        # Parse JSON and extract text response
        try:
            response = json.loads(result.stdout)
            # Extract the actual response text from JSON
            # (Need to verify exact JSON structure)
            return response.get("content", "")
        except json.JSONDecodeError:
            return result.stdout
    
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

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Claude Code JSON format unknown | High | Test manually first (Day 1) |
| Session continuity across subprocess | High | Verify with manual testing |
| Docker compatibility | Medium | Use existing aider Docker setup |
| Rate limiting | Low | Single-threaded execution |

## Quick Start

### Day 1: Manual Test
```bash
# Test Claude Code on one exercise
cd polyglot-benchmark/python/exercises/practice/two-fer
cat .docs/instructions.md
claude -p --output-format json --dangerously-skip-permissions \
  "Solve this Python exercise. The instructions are: [paste instructions]"
  
# Verify it modifies the files correctly
pytest
```

### Day 2-3: MVP Implementation
```bash
# Create wrapper
vim benchmark/cc_wrapper.py  # Copy code from above

# Modify benchmark.py to add --use-claude-code flag
# Run MVP test
cd benchmark
python benchmark.py python-10 --use-claude-code --model claude-3-5-sonnet-20241022
```

### Day 4-7: Full Run
```bash
# Run all exercises
python benchmark.py all-exercises --use-claude-code
```

## Success Criteria

### MVP (Day 3)
- [ ] Claude Code runs via subprocess in Docker
- [ ] Session continuity works with `--continue`
- [ ] 10 Python exercises complete
- [ ] Pass rate calculated and compared to aider's 85%

### Full Benchmark (Day 7)
- [ ] All Python exercises tested
- [ ] Pass rate > 85% to beat aider
- [ ] Results stored in same format as aider

### Critical Questions to Answer
1. **Does Claude Code beat aider's 85% pass rate?**
2. **Which exercises does Claude Code fail that aider passes?**
3. **Is there a pattern to the failures?**

## Summary

This revised plan focuses on what matters:
- **One new file** (`cc_wrapper.py`)
- **Minimal changes** to existing code
- **Fast validation** (MVP in 3 days)
- **Clear success metric** (beat 85% pass rate)

The original plan was overengineered. This approach gets you to meaningful results quickly by leveraging the existing infrastructure rather than rebuilding it.