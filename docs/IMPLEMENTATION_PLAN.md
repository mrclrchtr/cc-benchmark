# Claude Code Benchmark Implementation Plan

## Executive Summary
- **Objective**: Benchmark Claude Code vs aider on Exercism exercises to prove/disprove performance hypothesis
- **Duration**: 4 phases with flexible timeline (no pressure)
- **Parallel Streams**: MVP focus on sequential execution, parallel optimization in later phases
- **Critical Path**: Claude Code integration → Exercise execution → Results validation

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
- **Replace**: `Coder` class instantiation with Claude Code CLI calls
- **Adapt**: Response parsing from aider's format to Claude Code's JSON output
- **Maintain**: Docker isolation, test runner logic, results storage structure
- **New Requirements**:
  - Handle `--dangerously-skip-permissions` for unattended execution
  - Parse Claude Code's specific JSON response format
  - Manage session continuity with `--continue` flag

## Multi-Perspective Architecture

### Technical Perspective
- **Core Integration**: Claude Code SDK mode (`-p` flag) with JSON output parsing
- **Session Management**: Leverage `--continue` and `--dangerously-skip-permissions` for automation
- **Error Handling**: Process-level failures, rate limiting awareness
- **Data Pipeline**: Exercise → Claude Code → Test Results → Metrics

### Security Perspective
- **Sandbox Isolation**: Maintain Docker containers for code execution safety
- **Permission Management**: Use `--dangerously-skip-permissions` for unattended runs
- **Code Validation**: Test execution in isolated environments only
- **Data Protection**: Local execution, no sensitive data exposure

### Performance Perspective
- **Rate Limiting**: Handle Claude API limits gracefully
- **Resource Usage**: Single-threaded MVP, optimize for accuracy over speed
- **Caching Strategy**: Session continuity for related exercises
- **Scalability**: Design for eventual parallel execution

### Operations Perspective
- **Deployment**: Local development focus, containerized execution
- **Monitoring**: Simple logging and progress tracking
- **Reproducibility**: Version pinning for Claude Code CLI
- **Maintenance**: Modular design for CLI interface changes

## Project Structure

```
cc-benchmark/
├── polyglot-benchmark/           # EXISTING: Exercism exercises (symlink)
│   ├── python/                   # Python exercises
│   ├── javascript/               # JavaScript exercises
│   ├── go/                       # Go exercises
│   ├── rust/                     # Rust exercises
│   ├── cpp/                      # C++ exercises
│   └── java/                     # Java exercises
├── benchmark/                    # Adapted from aider benchmark
│   ├── cc_benchmark.py          # NEW: Claude Code benchmark runner
│   ├── cc_integration.py        # NEW: Claude Code CLI interface
│   ├── cc_parser.py             # NEW: Output parsing logic
│   ├── benchmark.py             # EXISTING: Aider benchmark (reference)
│   ├── prompts.py               # EXISTING: Exercise prompts (adapt)
│   └── Dockerfile               # EXISTING: Execution environment (adapt)
├── exercises/                    # NEW: Exercise management
│   ├── python_subset.py         # NEW: 10 Python exercises for MVP
│   └── loader.py                # NEW: Exercise loading utilities
├── results/                      # NEW: Benchmark outputs
│   ├── claude_code/             # NEW: Claude Code results
│   ├── comparisons/             # NEW: Comparative analysis
│   └── raw_data/                # NEW: Raw execution logs
├── tests/                        # NEW: Validation tests
│   ├── test_cc_integration.py   # NEW: Claude Code integration tests
│   └── test_exercise_loader.py  # NEW: Exercise loading tests
└── scripts/                      # NEW: Automation helpers
    ├── run_benchmark.py         # NEW: Main execution script
    └── compare_results.py       # NEW: Results comparison tool
```

## Execution Plan

### Phase 1: Core Infrastructure [P] (Week 1-2)
**Parallel Tasks** (execute simultaneously):
1. **Claude Code Integration** (Est: 8 hrs) [P]
   - Owner: Core - Output: Working CLI interface wrapper
   - Implement `cc_integration.py` with SDK mode calls
   - Handle `--dangerously-skip-permissions` flag
   - Test basic prompt → response workflow

2. **Output Parser Development** (Est: 6 hrs) [P]
   - Owner: Core - Output: JSON response parser
   - Parse Claude Code JSON output format
   - Extract code changes and test results
   - Error handling for malformed responses

3. **Exercise Subset Selection** (Est: 4 hrs) [P]
   - Owner: Core - Output: 10 Python exercises list
   - Identify 10 representative Python Exercism exercises
   - Validate exercise format compatibility
   - Create `python_subset.py` configuration

