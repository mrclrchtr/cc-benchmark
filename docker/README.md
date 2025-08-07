# Docker Environment for CC-Benchmark

This directory contains the Docker configuration for running Claude Code benchmarks in a consistent, isolated environment.

## Quick Start

See [CLAUDE.md](../CLAUDE.md#docker-setup) for setup and usage instructions.

## Files Overview

### `Dockerfile`
Multi-stage Docker build for optimized image size and build caching:
- **Stage 1 (Builder)**: Compiles all languages and dependencies
- **Stage 2 (Runtime)**: Lightweight runtime with only necessary components
- **Languages**: Python 3.12.7, Go 1.21.5, Rust (latest), Node.js 20.x, Java 21
- **Tools**: Claude Code CLI & SDK, pytest, uv, pnpm-managed packages for JavaScript testing
- **Package Manager**: pnpm for JavaScript dependencies (faster and more efficient than npm)
- **Base**: Ubuntu Jammy with buildpack-deps

### `docker-entrypoint.sh`
Container initialization script that:
- Validates Claude Code authentication
- Tests SDK import capability
- **Automatically sets up polyglot-benchmark** in `/benchmarks` directory
- Ensures environment is ready before executing commands

### `docker.sh`
Flexible Docker launcher with three modes:
1. **Interactive mode** (no args): Launches bash shell for exploration
2. **Benchmark mode** (`benchmark` keyword): Direct benchmark execution with parameters
3. **Command mode** (any other args): Runs arbitrary commands in container

#### Usage Examples
```bash
# Interactive shell for exploration
./docker/docker.sh

# Direct benchmark execution
./docker/docker.sh benchmark test-name \
  --use-claude-code \
  --languages python \
  --num-tests 10 \
  --new

# Run any command in container
./docker/docker.sh ls /benchmarks
./docker/docker.sh uv run python -c "print('Hello from Docker')"
```

Features:
- Checks for `.env` file existence
- Mounts volumes: code, benchmarks, logs
- Sets memory limits (12GB)
- Configures environment variables
- Supports dynamic parameter passing

### `docker_build.sh`
Build script that:
- Builds from project root (not docker directory)
- Tags image as `cc-benchmark`
- Uses `docker/Dockerfile` as build file

## Volume Mounts

| Local Path | Container Path | Purpose |
|------------|---------------|---------|
| `$(pwd)` | `/cc-benchmark` | Source code and exercises |
| `$(pwd)/tmp.benchmarks` | `/benchmarks` | Benchmark results storage |
| `$(pwd)/logs` | `/logs` | Benchmark execution logs |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Authentication for Claude Code SDK |
| `CC_BENCHMARK_DOCKER` | Flag indicating Docker environment |
| `CC_BENCHMARK_DIR` | Directory for benchmark outputs (`/benchmarks`) |
| `ANTHROPIC_API_KEY` | (Optional) For accurate token counting |

## Running Benchmarks

### Recommended: Use run-benchmark.sh
See [CLAUDE.md](../CLAUDE.md#benchmark-execution) for usage examples and details.

### Direct Docker Execution
For advanced usage or custom configurations:
```bash
# Using docker.sh wrapper
./docker/docker.sh benchmark my-test \
  --use-claude-code \
  --languages python \
  --num-tests 10 \
  --model sonnet \
  --new

# Raw docker command (advanced)
docker run --rm --memory=12g --memory-swap=12g \
  --env-file .env \
  -v $(pwd):/cc-benchmark \
  -v $(pwd)/tmp.benchmarks:/benchmarks \
  -v $(pwd)/logs:/logs \
  -e CC_BENCHMARK_DOCKER=1 \
  -e CC_BENCHMARK_DIR=/benchmarks \
  cc-benchmark bash -c \
  "cd /cc-benchmark && \
   uv run python benchmark/benchmark.py test-name \
     --use-claude-code \
     --languages python \
     --num-tests 10 \
     --new"
```

### Supported Languages
- `python` - Python exercises using pytest
- `javascript` - JavaScript with Jest
- `go` - Go with native testing
- `rust` - Rust with cargo test
- `cpp` - C++ with custom test script
- `java` - Java with Gradle

## Troubleshooting

### "polyglot-benchmark not found"
The entrypoint script automatically copies polyglot-benchmark to `/benchmarks`. If issues persist:
1. Ensure the submodule is initialized: `git submodule update --init`
2. Rebuild the Docker image: `./docker/docker_build.sh`

### Authentication Issues
1. Verify token in `.env` file
2. Get new token if needed: `claude setup-token`
3. Ensure token has no extra whitespace

### Memory Issues
Default memory limit is 12GB. Adjust in `docker.sh` if needed:
```bash
--memory=8g --memory-swap=8g  # For 8GB limit
```

## Key Implementation Details

### Polyglot-Benchmark Handling
The `docker-entrypoint.sh` automatically ensures `polyglot-benchmark` exercises are available in the `/benchmarks` directory. This happens transparently when the container starts, eliminating manual setup.

### Cost Tracking
- With `ANTHROPIC_API_KEY`: Accurate token counting via Anthropic SDK
- Without API key: Character-based estimation (less accurate but functional)

### Logging
All benchmark runs generate logs in `logs/benchmark.log`:
- Auto-rotation at 10MB
- Keeps 5 backup files
- Real-time monitoring: `tail -f logs/benchmark.log`

## Implementation Notes

### Polyglot-Benchmark Auto-Setup
The `docker-entrypoint.sh` automatically copies `polyglot-benchmark` exercises to `/benchmarks` on container startup, eliminating manual setup.

### Environment Variables
Uses `CC_BENCHMARK_*` prefixed variables for benchmark configuration (evolved from original aider fork).