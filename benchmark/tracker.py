#!/usr/bin/env python3
"""
Benchmark Tracking System

Provides real-time tracking and monitoring of benchmark execution state and progress.
Supports persistent state, progress monitoring, and statistics collection.
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExerciseStatus(Enum):
    """Status of individual exercise execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class BenchmarkState(Enum):
    """Overall benchmark run state."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExerciseResult:
    """Result data for a single exercise."""
    name: str
    language: str
    status: ExerciseStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary."""
        data['status'] = ExerciseStatus(data['status'])
        return cls(**data)


@dataclass
class BenchmarkRun:
    """Complete benchmark run information."""
    run_id: str
    state: BenchmarkState
    model: str
    languages: List[str]
    total_exercises: int
    completed_exercises: int = 0
    passed_exercises: int = 0
    failed_exercises: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    current_exercise: Optional[str] = None
    exercises: Dict[str, ExerciseResult] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['state'] = self.state.value
        data['exercises'] = {k: v.to_dict() for k, v in self.exercises.items()}
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary."""
        data['state'] = BenchmarkState(data['state'])
        exercises = data.get('exercises', {})
        data['exercises'] = {k: ExerciseResult.from_dict(v) for k, v in exercises.items()}
        return cls(**data)


class BenchmarkTracker:
    """
    Main tracking system for benchmark execution.
    
    Features:
    - Real-time state tracking
    - Progress monitoring
    - Persistent state management
    - Statistics collection
    - Thread-safe operations
    """
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize the benchmark tracker.
        
        Args:
            state_dir: Directory for storing state files (default: tmp.benchmarks/.tracker)
        """
        self.state_dir = state_dir or Path("tmp.benchmarks/.tracker")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_run: Optional[BenchmarkRun] = None
        self.run_history: List[BenchmarkRun] = []
        self._lock = threading.Lock()
        self._state_file: Optional[Path] = None
        self._auto_save_enabled = True
        self._stats_cache = {}
        
        # Load existing state if available
        self._load_latest_state()
        
        logger.info(f"BenchmarkTracker initialized with state_dir: {self.state_dir}")
    
    def start_run(self, run_id: str, model: str, languages: List[str], 
                  total_exercises: int, config: Optional[Dict] = None) -> BenchmarkRun:
        """
        Start a new benchmark run.
        
        Args:
            run_id: Unique identifier for the run
            model: Model being tested
            languages: List of programming languages
            total_exercises: Total number of exercises to run
            config: Additional configuration parameters
        
        Returns:
            BenchmarkRun instance
        """
        with self._lock:
            self.current_run = BenchmarkRun(
                run_id=run_id,
                state=BenchmarkState.INITIALIZING,
                model=model,
                languages=languages,
                total_exercises=total_exercises,
                start_time=datetime.now().isoformat(),
                config=config or {}
            )
            
            self._state_file = self.state_dir / f"{run_id}.json"
            self._save_state()
            
            logger.info(f"Started benchmark run: {run_id}")
            return self.current_run
    
    def update_state(self, state: BenchmarkState) -> None:
        """Update the overall benchmark state."""
        with self._lock:
            if not self.current_run:
                raise ValueError("No active benchmark run")
            
            self.current_run.state = state
            
            if state == BenchmarkState.RUNNING:
                if not self.current_run.start_time:
                    self.current_run.start_time = datetime.now().isoformat()
            elif state in [BenchmarkState.COMPLETED, BenchmarkState.FAILED, BenchmarkState.CANCELLED]:
                self.current_run.end_time = datetime.now().isoformat()
                if self.current_run.start_time:
                    start = datetime.fromisoformat(self.current_run.start_time)
                    end = datetime.fromisoformat(self.current_run.end_time)
                    self.current_run.duration_seconds = (end - start).total_seconds()
            
            self._save_state()
            logger.info(f"Benchmark state updated to: {state.value}")
    
    def start_exercise(self, name: str, language: str, max_attempts: int = 3) -> None:
        """
        Mark an exercise as started.
        
        Args:
            name: Exercise name
            language: Programming language
            max_attempts: Maximum number of attempts allowed
        """
        with self._lock:
            if not self.current_run:
                raise ValueError("No active benchmark run")
            
            exercise_key = f"{language}/{name}"
            
            if exercise_key not in self.current_run.exercises:
                self.current_run.exercises[exercise_key] = ExerciseResult(
                    name=name,
                    language=language,
                    status=ExerciseStatus.PENDING,
                    max_attempts=max_attempts
                )
            
            exercise = self.current_run.exercises[exercise_key]
            exercise.status = ExerciseStatus.RUNNING
            exercise.start_time = datetime.now().isoformat()
            exercise.attempts += 1
            
            self.current_run.current_exercise = exercise_key
            self.current_run.state = BenchmarkState.RUNNING
            
            self._save_state()
            logger.info(f"Started exercise: {exercise_key} (attempt {exercise.attempts}/{max_attempts})")
    
    def complete_exercise(self, name: str, language: str, passed: bool, 
                         error_message: Optional[str] = None,
                         metrics: Optional[Dict] = None) -> None:
        """
        Mark an exercise as completed.
        
        Args:
            name: Exercise name
            language: Programming language
            passed: Whether the exercise passed
            error_message: Error message if failed
            metrics: Additional metrics (tokens, cost, etc.)
        """
        with self._lock:
            if not self.current_run:
                raise ValueError("No active benchmark run")
            
            exercise_key = f"{language}/{name}"
            
            if exercise_key not in self.current_run.exercises:
                raise ValueError(f"Exercise {exercise_key} not found in current run")
            
            exercise = self.current_run.exercises[exercise_key]
            exercise.end_time = datetime.now().isoformat()
            
            if exercise.start_time:
                start = datetime.fromisoformat(exercise.start_time)
                end = datetime.fromisoformat(exercise.end_time)
                exercise.duration_seconds = (end - start).total_seconds()
            
            if passed:
                exercise.status = ExerciseStatus.PASSED
                self.current_run.passed_exercises += 1
            else:
                exercise.status = ExerciseStatus.FAILED
                self.current_run.failed_exercises += 1
            
            exercise.error_message = error_message
            if metrics:
                exercise.metrics.update(metrics)
            
            self.current_run.completed_exercises += 1
            self.current_run.current_exercise = None
            
            # Check if all exercises are completed
            if self.current_run.completed_exercises >= self.current_run.total_exercises:
                self.update_state(BenchmarkState.COMPLETED)
            
            self._save_state()
            logger.info(f"Completed exercise: {exercise_key} - {'PASSED' if passed else 'FAILED'}")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress information.
        
        Returns:
            Dictionary with progress metrics
        """
        with self._lock:
            if not self.current_run:
                return {"status": "No active benchmark run"}
            
            progress_pct = (self.current_run.completed_exercises / 
                          self.current_run.total_exercises * 100 
                          if self.current_run.total_exercises > 0 else 0)
            
            return {
                "run_id": self.current_run.run_id,
                "state": self.current_run.state.value,
                "model": self.current_run.model,
                "languages": self.current_run.languages,
                "current_exercise": self.current_run.current_exercise,
                "progress": {
                    "completed": self.current_run.completed_exercises,
                    "total": self.current_run.total_exercises,
                    "percentage": round(progress_pct, 2),
                    "passed": self.current_run.passed_exercises,
                    "failed": self.current_run.failed_exercises
                },
                "timing": {
                    "start_time": self.current_run.start_time,
                    "duration_seconds": self.current_run.duration_seconds,
                    "estimated_remaining": self._estimate_remaining_time()
                }
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detailed statistics for the current run.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        with self._lock:
            if not self.current_run:
                return {"status": "No active benchmark run"}
            
            # Language-specific stats
            lang_stats = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
            
            for exercise in self.current_run.exercises.values():
                lang_stats[exercise.language]["total"] += 1
                if exercise.status == ExerciseStatus.PASSED:
                    lang_stats[exercise.language]["passed"] += 1
                elif exercise.status == ExerciseStatus.FAILED:
                    lang_stats[exercise.language]["failed"] += 1
            
            # Calculate success rates
            for lang in lang_stats:
                total = lang_stats[lang]["total"]
                if total > 0:
                    lang_stats[lang]["success_rate"] = round(
                        lang_stats[lang]["passed"] / total * 100, 2
                    )
            
            # Token and cost metrics
            total_tokens = sum(
                e.metrics.get("total_tokens", 0) 
                for e in self.current_run.exercises.values()
            )
            total_cost = sum(
                e.metrics.get("cost", 0) 
                for e in self.current_run.exercises.values()
            )
            
            return {
                "run_id": self.current_run.run_id,
                "overall": {
                    "success_rate": round(
                        self.current_run.passed_exercises / 
                        max(self.current_run.completed_exercises, 1) * 100, 2
                    ),
                    "total_exercises": self.current_run.total_exercises,
                    "completed": self.current_run.completed_exercises,
                    "passed": self.current_run.passed_exercises,
                    "failed": self.current_run.failed_exercises
                },
                "by_language": dict(lang_stats),
                "metrics": {
                    "total_tokens": total_tokens,
                    "total_cost": round(total_cost, 4),
                    "avg_tokens_per_exercise": round(
                        total_tokens / max(self.current_run.completed_exercises, 1), 2
                    ),
                    "avg_cost_per_exercise": round(
                        total_cost / max(self.current_run.completed_exercises, 1), 4
                    )
                },
                "timing": {
                    "total_duration_seconds": self.current_run.duration_seconds,
                    "avg_exercise_duration": self._calculate_avg_exercise_duration()
                }
            }
    
    def export_report(self, output_path: Optional[Path] = None) -> Path:
        """
        Export a comprehensive report of the current run.
        
        Args:
            output_path: Path for the report file
        
        Returns:
            Path to the exported report
        """
        with self._lock:
            if not self.current_run:
                raise ValueError("No active benchmark run to export")
            
            if not output_path:
                output_path = self.state_dir / f"report_{self.current_run.run_id}.json"
            
            report = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "tracker_version": "1.0.0"
                },
                "run": self.current_run.to_dict(),
                "progress": self.get_progress(),
                "statistics": self.get_statistics()
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Exported report to: {output_path}")
            return output_path
    
    def _save_state(self) -> None:
        """Save current state to disk."""
        if not self._auto_save_enabled or not self.current_run:
            return
        
        try:
            with open(self._state_file, 'w') as f:
                json.dump(self.current_run.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_latest_state(self) -> None:
        """Load the most recent state file."""
        state_files = sorted(self.state_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        
        for state_file in state_files:
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    run = BenchmarkRun.from_dict(data)
                    
                    # Only load if run is not completed
                    if run.state not in [BenchmarkState.COMPLETED, BenchmarkState.CANCELLED]:
                        self.current_run = run
                        self._state_file = state_file
                        logger.info(f"Loaded existing run: {run.run_id}")
                        return
                    else:
                        self.run_history.append(run)
            except Exception as e:
                logger.warning(f"Failed to load state file {state_file}: {e}")
    
    def _estimate_remaining_time(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if not self.current_run or self.current_run.completed_exercises == 0:
            return None
        
        avg_duration = self._calculate_avg_exercise_duration()
        if not avg_duration:
            return None
        
        remaining = self.current_run.total_exercises - self.current_run.completed_exercises
        return round(avg_duration * remaining, 2)
    
    def _calculate_avg_exercise_duration(self) -> Optional[float]:
        """Calculate average exercise duration."""
        if not self.current_run:
            return None
        
        durations = [
            e.duration_seconds 
            for e in self.current_run.exercises.values() 
            if e.duration_seconds
        ]
        
        if not durations:
            return None
        
        return round(sum(durations) / len(durations), 2)


class TrackerCLI:
    """Command-line interface for monitoring benchmark progress."""
    
    @staticmethod
    def find_latest_benchmark_dir(base_dir: Path = None) -> Optional[Path]:
        """Find the latest benchmark directory."""
        if base_dir is None:
            base_dir = Path("tmp.benchmarks")
        
        if not base_dir.exists():
            return None
        
        # Find directories matching benchmark pattern (YYYY-MM-DD-HH-MM-SS--)
        benchmark_dirs = [
            d for d in base_dir.iterdir() 
            if d.is_dir() and d.name[:19].replace('-', '').isdigit()
        ]
        
        if not benchmark_dirs:
            return None
        
        # Sort by name (which includes timestamp) and return latest
        return sorted(benchmark_dirs, reverse=True)[0]
    
    @staticmethod
    def monitor(state_dir: Optional[Path] = None, refresh_interval: int = 5, auto_detect: bool = True):
        """
        Monitor benchmark progress in real-time with auto-detection of new runs.
        
        Args:
            state_dir: Directory containing state files (if None, auto-detect)
            refresh_interval: Refresh interval in seconds
            auto_detect: Automatically detect and switch to new benchmark runs
        """
        current_run_dir = None
        tracker = None
        last_check_time = 0
        no_run_counter = 0
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Auto-detect new runs every refresh cycle if enabled
                if auto_detect and (time.time() - last_check_time > refresh_interval or tracker is None):
                    latest_dir = TrackerCLI.find_latest_benchmark_dir()
                    
                    if latest_dir and latest_dir != current_run_dir:
                        # New benchmark detected
                        new_state_dir = latest_dir / ".tracker"
                        if new_state_dir.exists():
                            if current_run_dir:
                                print(f"🔄 Switching to new benchmark: {latest_dir.name}")
                                time.sleep(1)
                            current_run_dir = latest_dir
                            state_dir = new_state_dir
                            tracker = BenchmarkTracker(state_dir)
                            no_run_counter = 0
                    
                    last_check_time = time.time()
                
                # Initialize tracker if needed
                if tracker is None and state_dir:
                    tracker = BenchmarkTracker(state_dir)
                
                print("=" * 60)
                print("BENCHMARK TRACKING MONITOR")
                if auto_detect:
                    print("(Auto-detecting new runs)")
                print("=" * 60)
                
                if tracker is None:
                    no_run_counter += 1
                    dots = "." * (no_run_counter % 4)
                    print(f"\n⏳ Waiting for benchmark to start{dots}")
                    print("\nNo active benchmark found.")
                    print("Start a benchmark with: ./run-benchmark.sh")
                    print(f"\n[Checking every {refresh_interval}s, Ctrl+C to exit]")
                else:
                    progress = tracker.get_progress()
                    stats = tracker.get_statistics()
                    
                    if "status" in progress:
                        # No active run in this tracker
                        if progress['status'] == "No active benchmark run":
                            # Try to reload latest state
                            tracker._load_latest_state()
                            progress = tracker.get_progress()
                            stats = tracker.get_statistics()
                    
                    if "status" in progress and progress['status'] == "No active benchmark run":
                        print(f"\n📁 Monitoring: {current_run_dir.name}")
                        print("⏸️  Benchmark completed or not yet started")
                        print("\nWaiting for new activity...")
                    else:
                        # Display run information
                        print(f"\n📊 Run ID: {progress['run_id']}")
                        
                        # Show state with emoji
                        state_emoji = {
                            "initializing": "🔧",
                            "running": "🏃",
                            "completed": "✅",
                            "failed": "❌",
                            "paused": "⏸️",
                            "cancelled": "🚫"
                        }.get(progress['state'].lower(), "❓")
                        print(f"{state_emoji} State: {progress['state']}")
                        
                        print(f"🤖 Model: {progress['model']}")
                        print(f"🗣️ Languages: {', '.join(progress['languages'])}")
                        
                        if progress['current_exercise']:
                            print(f"\n▶️  Currently Running: {progress['current_exercise']}")
                        
                        # Progress bar
                        completed = progress['progress']['completed']
                        total = progress['progress']['total']
                        percentage = progress['progress']['percentage']
                        
                        bar_length = 30
                        filled = int(bar_length * completed / max(total, 1))
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        print(f"\n📈 Progress: [{bar}] {completed}/{total} ({percentage}%)")
                        print(f"✅ Passed: {progress['progress']['passed']}")
                        print(f"❌ Failed: {progress['progress']['failed']}")
                        
                        if progress['timing']['estimated_remaining']:
                            remaining = progress['timing']['estimated_remaining']
                            mins, secs = divmod(int(remaining), 60)
                            print(f"\n⏱️  Estimated Time Remaining: {mins}m {secs}s")
                        
                        if "overall" in stats:
                            success_rate = stats['overall']['success_rate']
                            if success_rate >= 80:
                                rate_emoji = "🎯"
                            elif success_rate >= 60:
                                rate_emoji = "📊"
                            else:
                                rate_emoji = "📉"
                            print(f"\n{rate_emoji} Success Rate: {success_rate}%")
                            
                            if stats['by_language']:
                                print("\n📚 By Language:")
                                for lang, lang_stats in stats['by_language'].items():
                                    rate = lang_stats.get('success_rate', 0)
                                    passed = lang_stats['passed']
                                    total_lang = lang_stats['total']
                                    
                                    # Language emoji
                                    lang_emoji = {
                                        'python': '🐍',
                                        'javascript': '📜',
                                        'go': '🐹',
                                        'rust': '🦀',
                                        'java': '☕',
                                        'cpp': '⚙️'
                                    }.get(lang.lower(), '📝')
                                    
                                    print(f"  {lang_emoji} {lang}: {rate}% ({passed}/{total_lang})")
                            
                            # Show metrics if available
                            if stats.get('metrics') and stats['metrics'].get('total_cost', 0) > 0:
                                print(f"\n💰 Total Cost: ${stats['metrics']['total_cost']:.4f}")
                                print(f"🔤 Total Tokens: {stats['metrics']['total_tokens']:,}")
                
                if auto_detect:
                    print(f"\n[Auto-refresh every {refresh_interval}s, Ctrl+C to exit]")
                else:
                    print(f"\n[Refreshing every {refresh_interval}s, Ctrl+C to exit]")
                
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Parse arguments
        state_dir = None
        if len(sys.argv) > 2 and sys.argv[2] != "None":
            state_dir = Path(sys.argv[2])
        
        refresh = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        auto_detect = True
        if len(sys.argv) > 4:
            auto_detect = sys.argv[4].lower() in ['true', '1', 'yes']
        
        TrackerCLI.monitor(state_dir=state_dir, refresh_interval=refresh, auto_detect=auto_detect)
    else:
        print("Usage: python tracker.py monitor [state_dir] [refresh_interval] [auto_detect]")