**Sequential Requirements**:
4. **Integration Testing** [S] - Prerequisites: Tasks 1-3 - Blocks: Phase 2
   - End-to-end test with single exercise
   - Validate Docker environment compatibility
   - Confirm output parsing accuracy

### Phase 2: MVP Implementation [S] (Week 3-4)
**Sequential Tasks** (dependent on Phase 1):
1. **Benchmark Runner Creation** (Est: 12 hrs) [S]
   - Adapt `benchmark.py` for Claude Code workflow
   - Implement single-threaded exercise execution
   - Add progress tracking and logging
   - Error recovery for failed exercises

2. **Results Management** (Est: 8 hrs) [S]
   - Create results storage structure
   - Implement raw data logging
   - Basic pass/fail metric calculation
   - Exercise completion tracking

3. **MVP Validation** (Est: 6 hrs) [S]
   - Run benchmark on 10 Python exercises
   - Validate results format consistency
   - Compare against expected exercise outcomes
   - Document any Claude Code limitations discovered

### Phase 3: Comparison Framework [P] (Week 5-6)
**Parallel Tasks**:
1. **Aider Results Integration** (Est: 8 hrs) [P]
   - Owner: Analysis - Output: Aider baseline data
   - Fetch/scrape aider's published results
   - Normalize data formats for comparison
   - Validate exercise overlap

2. **Comparative Analysis Tools** (Est: 10 hrs) [P]
   - Owner: Analysis - Output: Comparison utilities
   - Implement statistical comparison functions
   - Create pass rate analysis tools
   - Build failure category classification

3. **Documentation and Reporting** (Est: 6 hrs) [P]
   - Owner: Documentation - Output: Usage guides
   - Create benchmark execution documentation
   - Build results interpretation guides
   - Prepare sharing format templates

### Phase 4: Production Readiness [S] (Week 7-8)
**Sequential Tasks**:
1. **Error Handling Enhancement** (Est: 8 hrs) [S]
   - Robust rate limiting handling
   - Network failure recovery
   - Claude Code version compatibility checks
   - Comprehensive logging system

2. **Reproducibility Features** (Est: 6 hrs) [S]
   - Version pinning for all dependencies
   - Deterministic exercise ordering
   - Results validation checksums
   - Environment documentation

3. **Final Validation** (Est: 10 hrs) [S]
   - Complete benchmark run on full exercise set
   - Results validation against aider baseline
   - Performance optimization if needed
   - Publication-ready output generation

## Integration Points
- **Phase 1-2 Convergence**: Core infrastructure enables MVP execution
- **Phase 2-3 Convergence**: MVP results feed comparative analysis
- **Phase 3-4 Convergence**: Comparison tools enable production validation

## Technical Implementation Details

### Claude Code Integration Architecture
```python
# cc_integration.py - Core Interface
class ClaudeCodeRunner:
    def __init__(self, model="sonnet", session_continuity=True):
        self.base_cmd = [
            "claude", "-p", 
            "--output-format", "json",
            "--dangerously-skip-permissions"
        ]
        if session_continuity:
            self.base_cmd.extend(["--continue"])
    
    def run_exercise(self, prompt: str, files: List[str]) -> dict:
        # Execute Claude Code with exercise prompt
        # Parse JSON response for code changes
        # Return structured results
        pass
```

### Exercise Execution Flow
1. **Setup**: Load exercise files into isolated directory
2. **Prompt**: Send exercise instruction + current code to Claude Code
3. **Execute**: Run Claude Code with `--dangerously-skip-permissions`
4. **Parse**: Extract code changes from JSON response
5. **Test**: Run exercise tests against modified code
6. **Record**: Log results (pass/fail, iterations, changes)

### Output Format Specification
```json
{
  "exercise_id": "two-fer",
  "language": "python",
  "attempt": 1,
  "status": "pass|fail|error",
  "claude_response": {
    "code_changes": [...],
    "reasoning": "...",
    "confidence": 0.95
  },
  "test_results": {
    "passed": 5,
    "failed": 0,
    "errors": []
  },
  "metrics": {
    "execution_time": 45.2,
    "tokens_used": 1250
  }
}
```

## Resource Matrix
| Component | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Parallel Capacity |
|-----------|---------|---------|---------|---------|-------------------|
| Core Dev  | Integration, Parser, Selection | Runner, Results | - | Error Handling, Validation | 3 concurrent tasks max |
| Analysis  | - | - | Aider Integration, Comparison Tools | - | 2 concurrent tasks max |
| Documentation | - | Validation | Reporting | Final Docs | 1 task at a time |

## Risk Mitigation Strategy

