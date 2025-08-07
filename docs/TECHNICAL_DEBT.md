# Technical Debt

Current technical debt and areas for improvement in the cc-benchmark project.

## Active Technical Debt

### Optional Enhancements
- **Exact Token Counting**: Currently using character-based estimation (3.5-4.0 chars/token). Could add ANTHROPIC_API_KEY for precise SDK-based counting
- **Error Tracking Validation**: Error counting logic exists but hasn't been tested with actual failures
- **Comprehensive Benchmark Suite**: Need to run full 50+ exercise validation at scale

## Lessons Learned

1. **Start Simple**: Begin with standard practices, add complexity only when needed
2. **Scope Control**: Keep scripts focused on single responsibility
3. **Documentation Sync**: Ensure status consistency across all project documents
4. **Docker Standards**: Use established Docker patterns rather than custom solutions
5. **Time Boxing**: Set strict limits to prevent gold-plating
6. **Integrity First**: Never claim success with known fake data
7. **Metrics Matter**: Without real metrics, benchmarks are meaningless
8. **Documentation Lag**: Always update docs immediately after fixes to prevent confusion
9. **Verify Claims**: Test actual functionality before documenting failures or successes

## Philosophy for Future Development

- **Functional > Perfect**: Working simple solution beats complex perfect solution
- **Standard > Custom**: Use established patterns unless there's a compelling reason not to
- **Incremental**: Build complexity incrementally rather than upfront
- **Time-Boxed**: Set strict time limits for implementation tasks