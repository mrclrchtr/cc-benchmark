# Milestone: M0 Docker Environment Setup 🐳 [B]

**Parallel Track**: Infrastructure  
**Dependencies**: None (foundational milestone)  
**Can Run In Parallel With**: None (blocking milestone)  
**Status**: pending

## Prerequisites
- [ ] Git repository accessible and clean working directory
- [ ] Docker installed and running on host system
- [ ] Claude.ai subscription account for authentication
- [ ] Internet connectivity for package downloads and authentication

## Overview
Establish the Docker-based execution environment for running Claude Code benchmarks. This milestone adapts the existing aider benchmark Docker infrastructure to support Claude Code CLI and SDK, including secure authentication handling and environment isolation.

## Objectives
- [ ] Modify Docker configuration to include Claude Code CLI and Python SDK
- [ ] Implement secure authentication handling via persistent Docker volumes
- [ ] Create automated setup scripts and validation procedures
- [ ] Document Docker environment usage and troubleshooting

## Deliverables
- [ ] Updated Dockerfile with Claude Code dependencies
- [ ] Modified docker.sh with Claude Code environment variables
- [ ] New docker-entrypoint.sh for authentication validation
- [ ] Updated docker_build.sh with new image naming
- [ ] Optional docker-compose.yml for streamlined management

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
- M1_MVP_Test_the_Hypothesis: Requires working Docker environment
- All future development: Docker environment is prerequisite for all benchmark execution

## Technical Specifications
### Architecture Decisions
- Use Docker volumes for persistent Claude Code authentication storage
- Extend existing aider Dockerfile rather than creating new one
- Force Claude.ai subscription login method to ensure proper authentication
- Use environment variables for Claude Code configuration

### Integration Points
- Claude Code CLI: Global npm installation in Docker container
- Claude Code SDK: Python package installation via uv
- Authentication: Persistent volume mounting for ~/.config/claude-code/
- Session management: Writable directories for Claude Code sessions

### Implementation Notes
- Authentication requires one-time interactive login setup
- Docker volume `claude-code-auth` stores authentication tokens securely
- Environment variables control Claude Code behavior (telemetry, headless mode)
- Entry point script validates authentication before allowing container usage

## Testing Requirements
- **Unit Tests**: N/A (infrastructure milestone)
- **Integration Tests**: Claude Code CLI responds to version check, SDK can be imported
- **E2E Tests**: Full authentication flow works, benchmark can execute in container
- **Performance Tests**: Container startup time, image build time
- **Security Tests**: Authentication tokens properly isolated in Docker volume

## Documentation Requirements
- [ ] Code documentation (inline comments in Docker scripts)
- [ ] API documentation (N/A)
- [ ] Architecture decision records (Docker approach rationale)
- [ ] User-facing documentation (Docker setup instructions)
- [ ] Runbook/operational guide (Authentication troubleshooting)

## Troubleshooting
**Common Issues and Solutions:**
1. **Claude Code CLI not found in container**
   - Error: `claude: command not found`
   - Solution: Verify npm install completed successfully, check PATH includes npm global bin directory
   
2. **Authentication file not persisting**
   - Error: `auth.json not found` on container restart
   - Solution: Ensure Docker volume is properly created and mounted: `docker volume create claude-code-auth`
   
3. **SDK import fails**
   - Error: `ModuleNotFoundError: No module named 'claude_code_sdk'`
   - Solution: Verify uv pip install completed, check Python path and virtual environment

4. **Authentication fails with valid login**
   - Error: `Claude Code authentication is invalid`
   - Solution: Remove old auth and re-login: `rm -rf /root/.config/claude-code/auth.json` then `claude --forceLoginMethod=claudeai`

**Fallback Strategies:**
- If npm global install fails: Use manual binary download and PATH configuration
- If volume mounting fails: Use bind mounts to host directory as temporary workaround
- If SDK install fails: Use pip instead of uv as fallback package manager

## Implementation Examples
```bash
# Build the new Docker image
./benchmark/docker_build.sh

# Create persistent authentication volume
docker volume create claude-code-auth

# One-time authentication setup
docker run -it --rm \
  -v claude-code-auth:/root/.config/claude-code \
  cc-benchmark \
  claude --forceLoginMethod=claudeai

# Verify installation and authentication
docker run --rm \
  -v claude-code-auth:/root/.config/claude-code \
  cc-benchmark \
  bash -c "claude --version && python -c 'import claude_code_sdk; print(\"SDK OK\")' && claude status"
```

```dockerfile
# Key Dockerfile additions
RUN npm install -g @anthropic-ai/claude-code@latest
RUN uv pip install --system --no-cache-dir claude-code-sdk

ENV CLAUDE_CODE_NO_TELEMETRY=1
ENV CLAUDE_CODE_HEADLESS=1

COPY benchmark/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
```

```bash
# docker-entrypoint.sh authentication check
if [ ! -f "/root/.config/claude-code/auth.json" ]; then
    echo "ERROR: Claude Code not authenticated"
    echo "Run: docker run -it -v claude-code-auth:/root/.config/claude-code cc-benchmark claude --forceLoginMethod=claudeai"
    exit 1
fi
```

## Notes
- **Token Budget**: lightweight <3K (infrastructure setup, minimal new code)
- **Integration Multipliers Applied**: 1.5x Docker complexity multiplier
- **Parallel Execution Notes**: This is a blocking milestone - no other development work can proceed until Docker environment is established
- **Authentication Security**: auth.json contains sensitive tokens, properly isolated in Docker volume
- **One-time Setup**: Authentication is required once per Docker host, persists across container restarts