#!/bin/bash

# Claude Code Authentication Setup Script
# This script helps set up Claude Code authentication for the Docker environment

set -e

echo "=========================================="
echo "Claude Code Authentication Setup"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker is not running or not accessible"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if the Docker image exists
if ! docker image inspect cc-benchmark >/dev/null 2>&1; then
    echo "❌ Error: cc-benchmark Docker image not found"
    echo ""
    echo "Please build the Docker image first:"
    echo "  ./docker/docker_build.sh"
    exit 1
fi

# Create the authentication volume if it doesn't exist
echo "📦 Creating Docker volume for authentication storage..."
docker volume create claude-code-auth >/dev/null 2>&1 || true

echo ""
echo "🔐 Claude Code Token Setup"
echo ""
echo "To get your Claude Code token:"
echo "1. Install Claude Code CLI on your host system (if not already installed):"
echo "   npm install -g @anthropic-ai/claude-code"
echo ""
echo "2. Run the authentication setup:"
echo "   claude setup-token"
echo ""
echo "3. After successful authentication, get your token by running:"
echo "   claude config get token"
echo ""
echo "4. Copy the token and paste it below."
echo ""

# Prompt for token
read -p "📋 Please paste your Claude Code token: " -r CLAUDE_TOKEN

if [ -z "$CLAUDE_TOKEN" ]; then
    echo "❌ Error: No token provided"
    exit 1
fi

# Validate token format (basic check)
if [[ ! "$CLAUDE_TOKEN" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "⚠️ Warning: Token format looks unusual, but proceeding..."
fi

echo ""
echo "🧪 Testing token validity..."

# Test the token by making a simple API call
if docker run --rm --entrypoint="" -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_TOKEN" cc-benchmark claude --print "test" >/dev/null 2>&1; then
    echo "✅ Token is valid!"
else
    echo "❌ Error: Token validation failed"
    echo "Please check that your token is correct and try again."
    exit 1
fi

echo ""
echo "💾 Storing authentication in Docker volume..."

# Store the token in a dedicated file in a clean location
# Use --entrypoint="" to bypass authentication check during setup
docker run --rm --entrypoint="" -v claude-code-auth:/root/.cc-benchmark -e CLAUDE_TOKEN="$CLAUDE_TOKEN" cc-benchmark bash -c "
    mkdir -p /root/.cc-benchmark
    echo \"\$CLAUDE_TOKEN\" > /root/.cc-benchmark/token
    chmod 600 /root/.cc-benchmark/token
    echo 'Token stored successfully in /root/.cc-benchmark/token'
"

echo ""
echo "🔍 Verifying authentication setup..."

# Test that the stored authentication works
if docker run --rm -v claude-code-auth:/root/.cc-benchmark cc-benchmark echo "Authentication test successful!" >/dev/null 2>&1; then
    echo "✅ Authentication setup complete!"
else
    echo "❌ Error: Authentication verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 Claude Code Authentication Setup Complete!"
echo "=========================================="
echo ""
echo "Your Claude Code token is now stored in the Docker volume 'claude-code-auth'."
echo ""
echo "To use the authenticated environment, run:"
echo "  ./docker/docker.sh"
echo ""
echo "Or for manual container runs, use:"
echo "  docker run --rm -v claude-code-auth:/root/.config/claude-code cc-benchmark [command]"
echo ""
echo "The authentication will persist across container restarts."
echo ""