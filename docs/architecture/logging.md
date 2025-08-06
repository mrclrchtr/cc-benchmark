# Benchmark Logging System

## Overview

The cc-benchmark project uses a comprehensive structured logging system that replaces all print statements with proper logging calls. This provides real-time monitoring capabilities, persistent log storage, and improved debugging for long-running benchmark executions.

## Architecture

### Dual Output System
- **Console Output**: Real-time feedback during execution with clean formatting
- **File Output**: Persistent storage with detailed information and log rotation

### Log Levels
- **INFO**: Progress updates, status messages, successful operations
- **WARNING**: Non-critical issues, incomplete results, recovery situations
- **ERROR**: Test failures, critical errors, system problems
- **DEBUG**: Detailed operations, file copying, cleanup activities

## Configuration

### Setup Function
The logging system is initialized by the `setup_logging()` function in `benchmark/benchmark.py`:

```python
def setup_logging():
    """Configure logging to write to both console and file."""
    # Create logs directory if it doesn't exist
    log_dir = Path("/logs" if os.environ.get("AIDER_DOCKER") else "logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger with INFO level
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with simple formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler with rotation and detailed formatting
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "benchmark.log", 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

### Log Rotation
- **Maximum Size**: 10MB per log file
- **Backup Files**: 5 rotated backups maintained
- **Naming Pattern**: `benchmark.log`, `benchmark.log.1`, `benchmark.log.2`, etc.

## Docker Integration

### Volume Mounting
The Docker container mounts the host logs directory for persistent storage:

```bash
-v $(pwd)/logs:/logs
```

### Environment Detection
The logging system automatically detects Docker environment via `AIDER_DOCKER` environment variable:
- **Host**: Logs written to `logs/benchmark.log`
- **Docker**: Logs written to `/logs/benchmark.log` (mapped to host)

## Usage

### Real-time Monitoring
Monitor benchmark execution in real-time from the host system:

```bash
# Start benchmark in Docker (Terminal 1)
./docker/docker.sh
# Inside container: python benchmark/benchmark.py --your-options

# Monitor logs in real-time (Terminal 2)
tail -f logs/benchmark.log
```

### Log Analysis
Examine completed benchmark logs:

```bash
# View recent logs
tail -100 logs/benchmark.log

# Search for specific patterns
grep "ERROR\|WARNING" logs/benchmark.log

# Count test results
grep -c "Test passed" logs/benchmark.log
grep -c "Test failed" logs/benchmark.log
```

## Log Examples

### Typical Log Output
```
2025-08-06 00:15:02,077 - root - INFO - Processing files: hello_world.py
2025-08-06 00:15:02,078 - root - INFO - Starting attempt 1/2 for hello-world
2025-08-06 00:15:05,123 - root - INFO - Running unit tests for hello-world
2025-08-06 00:15:08,456 - root - INFO - Test passed on attempt 1/2 for hello-world
2025-08-06 00:15:08,457 - root - DEBUG - Cleaned up Rust target/debug directory: /path/to/target/debug
```

### Error Scenarios
```
2025-08-06 00:16:15,789 - root - ERROR - Not a directory: /invalid/path
2025-08-06 00:16:20,123 - root - WARNING - Tests timed out for complex-exercise
2025-08-06 00:16:25,456 - root - ERROR - Test error: SyntaxError: invalid syntax
```

### Progress Tracking
```
2025-08-06 00:10:00,000 - root - INFO - Using Claude Code with model: anthropic/claude-sonnet-4-20250514
2025-08-06 00:10:05,123 - root - INFO - Copying polyglot-benchmark/python -> 2025-08-06-00-10-00--python ...
2025-08-06 00:10:10,456 - root - INFO - Copy completed
2025-08-06 00:10:15,789 - root - INFO - Benchmark execution completed
```

## Troubleshooting

### Common Issues

#### Log File Not Created
**Problem**: `logs/benchmark.log` doesn't exist after running benchmarks

**Solutions**:
1. Check if `logs/` directory exists: `ls -la logs/`
2. Verify Docker volume mount: ensure `-v $(pwd)/logs:/logs` in docker run command
3. Check permissions: `ls -la logs/` (should be writable)

#### No Real-time Updates
**Problem**: `tail -f logs/benchmark.log` shows no new content during execution

**Solutions**:
1. Verify logging is initialized: look for initial log messages
2. Check if benchmark is actually running: monitor CPU usage
3. Ensure proper volume mounting in Docker

#### Log File Too Large
**Problem**: `benchmark.log` consuming excessive disk space

**Solutions**:
1. Log rotation should automatically manage this (10MB limit)
2. Check for rotation files: `ls -la logs/benchmark.log*`
3. Manually clean old logs if needed: `rm logs/benchmark.log.[2-5]`

### Debug Mode
For more detailed logging, modify the setup function to use DEBUG level:

```python
# In benchmark/benchmark.py setup_logging()
logger.setLevel(logging.DEBUG)
console_handler.setLevel(logging.DEBUG)
```

## Best Practices

### For Users
1. **Start Monitoring Early**: Begin `tail -f` before starting benchmarks
2. **Use Multiple Terminals**: One for execution, one for monitoring
3. **Save Important Logs**: Copy significant log files before they rotate
4. **Filter Noise**: Use `grep` to focus on relevant log levels

### For Developers
1. **Appropriate Log Levels**: Use INFO for progress, WARNING for issues, ERROR for failures
2. **Descriptive Messages**: Include context like exercise names and attempt numbers
3. **Structured Format**: Use consistent formatting for easy parsing
4. **Performance Impact**: Logging adds minimal overhead but avoid excessive DEBUG logging in production

## Integration with Rich Console
The logging system coexists with Rich library's `console.print()` for formatted statistical output. Rich output is preserved for:
- Statistical summaries
- Formatted tables
- Colored progress indicators

Regular logging handles:
- Progress updates
- Error messages
- Debug information
- Test execution details

This dual approach provides both structured logging and visually appealing output formatting.