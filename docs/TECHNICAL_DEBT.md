# Technical Debt

This document tracks over-engineering and technical debt issues identified during development.

## M0 Over-Engineering Issues

### 1. Authentication System Complexity - RESOLVED
**Issue**: 105-line setup script for what is essentially a 3-step process  
- **Location**: `docker/setup-claude-auth.sh` (DELETED)
- **Over-engineering**: Complex token validation, fancy UI, extensive error handling
- **Solution implemented**: Standard `.env` file approach with Docker `--env-file`
- **Impact resolved**: Eliminated maintenance overhead and user confusion
- **Status**: COMPLETED - Single authentication method only

### 2. Complex Volume Mounting - RESOLVED
**Issue**: Custom Docker volume system instead of standard environment variables
- **Location**: All Docker scripts now use `--env-file` only
- **Over-engineering**: Was using persistent token storage in Docker volumes when env vars are simpler
- **Solution implemented**: Direct environment variable injection via `--env-file`
- **Impact resolved**: Eliminated Docker setup and debugging complexity
- **Status**: COMPLETED - Volume mounting completely removed

### 3. Scope Creep in Setup Script
**Issue**: Authentication script does more than authentication
- **Features added**: 
  - Docker image validation
  - Token format validation
  - API testing
  - Fancy terminal formatting
  - Detailed error messages and help text
- **Core function**: Store authentication token
- **Impact**: Script became 111 lines instead of ~10 lines
- **Recommended fix**: Separate concerns - authentication vs validation vs help

### 4. Documentation Status Inconsistency
**Issue**: Milestone status not synchronized between files
- **Location**: `docs/milestones/M0-Docker_Environment_Setup.md` vs `docs/MILESTONE_MANAGER.md`
- **Problem**: Status showed "pending" but was marked DONE in manager
- **Impact**: Confusion about project state
- **Fix**: Status synchronization (completed in M0_1)

### 5. Non-Standard Docker Practices
**Issue**: Custom solutions instead of Docker best practices
- **Examples**:
  - Custom token file system instead of environment variables
  - Complex entrypoint logic for simple authentication check
  - Volume mounting for configuration data
- **Standard approach**: Use environment variables and `--env-file`
- **Impact**: Harder to understand and maintain for Docker users

## Resolution Strategy

### Completed (M0_1 - Final)
- [x] Create simplified `.env` approach
- [x] Document technical debt issues
- [x] Fix documentation inconsistency  
- [x] **ACTUALLY COMPLETED**: Removed `setup-claude-auth.sh` script entirely (105 lines → 0 lines)
- [x] **ACTUALLY COMPLETED**: Authentication uses only `--env-file` approach (no volume mounting)
- [x] **ACTUALLY COMPLETED**: Single authentication method in all documentation

### Future Cleanup (Post-M1)
- [ ] Update remaining documentation references to old volume-based approach
- [ ] Clean up historical references in IMPLEMENTATION_PLAN.md and IMPLEMENTATION_LOG.md

## Resolved Issues

### 6. Print Statement Inconsistency - RESOLVED
**Issue**: Inconsistent debugging and progress output throughout benchmark system
- **Location**: `benchmark/benchmark.py` - 29 print statements scattered throughout codebase
- **Problems**: 
  - No structured logging levels
  - Mixed print/console.print usage
  - No persistent log storage
  - Difficult to monitor long-running processes
- **Solution implemented**: Comprehensive structured logging system
  - **Print Replacement**: All 29 print statements replaced with appropriate logging calls
  - **Log Levels**: INFO (progress), WARNING (issues), ERROR (failures), DEBUG (details)
  - **Dual Output**: Console and persistent file storage with rotation
  - **Docker Integration**: Volume mounting for real-time log monitoring
- **Impact resolved**: Users can now monitor benchmarks in real-time with `tail -f logs/benchmark.log`
- **Status**: COMPLETED (2025-08-06)

### 7. Docker Monitoring Visibility - RESOLVED
**Issue**: No way to monitor long-running benchmark executions inside Docker containers
- **Location**: Docker execution environment
- **Problems**:
  - No persistent log files accessible from host
  - Console output lost when container exits
  - Impossible to monitor progress of multi-hour benchmark runs
  - Debugging failures required container inspection
- **Solution implemented**: Docker log volume mounting and real-time access
  - **Volume Mount**: `-v $(pwd)/logs:/logs` in docker.sh
  - **Persistent Storage**: Logs survive container restarts
  - **Real-time Access**: `tail -f logs/benchmark.log` from host while container runs
  - **Rotation**: 10MB limit with 5 backups prevents disk space issues
- **Impact resolved**: Complete visibility into benchmark execution from host system
- **Status**: COMPLETED (2025-08-06)

## Critical Technical Debt (M2 FAILED TO FIX - STILL BLOCKING)

### 1. Broken Metrics Integration - CRITICAL BLOCKING
**Issue**: Wrapper calculates metrics but they NEVER reach benchmark results
- **Location**: Integration between `cc_wrapper.py` and `benchmark.py`
- **Evidence**: Latest benchmark run shows all zeros despite M2 "fix"
- **Impact**: Makes ALL benchmark results scientifically meaningless
- **Specifics**:
  - Wrapper shows: "Cost: $0.000024, Tokens: 3/1" internally
  - Results JSON shows: `cost: 0.0, tokens: 0`
  - Integration point in benchmark.py doesn't extract wrapper metrics
- **M2 Attempt**: Added metric tracking but didn't fix the actual problem
- **Priority**: CRITICAL - blocks everything, M2 marked DONE despite this
- **Status**: BROKEN - Must fix integration, not just add more code

### 2. Fake Token Counting - HIGH
**Issue**: Using word splits instead of real token counts
- **Location**: `cc_wrapper.py` lines with `len(prompt.split())`
- **Impact**: Token counts completely inaccurate
- **Specifics**:
  - Word count != token count (can be 2-3x off)
  - SDK may provide real counts but not being used
  - Hardcoded pricing will be wrong when models change
- **Status**: PARTIAL - M2 added fake tracking instead of real data

### 3. Documentation Line Number Drift - RESOLVED
**Issue**: CLAUDE.md references outdated line numbers
- **Status**: FIXED in M2 (one of the few things that actually worked)

### 4. Milestone Status Integrity - HIGH
**Issue**: Milestones marked "DONE" despite broken functionality
- **Examples**: 
  - M1 marked "SUCCESS" with all metrics showing zeros
  - M2 marked "COMPLETED" with integration completely broken
- **Impact**: False sense of progress, technical debt accumulation, undermines credibility
- **Resolution**: Updated to PARTIAL status, needs real implementation
- **Priority**: HIGH - integrity issue
- **Status**: PARTIALLY ADDRESSED - status updated but implementation still broken

## Lessons Learned

1. **Start Simple**: Begin with standard practices, add complexity only when needed
2. **Scope Control**: Keep scripts focused on single responsibility
3. **Documentation Sync**: Ensure status consistency across all project documents
4. **Docker Standards**: Use established Docker patterns rather than custom solutions
5. **Time Boxing**: Set strict limits to prevent gold-plating
6. **Integrity First**: Never claim success with known fake data
7. **Metrics Matter**: Without real metrics, benchmarks are meaningless

## Philosophy for Future Development

- **Functional > Perfect**: Working simple solution beats complex perfect solution
- **Standard > Custom**: Use established patterns unless there's a compelling reason not to
- **Incremental**: Build complexity incrementally rather than upfront
- **Time-Boxed**: Set strict time limits for implementation tasks