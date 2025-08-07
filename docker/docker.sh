#!/bin/bash

# Docker launcher for CC-Benchmark
# Usage:
#   ./docker/docker.sh                    # Interactive shell
#   ./docker/docker.sh benchmark [args]   # Run benchmark with arguments
#   ./docker/docker.sh [command]          # Run any command in container

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo ""
    echo "To create one:"
    echo "  cp .env.example .env"
    echo "  # Edit .env and add your CLAUDE_CODE_OAUTH_TOKEN"
    echo ""
    exit 1
fi

# Determine command to run
if [ $# -eq 0 ]; then
    # No arguments: interactive shell
    DOCKER_CMD="bash"
    DOCKER_FLAGS="-it"
elif [ "$1" = "benchmark" ]; then
    # Benchmark shortcut: shift off 'benchmark' and pass remaining args
    shift
    DOCKER_CMD="cd /cc-benchmark && uv run python benchmark/benchmark.py $@"
    DOCKER_FLAGS=""
else
    # Custom command: pass all arguments as-is
    DOCKER_CMD="$@"
    DOCKER_FLAGS="-it"
fi

# Run Docker container with appropriate command
if [ -n "$DOCKER_FLAGS" ]; then
    docker run \
           $DOCKER_FLAGS --rm \
           --memory=12g \
           --memory-swap=12g \
           --add-host=host.docker.internal:host-gateway \
           --env-file .env \
           -v `pwd`:/cc-benchmark \
           -v `pwd`/tmp.benchmarks/.:/benchmarks \
           -v `pwd`/logs:/logs \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           -e HISTFILE=/cc-benchmark/.bash_history \
           -e PROMPT_COMMAND='history -a' \
           -e HISTCONTROL=ignoredups \
           -e HISTSIZE=10000 \
           -e HISTFILESIZE=20000 \
           -e CC_BENCHMARK_DOCKER=1 \
           -e CC_BENCHMARK_DIR=/benchmarks \
           -e UV_LINK_MODE=copy \  # Performance: Copies packages instead of symlinks
           cc-benchmark \
           $DOCKER_CMD
else
    docker run \
           --rm \
           --memory=12g \
           --memory-swap=12g \
           --add-host=host.docker.internal:host-gateway \
           --env-file .env \
           -v `pwd`:/cc-benchmark \
           -v `pwd`/tmp.benchmarks/.:/benchmarks \
           -v `pwd`/logs:/logs \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           -e HISTFILE=/cc-benchmark/.bash_history \
           -e PROMPT_COMMAND='history -a' \
           -e HISTCONTROL=ignoredups \
           -e HISTSIZE=10000 \
           -e HISTFILESIZE=20000 \
           -e CC_BENCHMARK_DOCKER=1 \
           -e CC_BENCHMARK_DIR=/benchmarks \
           -e UV_LINK_MODE=copy \  # Performance: Copies packages instead of symlinks
           cc-benchmark \
           bash -c "$DOCKER_CMD"
fi
