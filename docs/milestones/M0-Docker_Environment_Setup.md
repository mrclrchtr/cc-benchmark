# Milestone: M0 Docker Environment Setup 🐳 [B]

**Parallel Track**: Infrastructure  
**Dependencies**: None (foundational milestone)  
**Can Run In Parallel With**: None (blocking milestone)  
**Status**: pending

## Prerequisites
- [x] Git repository accessible and clean working directory
- [x] Docker installed and running on host system
- [x] Claude.ai subscription account for authentication
- [x] Internet connectivity for package downloads and authentication

## Overview
Establish the Docker-based execution environment for running Claude Code benchmarks. This milestone adapts the existing aider benchmark Docker infrastructure to support Claude Code CLI and SDK, including secure authentication handling and environment isolation.

## Objectives
- [x] Modify Docker configuration to include Claude Code CLI and Python SDK
- [x] Implement secure authentication handling via persistent Docker volumes
- [x] Create automated setup scripts and validation procedures
- [x] Document Docker environment usage and troubleshooting

## Deliverables
- [x] Updated docker/Dockerfile with Claude Code dependencies
- [x] Modified docker/docker.sh with Claude Code environment variables
- [x] New docker/docker-entrypoint.sh for authentication validation
- [x] Updated docker/docker_build.sh with new image naming
- [x] **MANUAL VERIFICATION REQUIRED**: Test Claude Code authentication flow in Docker container

## Success Criteria
- **Automated tests**: Docker image builds successfully with Claude Code CLI and SDK installed
- **Manual validation**: Claude Code can be invoked inside container and authentication persists
- **Performance metrics**: Container startup time < 30 seconds, image size reasonable
- **Quality metrics**: All Docker scripts follow best practices, proper error handling

## Timeline
- **Start**: Immediately (no dependencies)
- **Duration**: 3-4 hours (base estimate with Docker complexity multiplier)
- **Buffer**: +1 hour (25% buffer for Docker integration challenges)
- **Blocker Resolution Time**: N/A (foundational milestone)
- **Parallel Speedup**: 0% (blocking milestone, cannot be parallelized)
- **Critical Path**: Yes - blocks all subsequent development work

## Risk Factors
| Risk | Impact | Likelihood | Mitigation Strategy | Owner |
|------|--------|------------|-------------------|--------|
| Claude Code CLI installation fails | H | L | Test with specific CLI version, fallback to manual install | Dev |
| Authentication volume mounting issues | H | M | Test volume persistence, provide manual volume creation steps | Dev |
| Docker build fails due to dependency conflicts | M | M | Use specific package versions, test build process incrementally | Dev |
| Image size becomes too large | L | M | Multi-stage build, minimize installed packages | Dev |

## Resource Allocation
| Team/Resource | Tasks | Capacity | Conflicts |
|---------------|-------|----------|-----------|
| Developer | Docker configuration, testing | 4 hours | None (blocking milestone) |
| System | Docker build resources | 2GB RAM, 5GB disk | None |

## Dependencies
### Upstream Dependencies
- None (foundational milestone)

### Downstream Impact
- M1-MVP_Test_the_Hypothesis: Requires working Docker environment
- All future development: Docker environment is prerequisite for all benchmark execution

## Technical Specifications
### Architecture Decisions
- Use environment variable `CLAUDE_CODE_OAUTH_TOKEN` for authentication (no file-based auth)
- Store authentication token in Docker volume as dedicated token file
- Extend existing aider Dockerfile rather than creating new one
- Use environment variables for Claude Code configuration
- Clean separation: token storage in `/root/.cc-benchmark/` to avoid polluting Claude Code config

### Integration Points
- Claude Code CLI: Global npm installation in Docker container (v1.0.68)
- Claude Code SDK: Python package installation via uv (v0.0.19)
- Authentication: `CLAUDE_CODE_OAUTH_TOKEN` environment variable set at container startup
- Token Storage: Docker volume `claude-code-auth` mounted to `/root/.cc-benchmark/`
- Token File: `/root/.cc-benchmark/token` with 600 permissions

### Implementation Notes
- Authentication uses `CLAUDE_CODE_OAUTH_TOKEN` environment variable (no file-based auth)
- Setup script `./docker/setup-claude-auth.sh` handles token collection and storage
- Docker volume `claude-code-auth` stores token in dedicated clean location
- Docker entrypoint reads token file and sets environment variable automatically
- Environment variables control Claude Code behavior (`CLAUDE_CODE_NO_TELEMETRY=1`, `CLAUDE_CODE_HEADLESS=1`)
- Entry point script validates token authentication before allowing container usage

## Testing Requirements
- **Unit Tests**: N/A (infrastructure milestone)
- **Integration Tests**: Claude Code CLI responds to version check, SDK can be imported
- **E2E Tests**: Full authentication flow works, benchmark can execute in container
- **Performance Tests**: Container startup time, image build time
- **Security Tests**: Authentication tokens properly isolated in Docker volume

