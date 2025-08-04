#!/usr/bin/env python
"""Test Claude Code SDK functionality on a sample exercise."""
import asyncio
from pathlib import Path
from claude_code_sdk import (
    query, 
    ClaudeCodeOptions
)

async def test_sdk():
    """Test SDK on beer-song exercise."""
    # Get project root and exercise directory
    project_root = Path(__file__).parent.parent
    exercise_dir = project_root / "polyglot-benchmark/python/exercises/practice/beer-song"
    
    # Configure SDK options
    options = ClaudeCodeOptions(
        max_turns=1,
        model="claude-sonnet-4-0",
        permission_mode="bypassPermissions",
        cwd=exercise_dir
    )
    
    # Create prompt for the exercise
    prompt = """You need to implement the recite function in beer_song.py.
Read the test file beer_song_test.py to understand what the function should do.
Then implement the recite function to pass all tests.
After implementing, run pytest beer_song_test.py to verify."""
    
    try:
        # Execute query
        print("Sending query to Claude Code SDK...")
        print("-" * 50)
        async for message in query(prompt=prompt, options=options):
            print(f"Message type: {type(message).__name__}")
            print(f"Content: {message}")
            print("-" * 30)
        print("-" * 50)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sdk())
    print(f"\nTest {'passed' if success else 'failed'}")