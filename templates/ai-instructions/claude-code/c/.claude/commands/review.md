# Code Review Command

Review the specified code or recent changes for:

## Quality Checks
1. **Code Quality**
   - Style compliance with project standards
   - Proper naming conventions
   - Appropriate comments and documentation

2. **Functionality**
   - Logic correctness
   - Edge case handling
   - Error handling completeness

3. **Performance**
   - Algorithmic efficiency
   - Resource usage
   - Potential bottlenecks

4. **Security**
   - Input validation
   - Sensitive data handling
   - Common vulnerability patterns

5. **Testing**
   - Test coverage adequacy
   - Test case completeness
   - Edge case coverage

## Output Format
Provide findings in this format:

### Strengths
- [Positive aspects of the code]

### Issues Found
- **[Severity]** [Location]: [Description]
  - Suggestion: [How to fix]

### Recommendations
- [Actionable improvements]

## Arguments
If `$ARGUMENTS` is provided, focus review on that specific file or component.
Otherwise, review recent changes or the most recently discussed code.