## Documentation Requirements
- [x] Code documentation (inline comments in Docker scripts)
- [ ] API documentation (N/A)
- [x] Architecture decision records (Docker approach rationale)
- [x] User-facing documentation (Docker setup instructions)
- [x] Runbook/operational guide (Authentication troubleshooting)

## Troubleshooting
**Common Issues and Solutions:**
1. **Claude Code CLI not found in container**
   - Error: `claude: command not found`
   - Solution: Verify npm install completed successfully, check PATH includes npm global bin directory
   
2. **Authentication token not persisting**
   - Error: `CLAUDE_CODE_OAUTH_TOKEN not set` on container restart
   - Solution: Ensure Docker volume is properly created and mounted: `docker volume create claude-code-auth`
   
3. **SDK import fails**
   - Error: `ModuleNotFoundError: No module named 'claude_code_sdk'`
   - Solution: Verify uv pip install completed, check Python path and virtual environment

4. **Authentication fails with valid token**
   - Error: `Claude Code authentication failed`
   - Solution: Token may be expired or invalid, re-run setup script: `./docker/setup-claude-auth.sh`

**Fallback Strategies:**
- If npm global install fails: Use manual binary download and PATH configuration
- If volume mounting fails: Use bind mounts to host directory as temporary workaround
- If SDK install fails: Use pip instead of uv as fallback package manager

## Manual Verification Steps

**REQUIRED**: The following steps must be completed manually to verify the Docker environment:

1. **Build and test the Docker image**:
```bash
# Build the new Docker image
./docker/docker_build.sh

# Create persistent authentication volume
docker volume create claude-code-auth
```

2. **Authenticate Claude Code (Token-based)**:
```bash
# Run the authentication setup script (recommended)
./docker/setup-claude-auth.sh
```

This script will:
- Guide you through getting your Claude Code token
- Prompt you to paste the token
- Store it securely in the Docker volume
- Test that the authentication works

3. **Verify authentication persists**:
```bash
# Test that authentication works after container restart
docker run --rm \
  -v claude-code-auth:/root/.cc-benchmark \
  cc-benchmark \
  echo "Authentication test successful!"
```

The container will automatically:
- Read the token from `/root/.cc-benchmark/token`
- Set the `CLAUDE_CODE_OAUTH_TOKEN` environment variable
- Validate the token by making a test API call
- Display success messages and start normally if authentication is working

## Implementation Examples

```dockerfile
# Key Dockerfile additions
RUN npm install -g @anthropic-ai/claude-code@latest
RUN uv pip install --system --no-cache-dir claude-code-sdk

ENV CLAUDE_CODE_NO_TELEMETRY=1
ENV CLAUDE_CODE_HEADLESS=1

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
```

```bash
# docker-entrypoint.sh authentication check
# Load token from dedicated file if available
if [ -f "/root/.cc-benchmark/token" ]; then
    export CLAUDE_CODE_OAUTH_TOKEN=$(cat /root/.cc-benchmark/token)
fi

# Check if authentication token is available
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    echo "ERROR: Claude Code not authenticated"
    echo "Run: ./docker/setup-claude-auth.sh"
    exit 1
fi
```

## Completion Summary

### ✅ Final Implementation Status
**Status**: COMPLETED (2025-08-05)
**Total Duration**: ~4 hours (including authentication troubleshooting)

### Key Achievements
1. **Multi-Language Docker Environment**: Successfully built container with Python 3.12.7, Go 1.21.5, Rust, Node.js 20, Java 21
2. **Claude Code Integration**: CLI v1.0.68 and SDK v0.0.19 installed and functional
3. **Authentication System**: Token-based authentication with setup script `./docker/setup-claude-auth.sh`
4. **Clean Architecture**: Token storage in dedicated location (`/root/.cc-benchmark/token`) to avoid config pollution
5. **Verification Completed**: Full end-to-end authentication flow tested and working

### Final Authentication Flow
1. User runs `./docker/setup-claude-auth.sh`
2. Script guides through token collection from Claude Code CLI
3. Token stored securely in Docker volume with 600 permissions
4. Container startup automatically reads token and sets `CLAUDE_CODE_OAUTH_TOKEN`
5. Authentication validated with test API call before container start
6. All containers inherit authentication seamlessly

### Ready for Next Phase
- ✅ Docker environment fully functional
- ✅ Authentication working across container restarts  
- ✅ All language runtimes available
- ✅ Claude Code CLI and SDK operational
- ✅ Ready for M1 MVP or Phase 2 development

## Notes
- **Token Budget**: lightweight <3K (infrastructure setup, minimal new code)
- **Integration Multipliers Applied**: 1.5x Docker complexity multiplier
- **Parallel Execution Notes**: This is a blocking milestone - no other development work can proceed until Docker environment is established
- **Authentication Security**: CLAUDE_CODE_OAUTH_TOKEN contains sensitive token, properly isolated in Docker volume
- **One-time Setup**: Authentication is required once per Docker host, persists across container restarts