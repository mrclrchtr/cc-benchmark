# Benchmark Tracking System Architecture

## Overview

The tracking system provides real-time monitoring and state management for benchmark execution, enabling visibility into long-running benchmark processes and comprehensive performance analysis.

## Architecture Design

### Core Components

#### BenchmarkTracker (`benchmark/tracker.py`)
- **Purpose**: Central state management and statistics engine
- **Key Responsibilities**:
  - Thread-safe state persistence
  - Real-time progress calculation
  - Metrics aggregation across exercises
  - Report generation for analysis

#### State Model
- **Benchmark States**: `INITIALIZING`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`
- **Exercise States**: `PENDING`, `RUNNING`, `PASSED`, `FAILED`, `SKIPPED`, `ERROR`
- **Persistence**: JSON-based state files in `.tracker` directories
- **Concurrency**: Thread-safe operations for parallel benchmark execution

#### Integration Layer
- **Injection Points**: 
  - `benchmark.py:main()` - Tracker initialization
  - `benchmark.py:run_test_real()` - Exercise lifecycle hooks
- **Data Flow**: Exercise metrics → Tracker → State files → Monitor/Reports
- **Minimal Coupling**: Optional parameter passing maintains backward compatibility

### State Management

#### Persistence Strategy
```
tmp.benchmarks/
└── {timestamp}--{model}/
    ├── .tracker/
    │   ├── {run_id}.json         # Live state
    │   └── report_{run_id}.json  # Final report
    └── {language}/exercises/...
```

#### State Schema
- **Run Metadata**: model, languages, configuration
- **Progress Tracking**: completed/total exercises, pass/fail counts
- **Exercise Records**: Per-exercise status, duration, attempts, metrics
- **Metrics Collection**: tokens, cost, error types

### Monitoring System

#### Auto-Detection Architecture
- **Directory Scanning**: Pattern-based detection of benchmark directories
- **State Validation**: Verifies `.tracker` directory presence
- **Automatic Switching**: Seamless transition to new runs
- **Fallback Modes**: Graceful handling of missing/incomplete state

#### Display Pipeline
1. State retrieval from tracker
2. Statistics calculation
3. Visual formatting with progress bars and emojis
4. Terminal refresh with configurable intervals

## Key Design Decisions

### Thread Safety
- Lock-based synchronization for state mutations
- Atomic file writes prevent corruption
- Support for parallel exercise execution

### Extensibility Points
- **Custom Metrics**: Exercise results accept arbitrary metric dictionaries
- **Report Formats**: Export system designed for multiple output formats
- **State Hooks**: Integration points for future event systems

### Performance Considerations
- **Lazy Loading**: State files loaded on-demand
- **Incremental Updates**: Only modified state portions written
- **Efficient Aggregation**: Statistics cached and updated incrementally

## API Design

### Core Interface
```python
tracker.start_run(run_id, model, languages, total_exercises)
tracker.start_exercise(name, language, max_attempts)
tracker.complete_exercise(name, language, passed, metrics)
tracker.get_progress()  # Real-time progress
tracker.get_statistics()  # Aggregated metrics
tracker.export_report()  # Generate final report
```

### Monitoring Interface
```python
TrackerCLI.monitor(state_dir, refresh_interval, auto_detect)
TrackerCLI.find_latest_benchmark_dir()  # Auto-detection logic
```

## Usage Patterns

### Basic Monitoring
```bash
./monitor-benchmark.sh              # Auto-detect and monitor
./monitor-benchmark.sh --refresh 2  # Fast refresh
./monitor-benchmark.sh --no-auto    # Disable auto-switching
```

### Programmatic Access
- Direct tracker instantiation for custom tools
- State file parsing for external analysis
- Report generation for CI/CD pipelines

## Testing Strategy

### Test Coverage
- Unit tests: State management, calculations, serialization
- Integration tests: Benchmark.py integration, file I/O
- System tests: Monitor CLI, auto-detection

### Test Structure
- `tests/test_tracker.py` - Comprehensive test suite
- Fixtures for state files and mock runs
- Parametrized tests for multiple scenarios

## Future Architecture Considerations

### Potential Extensions
- **Event System**: Pub/sub for real-time notifications
- **Remote Monitoring**: WebSocket-based dashboard
- **Historical Analysis**: Time-series database integration
- **Distributed Tracking**: Multi-node benchmark coordination

### Scalability Paths
- **State Partitioning**: Split large state files by language/exercise
- **Streaming Updates**: Replace polling with event streams
- **Caching Layer**: In-memory state for high-frequency updates

## Technical Debt & Limitations

### Current Limitations
- Single-node tracking only
- File-based persistence (no database)
- Terminal-only monitoring interface
