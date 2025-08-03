# Claude Code Benchmark Vision (cc-benchmark)

## What This Is

A fork of aider's benchmark adapted to evaluate Claude Code performance. This enables direct comparison between aider and Claude Code using identical Exercism exercises.

## Why This Exists

- No benchmarking tool currently exists for Claude Code
- Claude Code is an agentic framework, not just a model - existing model benchmarks don't capture its capabilities  
- To fairly compare aider vs Claude Code, they need to run the same exercises
- Forking aider's proven approach is faster than building from scratch

## Technical Approach

### Safety First
Following aider's methodology, all code execution occurs within isolated Docker containers to prevent security risks from AI-generated code.

### What We're Forking
- **aider's polyglot-benchmark**: Curated collection of programming exercises from Exercism's language tracks
- **aider's benchmark harness**: Tools and infrastructure needed to run the benchmarking suite

### Adaptation Requirements
The harness will be modified to:
- Execute Claude Code instead of aider
- Handle Claude Code's CLI interface and workflow
- Maintain compatibility with aider's exercise format and scoring system

## v1.0 Goals (2 weeks)

- Fork aider's polyglot-benchmark and benchmark harness
- Analyze and adapt harness to execute Claude Code instead of aider
- Test default Claude Code configuration across all Exercism languages
- **Success criteria**: Claude Code can run the exercises and produce scores

## Future Iterations

### v1.1: Direct Comparison
- Compare Claude Code results against existing aider benchmark scores from the leaderboard
- Generate side-by-side performance comparisons using the same exercise sets
- Identify strengths and weaknesses of each approach

### v1.2: Configuration Testing  
- Test different Claude Code configurations (MCP servers, different models)
- Optimize configurations based on benchmark results
- Track performance improvements over different setups

## Implementation Notes

- **Language Coverage**: All Exercism languages supported by the original benchmark
- **Development Tool**: Using Claude Code itself to implement the benchmark adaptation
- **Scope**: Basic benchmarking functionality only - no web interfaces or enterprise features

## Expected Outcome

A practical tool that answers the question: "Should I use aider or Claude Code for my coding tasks?" by comparing Claude Code benchmark results against existing aider leaderboard data with quantitative analysis.