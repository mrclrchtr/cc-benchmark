#!/bin/bash

# Simplified Docker entrypoint script for Claude Code benchmark environment
# Uses CLAUDE_CODE_OAUTH_TOKEN directly from environment variables (--env-file)

set -e

# Check if Claude Code is properly installed
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code CLI not found in PATH"
    echo "This suggests the Docker image was not built correctly."
    exit 1
fi

# Check if authentication token is available
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    echo "ERROR: Claude Code not authenticated"
    echo ""
    echo "To authenticate Claude Code:"
    echo "1. Copy .env.example to .env:"
    echo "   cp .env.example .env"
    echo "2. Edit .env and set your token:"
    echo "   CLAUDE_CODE_OAUTH_TOKEN=your_actual_token"
    echo "3. Run with: ./docker/docker.sh"
    echo ""
    exit 1
fi

# Validate that authentication is working
echo "Validating Claude Code authentication..."
if ! claude --print "auth test" &> /dev/null; then
    echo "ERROR: Claude Code authentication failed"
    echo "Your token may be invalid or expired."
    echo "Please update your .env file with a valid token."
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