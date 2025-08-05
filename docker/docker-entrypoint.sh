#!/bin/bash

# Docker entrypoint script for Claude Code benchmark environment
# Validates authentication via CLAUDE_CODE_OAUTH_TOKEN environment variable

set -e

# Check if Claude Code is properly installed
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code CLI not found in PATH"
    echo "This suggests the Docker image was not built correctly."
    exit 1
fi

# Load token from dedicated file if available
if [ -f "/root/.cc-benchmark/token" ]; then
    export CLAUDE_CODE_OAUTH_TOKEN=$(cat /root/.cc-benchmark/token)
fi

# Check if authentication token is available
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    echo "========================================"
    echo "ERROR: Claude Code not authenticated"
    echo "========================================"
    echo ""
    echo "To authenticate Claude Code, use the setup script:"
    echo ""
    echo "  # Run the authentication setup script (recommended)"
    echo "  ./docker/setup-claude-auth.sh"
    echo ""
    echo "This will prompt you to paste your Claude Code token and store it"
    echo "in the Docker volume for persistent authentication."
    echo ""
    exit 1
fi

# Validate that authentication is working
echo "Validating Claude Code authentication..."
if ! claude --print "auth test" &> /dev/null; then
    echo "========================================"
    echo "ERROR: Claude Code authentication failed"
    echo "========================================"
    echo ""
    echo "Your token may be invalid or expired. To fix this:"
    echo ""
    echo "  # Re-run the authentication setup script"
    echo "  ./docker/setup-claude-auth.sh"
    echo ""
    exit 1
fi

# Test that the SDK can be imported
echo "Testing Claude Code SDK import..."
if ! python -c "import claude_code_sdk; print('✓ Claude Code SDK import successful')" 2>/dev/null; then
    echo "ERROR: Failed to import claude_code_sdk"
    echo "This suggests the Python SDK was not installed correctly."
    exit 1
fi

echo "✓ Claude Code CLI and SDK are ready"
echo "✓ Token authentication validated"
echo ""

# Execute the original command
exec "$@"