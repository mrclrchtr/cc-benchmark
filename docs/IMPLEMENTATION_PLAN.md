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

### Phase 0: Docker Environment Setup (NEW - Day 1)
**Duration: 3-4 hours**

1. **Update Docker Configuration (2 hours)**
   - Modify `benchmark/Dockerfile` to include Claude Code CLI and SDK
   - Update `docker.sh` with Claude Code environment variables
   - Change image name in `docker_build.sh` to `cc-benchmark`
   - Create `docker-entrypoint.sh` for authentication handling

2. **Build and Test Docker Image (1 hour)**
   - Build the new Docker image
   - Test Claude Code CLI availability in container
   - Verify SDK can be imported
   - Test authentication pass-through

3. **Documentation (30 minutes)**
   - Update README with Docker setup instructions
   - Document authentication options
   - Add troubleshooting guide for common Docker issues

### Phase 1: MVP - Test the Hypothesis (Day 2-3)

**Day 2: SDK Setup & Validation (3 hours)**
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

**Day 3: Create Wrapper & Integrate (4 hours)**
1. Create `cc_wrapper.py` using SDK
2. Add `--use-claude-code` flag to benchmark.py
3. Run 10 Python exercises
4. Compare pass rate to aider's 85%

### Phase 2: Full Benchmark (Day 4-6)

**Day 4-5: Python Complete**
- Run all Python exercises
- Fix any integration issues
- Document results

**Day 6: All Languages**
- Expand to JS, Go, Rust, C++, Java
- Handle language-specific quirks
- Generate comparison report

### Phase 3: Analysis & Sharing (Day 7-8)
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
            raise RuntimeError(f"Claude Code authentication failed. Please run 'claude login' to authenticate. Error: {e}")
    
    async def _test_auth(self):
        """Test authentication with minimal query"""
        options = ClaudeCodeOptions(
            max_turns=1,
            permission_mode="bypassPermissions",
            output_format="json"
        )
        async for message in query(prompt="test", options=options):
            if message.get("type") == "system" and message.get("subtype") == "init":
                # Just verify we get an init message, subscription login handles auth
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

## Docker Environment Adaptation Plan

### Overview
The benchmark framework uses Docker for secure, isolated test execution. The current Docker setup is tailored for aider and requires modifications to support Claude Code's runtime requirements.

### Required Docker Changes

#### 1. Dockerfile Modifications (`benchmark/Dockerfile`)
```dockerfile
# Add to existing Dockerfile after line 43 (Node.js installation)
# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code@latest

# Add after pip installations (line 62)
# Install Claude Code SDK
RUN uv pip install --system --no-cache-dir claude-code-sdk

# Add environment setup for Claude Code
ENV CLAUDE_CODE_NO_TELEMETRY=1
ENV CLAUDE_CODE_HEADLESS=1

# Copy and set entrypoint script
COPY benchmark/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]
```

#### 2. Docker Run Script (`benchmark/docker.sh`)
```bash
# Add Claude Code specific mounts and environment
-v claude-code-auth:/root/.config/claude-code \
-e CLAUDE_CODE_SESSION_DIR=/benchmarks/.claude-sessions \
-e CLAUDE_CODE_CONFIG_DIR=/benchmarks/.claude-config \
-e CLAUDE_CODE_NO_TELEMETRY=1 \
-e CLAUDE_CODE_HEADLESS=1 \
```

#### 3. Build Script Updates (`benchmark/docker_build.sh`)
- Update image tag from `aider-benchmark` to `cc-benchmark`
- Add build args for optional API key injection

#### 4. New Docker Security Considerations
- **Authentication**: Claude Code requires Claude.ai subscription login
  - Uses Docker volume `claude-code-auth` for persistent authentication
  - Authentication stored in `/root/.config/claude-code/auth.json`
  - One-time interactive login required per Docker host
  - Login enforced with `--forceLoginMethod=claudeai` to ensure Claude.ai subscription
  - No API keys in environment variables or code
  - Authentication persists across container restarts via Docker volume
- **Network Access**: Claude Code requires internet access for subscription validation
- **File System**: 
  - Persistent volume for authentication (`claude-code-auth`)
  - Writable benchmark directory for Claude Code sessions
  - Session data persists in `/benchmarks/.claude-sessions`
- **Security Best Practices**:
  - auth.json contains sensitive authentication tokens
  - Docker volume isolates credentials from host system
  - Volume can be inspected/backed up if needed
  - Clean removal: `docker volume rm claude-code-auth`

### Implementation Phases

