#!/usr/bin/env python3
"""
Test suite for the benchmark tracking system.
"""

import json
import tempfile
import time
from pathlib import Path
import pytest
import sys
import os

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

from tracker import (
    BenchmarkTracker,
    BenchmarkState,
    ExerciseStatus,
    ExerciseResult,
    BenchmarkRun
)


class TestBenchmarkTracker:
    """Test suite for BenchmarkTracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BenchmarkTracker(state_dir=Path(tmpdir))
            assert tracker.state_dir == Path(tmpdir)
            assert tracker.current_run is None
            assert tracker.run_history == []
    
    def test_start_run(self):
        """Test starting a new benchmark run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BenchmarkTracker(state_dir=Path(tmpdir))
            
            run = tracker.start_run(
                run_id="test-run-001",
                model="claude-3-sonnet",
                languages=["python", "javascript"],
                total_exercises=10,
                config={"threads": 1}
            )
            
            assert run.run_id == "test-run-001"
            assert run.model == "claude-3-sonnet"
            assert run.languages == ["python", "javascript"]
            assert run.total_exercises == 10
            assert run.state == BenchmarkState.INITIALIZING
            assert run.config["threads"] == 1
            
            # Check state file was created
            state_file = Path(tmpdir) / "test-run-001.json"
            assert state_file.exists()
    
    def test_exercise_lifecycle(self):
        """Test exercise start and completion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BenchmarkTracker(state_dir=Path(tmpdir))
            
            # Start a run
            tracker.start_run(
                run_id="test-run-002",
                model="claude-3-opus",
                languages=["python"],
                total_exercises=2
            )
            
            # Start an exercise
            tracker.start_exercise("hello-world", "python", max_attempts=3)
            
            assert tracker.current_run.current_exercise == "python/hello-world"
            exercise = tracker.current_run.exercises["python/hello-world"]
            assert exercise.status == ExerciseStatus.RUNNING
            assert exercise.attempts == 1
            
            # Complete the exercise
            tracker.complete_exercise(
                "hello-world",
                "python",
                passed=True,
                metrics={"cost": 0.05, "tokens": 1000}
            )
            
            assert tracker.current_run.current_exercise is None
            assert exercise.status == ExerciseStatus.PASSED
            assert exercise.metrics["cost"] == 0.05
            assert tracker.current_run.passed_exercises == 1
            assert tracker.current_run.completed_exercises == 1
    
    def test_progress_tracking(self):
        """Test progress reporting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BenchmarkTracker(state_dir=Path(tmpdir))
            
            tracker.start_run(
                run_id="test-run-003",
                model="claude-3-haiku",
                languages=["go", "rust"],
                total_exercises=4
            )
            
            # Complete some exercises
            tracker.start_exercise("exercise1", "go")
            tracker.complete_exercise("exercise1", "go", passed=True)
            
            tracker.start_exercise("exercise2", "rust")
            tracker.complete_exercise("exercise2", "rust", passed=False)
            
            progress = tracker.get_progress()
            
            assert progress["progress"]["completed"] == 2
            assert progress["progress"]["total"] == 4
            assert progress["progress"]["percentage"] == 50.0
            assert progress["progress"]["passed"] == 1
            assert progress["progress"]["failed"] == 1
    
    def test_statistics_calculation(self):
        """Test statistics generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BenchmarkTracker(state_dir=Path(tmpdir))
            
            tracker.start_run(
                run_id="test-run-004",
                model="claude-3-sonnet",
                languages=["python", "javascript"],
                total_exercises=4
            )
            
            # Add exercises with metrics
            exercises = [
                ("exercise1", "python", True, {"cost": 0.02, "total_tokens": 500}),
                ("exercise2", "python", False, {"cost": 0.03, "total_tokens": 750}),
                ("exercise3", "javascript", True, {"cost": 0.01, "total_tokens": 250}),
                ("exercise4", "javascript", True, {"cost": 0.04, "total_tokens": 1000}),
            ]
            
            for name, lang, passed, metrics in exercises:
                tracker.start_exercise(name, lang)
                time.sleep(0.01)  # Small delay for duration calculation
                tracker.complete_exercise(name, lang, passed=passed, metrics=metrics)
            
            stats = tracker.get_statistics()
            
            # Check overall stats
            assert stats["overall"]["completed"] == 4
            assert stats["overall"]["passed"] == 3
            assert stats["overall"]["failed"] == 1
            assert stats["overall"]["success_rate"] == 75.0
            
            # Check language stats
            assert stats["by_language"]["python"]["total"] == 2
            assert stats["by_language"]["python"]["passed"] == 1
            assert stats["by_language"]["python"]["success_rate"] == 50.0
            
            assert stats["by_language"]["javascript"]["total"] == 2
            assert stats["by_language"]["javascript"]["passed"] == 2
            assert stats["by_language"]["javascript"]["success_rate"] == 100.0
            
            # Check metrics
            assert stats["metrics"]["total_tokens"] == 2500
            assert stats["metrics"]["total_cost"] == 0.10
            assert stats["metrics"]["avg_tokens_per_exercise"] == 625.0
    
    def test_state_persistence(self):
        """Test saving and loading state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            
            # Create and save a run
            tracker1 = BenchmarkTracker(state_dir=state_dir)
            tracker1.start_run(
                run_id="persistent-run",
                model="claude-3-opus",
                languages=["python"],
                total_exercises=3
            )
            tracker1.start_exercise("test", "python")
            tracker1.complete_exercise("test", "python", passed=True)
            
            # Load in a new tracker instance
            tracker2 = BenchmarkTracker(state_dir=state_dir)
            
            assert tracker2.current_run is not None
            assert tracker2.current_run.run_id == "persistent-run"
            assert tracker2.current_run.completed_exercises == 1
            assert tracker2.current_run.passed_exercises == 1
    
    def test_export_report(self):
        """Test report export functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BenchmarkTracker(state_dir=Path(tmpdir))
            
            tracker.start_run(
                run_id="report-test",
                model="claude-3-sonnet",
                languages=["python"],
                total_exercises=1
            )
            
            tracker.start_exercise("hello", "python")
            tracker.complete_exercise("hello", "python", passed=True)
            
            report_path = tracker.export_report()
            
            assert report_path.exists()
            
            with open(report_path) as f:
                report = json.load(f)
            
            assert "metadata" in report
            assert "run" in report
            assert "progress" in report
            assert "statistics" in report
            assert report["run"]["run_id"] == "report-test"


class TestExerciseResult:
    """Test suite for ExerciseResult class."""
    
    def test_exercise_result_creation(self):
        """Test creating an exercise result."""
        result = ExerciseResult(
            name="two-fer",
            language="python",
            status=ExerciseStatus.PASSED,
            attempts=1,
            metrics={"cost": 0.02}
        )
        
        assert result.name == "two-fer"
        assert result.language == "python"
        assert result.status == ExerciseStatus.PASSED
        assert result.metrics["cost"] == 0.02
    
    def test_exercise_result_serialization(self):
        """Test serializing and deserializing exercise results."""
        result = ExerciseResult(
            name="leap",
            language="go",
            status=ExerciseStatus.FAILED,
            error_message="Test timeout"
        )
        
        # Serialize
        data = result.to_dict()
        assert data["status"] == "failed"
        assert data["error_message"] == "Test timeout"
        
        # Deserialize
        result2 = ExerciseResult.from_dict(data)
        assert result2.name == "leap"
        assert result2.status == ExerciseStatus.FAILED


class TestBenchmarkRun:
    """Test suite for BenchmarkRun class."""
    
    def test_benchmark_run_creation(self):
        """Test creating a benchmark run."""
        run = BenchmarkRun(
            run_id="test-123",
            state=BenchmarkState.RUNNING,
            model="claude-3-opus",
            languages=["python", "rust"],
            total_exercises=20
        )
        
        assert run.run_id == "test-123"
        assert run.state == BenchmarkState.RUNNING
        assert run.model == "claude-3-opus"
        assert len(run.languages) == 2
    
    def test_benchmark_run_serialization(self):
        """Test serializing and deserializing benchmark runs."""
        run = BenchmarkRun(
            run_id="serialize-test",
            state=BenchmarkState.COMPLETED,
            model="claude-3-sonnet",
            languages=["javascript"],
            total_exercises=5,
            completed_exercises=5,
            passed_exercises=4
        )
        
        # Add an exercise
        run.exercises["js/test"] = ExerciseResult(
            name="test",
            language="javascript",
            status=ExerciseStatus.PASSED
        )
        
        # Serialize
        data = run.to_dict()
        assert data["state"] == "completed"
        assert "js/test" in data["exercises"]
        
        # Deserialize
        run2 = BenchmarkRun.from_dict(data)
        assert run2.run_id == "serialize-test"
        assert run2.state == BenchmarkState.COMPLETED
        assert "js/test" in run2.exercises
        assert run2.exercises["js/test"].status == ExerciseStatus.PASSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])