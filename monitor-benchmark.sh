#!/bin/bash
#
# monitor-benchmark.sh - Real-time monitoring of benchmark execution
#
# This script provides a convenient way to monitor benchmark progress
# in real-time, showing current status, progress, and statistics.
# It can automatically detect and switch to new benchmark runs.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
REFRESH_INTERVAL=5
STATE_DIR=""
AUTO_DETECT="true"

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Monitor benchmark execution progress in real-time with automatic detection
of new benchmark runs.

OPTIONS:
    -d, --dir DIR          State directory (default: auto-detect latest)
    -r, --refresh SECONDS  Refresh interval (default: 5)
    -n, --no-auto         Disable auto-detection of new runs
    -h, --help            Show this help message

FEATURES:
    • Auto-detects and switches to new benchmark runs
    • Visual progress bar with emojis
    • Real-time statistics by language
    • Cost and token tracking
    • Estimated time remaining

EXAMPLES:
    # Auto-monitor latest/new benchmark runs
    $0

    # Monitor specific benchmark run (no auto-switching)
    $0 --dir tmp.benchmarks/2025-01-07-10-00-00--sonnet --no-auto

    # Fast refresh with auto-detection
    $0 --refresh 2

    # Watch for new benchmarks (useful when starting monitor before benchmark)
    $0

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir)
            STATE_DIR="$2"
            AUTO_DETECT="false"  # Disable auto-detect when specific dir is given
            shift 2
            ;;
        -r|--refresh)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        -n|--no-auto)
            AUTO_DETECT="false"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# If auto-detect is enabled and no specific dir
if [ "$AUTO_DETECT" = "true" ]; then
    echo -e "${CYAN}🔍 Auto-detection mode enabled${NC}"
    echo -e "${BLUE}Will automatically detect and switch to new benchmark runs${NC}"
    
    if [ -z "$STATE_DIR" ]; then
        # Find the most recent benchmark directory as initial target
        LATEST_DIR=$(find tmp.benchmarks -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r | head -n 1)
        
        if [ -n "$LATEST_DIR" ]; then
            STATE_DIR="$LATEST_DIR/.tracker"
            echo -e "${GREEN}Initial benchmark found: $(basename $LATEST_DIR)${NC}"
        else
            echo -e "${YELLOW}No existing benchmarks found. Waiting for new benchmark to start...${NC}"
        fi
    fi
else
    # Manual mode - need a specific directory
    if [ -z "$STATE_DIR" ]; then
        echo -e "${BLUE}Looking for latest benchmark run...${NC}"
        
        # Find the most recent benchmark directory
        LATEST_DIR=$(find tmp.benchmarks -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r | head -n 1)
        
        if [ -z "$LATEST_DIR" ]; then
            echo -e "${RED}No benchmark runs found in tmp.benchmarks/${NC}"
            echo "Please specify a directory with --dir or start a benchmark first."
            exit 1
        fi
        
        STATE_DIR="$LATEST_DIR/.tracker"
        echo -e "${GREEN}Found: $LATEST_DIR${NC}"
    fi
    
    # Check if state directory exists
    if [ ! -d "$STATE_DIR" ]; then
        # Try appending .tracker if not already there
        if [[ ! "$STATE_DIR" == *"/.tracker" ]]; then
            STATE_DIR="$STATE_DIR/.tracker"
        fi
        
        if [ ! -d "$STATE_DIR" ]; then
            echo -e "${RED}State directory not found: $STATE_DIR${NC}"
            echo "Make sure a benchmark is running or has run recently."
            exit 1
        fi
    fi
fi

echo -e "${YELLOW}⏱️  Refresh interval: ${REFRESH_INTERVAL}s${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""

# Prepare Python command with auto-detect flag
PYTHON_CMD="benchmark/tracker.py monitor"
if [ -n "$STATE_DIR" ]; then
    PYTHON_CMD="$PYTHON_CMD \"$STATE_DIR\""
else
    PYTHON_CMD="$PYTHON_CMD None"
fi
PYTHON_CMD="$PYTHON_CMD $REFRESH_INTERVAL"

if [ "$AUTO_DETECT" = "true" ]; then
    PYTHON_CMD="$PYTHON_CMD true"
else
    PYTHON_CMD="$PYTHON_CMD false"
fi

# Start monitoring
if command -v python3 &> /dev/null; then
    eval python3 $PYTHON_CMD
elif command -v python &> /dev/null; then
    eval python $PYTHON_CMD
else
    echo -e "${RED}Python not found. Please install Python 3.${NC}"
    exit 1
fi