#### Phase 0: Docker Preparation (New - Before Phase 1)
**Duration**: 2-3 hours

1. **Create Docker adaptation branch**
   ```bash
   git checkout -b docker-claude-code-integration
   ```

2. **Update Dockerfile**
   - Add Claude Code CLI and SDK installations
   - Configure environment variables
   - Test build process

3. **Modify docker.sh**
   - Add Claude Code environment variables
   - Handle authentication mounting
   - Update container name

4. **Create docker-compose.yml (optional)**
   ```yaml
   version: '3.8'
   services:
     cc-benchmark:
       build:
         context: .
         dockerfile: benchmark/Dockerfile
       environment:
         - CLAUDE_CODE_NO_TELEMETRY=1
         - CLAUDE_CODE_HEADLESS=1
         - CLAUDE_CODE_SESSION_DIR=/benchmarks/.claude-sessions
         - CLAUDE_CODE_CONFIG_DIR=/benchmarks/.claude-config
       volumes:
         - claude-code-auth:/root/.config/claude-code
         - ./tmp.benchmarks:/benchmarks
         - ./polyglot-benchmark:/polyglot-benchmark
         - .:/aider
       working_dir: /aider
       stdin_open: true
       tty: true
   
   volumes:
     claude-code-auth:
       external: true
   ```

5. **Test Docker environment**
   ```bash
   # Build new image
   ./benchmark/docker_build.sh
   
   # Test Claude Code CLI in container
   docker run --rm cc-benchmark claude --version
   
   # Test SDK import
   docker run --rm cc-benchmark python -c "import claude_code_sdk"
   ```

### Authentication Strategy

#### Claude Code Subscription Login (Required)
The benchmark requires using Claude Code with a valid Claude.ai subscription login. Authentication is stored in `~/.config/claude-code/auth.json`.

1. **Persistent Login Storage**:
   ```bash
   # Create persistent volume for Claude Code config
   docker volume create claude-code-auth
   
   # Mount in docker.sh - specific to auth.json location
   -v claude-code-auth:/root/.config/claude-code \
   ```

2. **Initial Login Setup**:
   ```bash
   # One-time interactive login (force Claude.ai subscription login)
   docker run -it --rm \
     -v claude-code-auth:/root/.config/claude-code \
     cc-benchmark \
     claude --forceLoginMethod=claudeai
   
   # Note: Use --forceLoginMethod=claudeai to ensure Claude.ai subscription login
   # (not Anthropic Console API billing accounts)
   ```

3. **Verification**:
   ```bash
   # Verify login persists by checking auth.json
   docker run --rm \
     -v claude-code-auth:/root/.config/claude-code \
     cc-benchmark \
     bash -c "test -f /root/.config/claude-code/auth.json && echo 'Auth found' || echo 'No auth'"
   
   # Verify Claude Code status
   docker run --rm \
     -v claude-code-auth:/root/.config/claude-code \
     cc-benchmark \
     claude status
   ```

4. **Automated Login Check**:
   ```bash
   # Add to docker-entrypoint.sh
   if [ ! -f "/root/.config/claude-code/auth.json" ]; then
     echo "ERROR: Claude Code not authenticated (auth.json not found)"
     echo "Run: docker run -it -v claude-code-auth:/root/.config/claude-code cc-benchmark claude --forceLoginMethod=claudeai"
     exit 1
   fi
   
   if ! claude status &>/dev/null; then
     echo "ERROR: Claude Code authentication invalid"
     echo "Run: docker run -it -v claude-code-auth:/root/.config/claude-code cc-benchmark claude --forceLoginMethod=claudeai"
     exit 1
   fi
   ```

5. **Troubleshooting Authentication**:
   ```bash
   # If authentication fails, clean and retry
   docker run --rm \
     -v claude-code-auth:/root/.config/claude-code \
     cc-benchmark \
     rm -rf /root/.config/claude-code/auth.json
   
   # Then login again
   docker run -it --rm \
     -v claude-code-auth:/root/.config/claude-code \
     cc-benchmark \
     claude --forceLoginMethod=claudeai
   ```

### File Structure for Docker Support
```
cc-benchmark/
├── benchmark/
│   ├── Dockerfile                # MODIFY: Add Claude Code
│   ├── docker.sh                # MODIFY: Update environment
│   ├── docker_build.sh          # MODIFY: Update image name
│   ├── docker-compose.yml       # NEW: Optional compose file
│   └── docker-entrypoint.sh     # NEW: Handle auth setup
└── tmp.benchmarks/
    ├── .claude-sessions/        # NEW: Session storage
    └── .claude-config/          # NEW: Config storage
```

