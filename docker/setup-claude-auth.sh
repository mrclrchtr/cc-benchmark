#!/bin/bash

# Claude Code Authentication Setup Script (Simplified)
# This script helps set up Claude Code authentication using .env file

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
echo "💾 Creating .env file..."

# Create .env file with the token
cat > .env << EOF
# Claude Code Authentication
CLAUDE_CODE_OAUTH_TOKEN=$CLAUDE_TOKEN

# Optional: Disable telemetry and enable headless mode
CLAUDE_CODE_NO_TELEMETRY=1
CLAUDE_CODE_HEADLESS=1
EOF

echo "✅ .env file created successfully!"

echo ""
echo "🔍 Verifying authentication setup..."

# Test that the .env file approach works
if docker run --rm --env-file .env cc-benchmark echo "Authentication test successful!" >/dev/null 2>&1; then
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
echo "Your Claude Code token is now stored in the .env file."
echo ""
echo "To use the authenticated environment, run:"
echo "  ./docker/docker.sh"
echo ""
echo "The .env file will be automatically loaded by Docker."
echo ""