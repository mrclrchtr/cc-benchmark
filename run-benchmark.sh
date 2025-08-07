#!/bin/bash

# CC-Benchmark Runner - Convenience wrapper for common benchmark tasks
# Usage: ./run-benchmark.sh [preset] [options]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_MODEL="sonnet"
DEFAULT_TESTS=10

show_help() {
    echo "CC-Benchmark Runner"
    echo ""
    echo "Usage: $0 [preset] [options]"
    echo ""
    echo "Presets:"
    echo "  quick        - Quick test with 1 Python exercise"
    echo "  python       - Test 10 Python exercises (default)"
    echo "  multi        - Test 5 exercises each in Python, JavaScript, Go"
    echo "  full         - Full benchmark suite (all languages, 25 tests each)"
    echo "  custom       - Pass your own benchmark arguments"
    echo ""
    echo "Options:"
    echo "  --model MODEL     - Model to use (default: sonnet)"
    echo "  --tests N         - Number of tests (overrides preset)"
    echo "  --name NAME       - Custom test name (default: auto-generated)"
    echo "  --verbose         - Enable verbose output"
    echo "  --help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 quick                    # Quick single test"
    echo "  $0 python --tests 5         # 5 Python tests"
    echo "  $0 multi --model opus       # Multi-language with Opus"
    echo "  $0 custom --languages rust --num-tests 3"
    echo ""
}

# Parse command line arguments
PRESET=${1:-python}
shift || true

# Initialize variables
EXTRA_ARGS=""
CUSTOM_NAME=""
CUSTOM_TESTS=""
VERBOSE=""

# Parse additional options
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --tests)
            CUSTOM_TESTS="$2"
            shift 2
            ;;
        --name)
            CUSTOM_NAME="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

# Set model if not specified
MODEL=${MODEL:-$DEFAULT_MODEL}

# Generate test name if not provided
if [ -z "$CUSTOM_NAME" ]; then
    TIMESTAMP=$(date +%H%M)
    CUSTOM_NAME="${PRESET}-${MODEL}-${TIMESTAMP}"
fi

# Build Docker image if needed
if ! docker images | grep -q "cc-benchmark"; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    ./docker/docker_build.sh
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please run: cp .env.example .env"
    echo "Then add your CLAUDE_CODE_OAUTH_TOKEN to the .env file"
    exit 1
fi

# Set benchmark command based on preset
case $PRESET in
    quick)
        NUM_TESTS=${CUSTOM_TESTS:-1}
        echo -e "${GREEN}Running quick test: 1 Python exercise${NC}"
        BENCHMARK_CMD="--use-claude-code --languages python --num-tests $NUM_TESTS --model $MODEL --new $VERBOSE"
        ;;
    python)
        NUM_TESTS=${CUSTOM_TESTS:-10}
        echo -e "${GREEN}Running Python benchmark: $NUM_TESTS exercises${NC}"
        BENCHMARK_CMD="--use-claude-code --languages python --num-tests $NUM_TESTS --model $MODEL --new $VERBOSE"
        ;;
    multi)
        NUM_TESTS=${CUSTOM_TESTS:-5}
        echo -e "${GREEN}Running multi-language benchmark: $NUM_TESTS exercises each${NC}"
        BENCHMARK_CMD="--use-claude-code --languages python,javascript,go --num-tests $NUM_TESTS --model $MODEL --new $VERBOSE"
        ;;
    full)
        NUM_TESTS=${CUSTOM_TESTS:-25}
        echo -e "${GREEN}Running full benchmark suite: $NUM_TESTS exercises per language${NC}"
        BENCHMARK_CMD="--use-claude-code --languages python,javascript,go,rust,cpp,java --num-tests $NUM_TESTS --model $MODEL --new $VERBOSE"
        ;;
    custom)
        echo -e "${GREEN}Running custom benchmark${NC}"
        BENCHMARK_CMD="--use-claude-code $EXTRA_ARGS"
        ;;
    *)
        echo -e "${RED}Unknown preset: $PRESET${NC}"
        show_help
        exit 1
        ;;
esac

# Display configuration
echo "Configuration:"
echo "  Test Name: $CUSTOM_NAME"
echo "  Model: $MODEL"
echo "  Command: benchmark.py $CUSTOM_NAME $BENCHMARK_CMD"
echo ""

# Run the benchmark
echo -e "${YELLOW}Starting benchmark...${NC}"
./docker/docker.sh benchmark "$CUSTOM_NAME" $BENCHMARK_CMD

# Check if benchmark was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Benchmark completed successfully!${NC}"
    echo ""
    echo "Results saved to: tmp.benchmarks/$(date +%Y-%m-%d)*--$CUSTOM_NAME"
    echo "Logs available at: logs/benchmark.log"
    
    # Show quick stats if jq is available
    if command -v jq &> /dev/null; then
        LATEST_RESULT=$(find tmp.benchmarks -name "*--$CUSTOM_NAME" -type d | sort | tail -1)
        if [ -n "$LATEST_RESULT" ]; then
            echo ""
            echo "Quick Stats:"
            find "$LATEST_RESULT" -name "*.aider.results.json" -exec jq -r '
                "  " + .testcase + ": " + 
                (if .tests_outcomes[0] then "✓ PASS" else "✗ FAIL" end) + 
                " (cost: $" + (.cost | tostring | .[0:6]) + ", " + 
                (.duration | tostring | .[0:4]) + "s)"
            ' {} \;
        fi
    fi
else
    echo -e "${RED}✗ Benchmark failed. Check logs/benchmark.log for details.${NC}"
    exit 1
fi