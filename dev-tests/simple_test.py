#!/usr/bin/env python3
"""Simple test of Claude Code wrapper functionality."""
import os
import sys
from pathlib import Path

# Add benchmark directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "benchmark"))

from cc_wrapper import ClaudeCodeWrapper

def test_beer_song():
    """Test Claude Code wrapper on beer-song exercise."""
    project_root = Path(__file__).parent.parent
    exercise_dir = project_root / "polyglot-benchmark/python/exercises/practice/beer-song"
    
    if not exercise_dir.exists():
        print(f"Error: Exercise directory not found: {exercise_dir}")
        return False
    
    print(f"Testing Claude Code on beer-song exercise in {exercise_dir}")
    
    try:
        # Create wrapper
        wrapper = ClaudeCodeWrapper(verbose=True)
        wrapper.set_cwd(exercise_dir)
        
        # Read the current implementation
        beer_song_file = exercise_dir / "beer_song.py"
        test_file = exercise_dir / "beer_song_test.py"
        
        current_impl = beer_song_file.read_text()
        test_content = test_file.read_text()
        
        print(f"Current implementation:\n{current_impl}")
        print(f"Test file preview:\n{test_content[:500]}...")
        
        # Create prompt
        prompt = f"""You need to implement the recite function in beer_song.py to pass all tests.

Current implementation:
{current_impl}

Test file:
{test_content}

Please implement the recite function to make all tests pass. The function should generate verses of the "99 Bottles of Beer" song."""
        
        # Run Claude Code
        print("Sending prompt to Claude Code...")
        response = wrapper.run(prompt)
        
        print("Response received:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_beer_song()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")