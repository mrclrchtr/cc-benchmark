# Claude Code Benchmark Vision (cc-benchmark)

## Core Hypothesis

Claude Code outperforms aider at solving Exercism programming exercises. This project will quantitatively prove or disprove this hypothesis.

## What This Actually Is

A personal benchmarking tool that:
- Forks aider's proven benchmark infrastructure (MIT licensed)
- Runs identical Exercism exercises through Claude Code
- Produces quantitative comparisons between Claude Code and aider

## Why Build This

- **Personal validation**: I believe Claude Code is better and want data to support/refute this
- **No existing comparison**: Despite both tools being popular, no head-to-head comparison exists
- **Community value**: Other developers choosing between aider and Claude Code need objective data

## Success Metrics

### Primary Metric
- **Pass rate**: Percentage of exercises solved correctly on first attempt

### Secondary Metrics  
- **Iterations to solution**: Number of attempts needed to pass all tests
- **Code quality**: Cyclomatic complexity, line count, readability scores
- **Failure analysis**: Categories of exercises where each tool struggles

## Technical Approach

### Proven Foundation
- Fork aider's polyglot-benchmark (validated to work with Claude Code)
- Maintain Docker-based isolation for safe code execution
- Preserve exercise format compatibility for direct comparison

### Key Adaptations
- Replace aider CLI calls with Claude Code CLI interface
- Parse Claude Code output format for test results
- Handle Claude Code's interactive workflow programmatically

## Scope Boundaries

### What This IS
- A benchmarking tool for Exercism exercises
- A quantitative comparison framework
- A personal project with community benefit

### What This IS NOT
- A comprehensive AI coding assistant evaluation
- A real-world development workflow test
- A sponsored or official comparison

## v1.0 Definition of Done

Claude Code can:
1. Run all exercises from aider's polyglot-benchmark
2. Produce pass/fail scores for each exercise
3. Generate comparison data against aider's published results
4. Output results in a reproducible, shareable format

## Risk Acknowledgments

- **Bias risk**: I expect Claude Code to win. Results will be published regardless of outcome.
- **Scope risk**: Exercism exercises may not represent real-world coding tasks
- **Cost risk**: API costs are acceptable for personal project scope
- **Maintenance risk**: Claude Code interface changes will require updates

## Future Considerations

Once baseline comparison is established:
- Test different Claude Code configurations
- Expand to non-Exercism benchmarks if results prove interesting
- Open source for community contributions and validation

## Bottom Line

This is a personal project to quantify my belief that Claude Code > aider at code generation tasks. The benchmarking framework will be objective, even if my hypothesis isn't. Results will be published whether they confirm or refute my expectations.