### Docker Entrypoint Script (New)
```bash
#!/bin/bash
# docker-entrypoint.sh

# Check if auth.json exists
if [ ! -f "/root/.config/claude-code/auth.json" ]; then
    echo "ERROR: Claude Code not authenticated (auth.json not found)"
    echo ""
    echo "To login with your Claude.ai subscription, run:"
    echo "  docker run -it -v claude-code-auth:/root/.config/claude-code cc-benchmark claude --forceLoginMethod=claudeai"
    echo ""
    echo "This will save your login for future benchmark runs."
    exit 1
fi

# Verify Claude Code status
if ! claude status &>/dev/null; then
    echo "ERROR: Claude Code authentication is invalid!"
    echo ""
    echo "Your auth.json exists but authentication failed. To fix this:"
    echo "  1. Remove old auth: docker run --rm -v claude-code-auth:/root/.config/claude-code cc-benchmark rm -rf /root/.config/claude-code/auth.json"
    echo "  2. Login again: docker run -it -v claude-code-auth:/root/.config/claude-code cc-benchmark claude --forceLoginMethod=claudeai"
    echo ""
    exit 1
fi

# Initialize Claude Code directories if needed
if [ ! -d "$CLAUDE_CODE_SESSION_DIR" ]; then
    mkdir -p "$CLAUDE_CODE_SESSION_DIR"
fi
if [ ! -d "$CLAUDE_CODE_CONFIG_DIR" ]; then
    mkdir -p "$CLAUDE_CODE_CONFIG_DIR"
fi

echo "Claude Code authenticated successfully (auth.json found and valid)"

# Execute command
exec "$@"
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

### Day 1: Docker Setup
```bash
# Update Docker files
cd cc-benchmark
git checkout -b docker-claude-code-integration

# Modify Dockerfile to add Claude Code
vim benchmark/Dockerfile
# Add after line 43:
# RUN npm install -g @anthropic-ai/claude-code@latest
# Add after line 62:
# RUN uv pip install --system --no-cache-dir claude-code-sdk

# Update docker_build.sh
sed -i 's/aider-benchmark/cc-benchmark/g' benchmark/docker_build.sh

# Build the new image
./benchmark/docker_build.sh

# Create persistent volume for authentication
docker volume create claude-code-auth

# Login to Claude Code with Claude.ai subscription (one-time setup)
docker run -it --rm -v claude-code-auth:/root/.config/claude-code cc-benchmark claude --forceLoginMethod=claudeai

# Verify auth.json was created
docker run --rm -v claude-code-auth:/root/.config/claude-code cc-benchmark ls -la /root/.config/claude-code/auth.json

# Verify the setup
docker run --rm -v claude-code-auth:/root/.config/claude-code cc-benchmark claude status
```

### Day 2: SDK Test
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

### Day 3: MVP Implementation
```bash
# Create wrapper
vim benchmark/cc_wrapper.py  # Copy code from above

# Modify benchmark.py to add --use-claude-code flag
# Run MVP test in Docker
docker run -it --rm \
  -v claude-code-auth:/root/.config/claude-code \
  -v $(pwd):/aider \
  -v $(pwd)/tmp.benchmarks:/benchmarks \
  cc-benchmark \
  python benchmark/benchmark.py python-10 --use-claude-code --model claude-sonnet-4-0
```

### Day 4-6: Full Run
```bash
# Run all Python exercises
python benchmark.py python-all --use-claude-code

# Run all languages
python benchmark.py all-exercises --use-claude-code
```

## Success Criteria

### Docker Setup (Day 1)
- [ ] Docker image builds successfully with Claude Code CLI and SDK
- [ ] Authentication works via environment variable
- [ ] Claude Code can be invoked inside container
- [ ] Test execution environment is properly isolated

### MVP (Day 3)
- [ ] Claude Code SDK integrated successfully
- [ ] Session management works automatically
- [ ] 10 Python exercises complete
- [ ] Pass rate calculated and compared to aider's 85%

### Full Benchmark (Day 6)
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
- **Docker environment** adapted for Claude Code with secure authentication
- **Minimal changes** to existing code (Dockerfile modifications, one new wrapper)
- **Phased implementation** (Docker setup in 1 day, MVP in 3 days, full benchmark in 6 days)
- **Better reliability** with SDK's structured messages and error handling
- **Clear success metric** (beat 85% pass rate)

The SDK eliminates complexity around subprocess management, JSON parsing, and session continuity, while Docker provides a secure, isolated environment for consistent benchmark execution across different systems.