| Risk | Impact | Parallel Mitigation | Owner |
|------|--------|-------------------|--------|
| Claude Code CLI changes | High | Pin specific version, abstract interface layer | Core Dev |
| Rate limiting | Medium | Implement exponential backoff, session management | Core Dev |
| Exercise format incompatibility | Medium | Validate early, adapt prompts as needed | Analysis |
| Docker environment issues | Low | Test containers early, document dependencies | Core Dev |
| JSON parsing failures | Medium | Robust error handling, fallback to text parsing | Core Dev |

## Testing Strategy

### Unit Tests
- **cc_integration.py**: Mock Claude Code responses, test parsing logic
- **exercise_loader.py**: Validate exercise loading, file management
- **cc_parser.py**: Test JSON parsing edge cases, error handling

### Integration Tests
- **End-to-end exercise execution**: Single exercise complete workflow
- **Docker environment validation**: Container setup and teardown
- **Results storage**: Data persistence and retrieval

### Validation Tests
- **Known exercise solutions**: Verify Claude Code can solve reference exercises
- **Output format consistency**: Ensure results match expected schema
- **Aider comparison baseline**: Validate against published aider results

## Deployment/Usage Instructions

### Prerequisites
```bash
# Install Claude Code CLI (pinned version)
curl -sSL https://claude.ai/install.sh | sh
claude --version  # Verify: expected version

# Setup Python environment
uv sync
source .venv/bin/activate

# Build Docker environment
cd benchmark && docker build -t cc-benchmark .
```

### Running the Benchmark
```bash
# MVP run (10 Python exercises)
python scripts/run_benchmark.py --subset python_10 --output results/mvp_run

# Full benchmark run
python scripts/run_benchmark.py --language python --output results/full_run

# Compare against aider
python scripts/compare_results.py results/full_run results/aider_baseline
```

### Results Analysis
```bash
# Generate comparison report
python scripts/compare_results.py --format markdown results/claude_code results/aider

# Plot performance metrics
python scripts/plot_results.py results/claude_code --output plots/
```

## Success Metrics and Validation Criteria

### Phase 1 Completion Criteria
- [ ] Claude Code CLI integration working with JSON output
- [ ] Output parser handles successful responses and errors
- [ ] 10 Python exercises identified and loadable
- [ ] End-to-end test passes for at least 1 exercise

### Phase 2 Completion Criteria (MVP)
- [ ] Benchmark runner executes all 10 Python exercises
- [ ] Results stored in structured format
- [ ] Pass/fail determination matches exercise test outcomes
- [ ] Error handling prevents complete run failures

### Phase 3 Completion Criteria
- [ ] Aider baseline results obtained and formatted
- [ ] Statistical comparison functions implemented
- [ ] Pass rate differential calculated
- [ ] Results formatted for sharing/publication

### Phase 4 Completion Criteria
- [ ] Robust error handling for all identified failure modes
- [ ] Reproducible benchmark runs with version pinning
- [ ] Complete documentation for setup and execution
- [ ] Publication-ready results demonstrating hypothesis outcome

### Definition of "Pass" (Aligned with Aider)
An exercise **passes** when:
1. All provided unit tests execute successfully (exit code 0)
2. No syntax errors in generated code
3. Code meets exercise requirements as validated by test suite
4. Solution completes within reasonable time/resource limits

### Statistical Approach (Aligned with Aider)
- **Primary Metric**: Pass rate percentage across exercise set
- **Sample Size**: Minimum 10 exercises for MVP, expand for statistical significance
- **Confidence**: Document confidence intervals for pass rate comparisons
- **Reproducibility**: Multiple runs to account for non-deterministic responses

## Implementation Timeline Flexibility

This plan is designed for **no timeline pressure** as specified. Each phase can be extended as needed based on:
- **Learning curve**: Claude Code CLI behavior discovery
- **Integration challenges**: Unexpected API or output format issues  
- **Quality standards**: Ensuring robust, reliable benchmark execution
- **Scope expansion**: Adding exercises or metrics if initial results are promising

The modular design allows for iterative improvement and scope adjustment based on findings from each phase.

## Future Expansion Considerations

### Post-MVP Enhancements
- **Multi-language support**: Expand beyond Python exercises
- **Parallel execution**: Implement concurrent exercise processing
- **Advanced metrics**: Code quality analysis, token efficiency
- **Configuration management**: Different Claude Code model comparisons
- **Continuous benchmarking**: Automated runs for Claude Code updates

### Research Applications
- **Prompt optimization**: Test different exercise instruction formats
- **Model comparison**: Claude Code vs other AI coding assistants
- **Exercise difficulty analysis**: Categorize exercises by complexity/domain
- **Longitudinal studies**: Track performance improvements over time

This implementation plan provides a clear, actionable roadmap while maintaining flexibility for discovery and adaptation during development.