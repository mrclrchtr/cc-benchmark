"""Pytest configuration and shared fixtures for cc-benchmark tests."""
import sys
import pytest
from pathlib import Path

# Add benchmark directory to path for all tests
benchmark_dir = Path(__file__).parent.parent / "benchmark"
if str(benchmark_dir) not in sys.path:
    sys.path.insert(0, str(benchmark_dir))


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "model_sync: Model synchronization tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_anthropic: Tests that require Anthropic SDK")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add slow marker to potentially slow tests
        if "sync" in item.name.lower() or "integration" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark model sync tests
        if "model" in item.name.lower():
            item.add_marker(pytest.mark.model_sync)


@pytest.fixture(scope="session")
def benchmark_directory():
    """Provide path to benchmark directory."""
    return benchmark_dir


@pytest.fixture(scope="session") 
def project_root():
    """Provide path to project root directory."""
    return Path(__file__).parent.parent


# Optional: Skip tests requiring Anthropic SDK if not available
def pytest_runtest_setup(item):
    """Setup hook to handle conditional test skipping."""
    if item.get_closest_marker("requires_anthropic"):
        try:
            import anthropic
        except ImportError:
            pytest.skip("Test requires Anthropic SDK - install with 'uv add anthropic'")