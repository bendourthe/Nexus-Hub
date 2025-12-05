---
name: create-custom-command
description: Create custom slash commands for Claude Code to automate repetitive workflows
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Workflow
tags: [workflow, automation, commands, productivity, claude-code]
priority: HIGH
---

# Create Custom Slash Commands

Create custom slash commands for Claude Code that automate repetitive development workflows, enforce best practices, and streamline common tasks. Transform multi-step processes into single-command operations.

## When to Use This Skill

Use this skill when:
- ✅ You perform repetitive development workflows multiple times
- ✅ You want to standardize team processes and conventions
- ✅ You need to enforce code quality and review standards
- ✅ You want to simplify complex multi-step operations
- ✅ You need project-specific automation
- ✅ You want to reduce cognitive load for common tasks
- ✅ You're onboarding team members and want consistent workflows
- ✅ You need to document and codify development processes

**Custom commands are especially valuable when**:
- Your team has established conventions and checklists
- You want to automate code review, testing, or deployment steps
- You need to enforce documentation or testing standards
- You want to reduce human error in repetitive tasks

## What This Skill Does

This skill teaches you to create custom slash commands that:

### 1. Automate Workflows
- Convert multi-step processes into single commands
- Reduce manual work and potential errors
- Standardize team practices
- Speed up development cycles

### 2. Enforce Standards
- Apply code quality checks automatically
- Ensure documentation requirements are met
- Validate testing coverage
- Maintain architectural consistency

### 3. Simplify Complex Tasks
- Break down complicated operations into clear steps
- Provide contextual guidance and checklists
- Handle edge cases and error conditions
- Document best practices

### 4. Improve Collaboration
- Share workflows across team members
- Onboard new developers quickly
- Maintain consistency across projects
- Document tribal knowledge

## Command Benefits

### Productivity Gains
- **Time Savings**: Reduce 10-step processes to 1 command
- **Fewer Errors**: Automated checklists prevent missed steps
- **Cognitive Load**: Less to remember, more focus on code
- **Consistency**: Same quality every time

### Team Collaboration
- **Shared Standards**: Everyone follows same practices
- **Onboarding**: New team members learn by example
- **Documentation**: Commands document processes
- **Knowledge Transfer**: Tribal knowledge becomes codified

### Quality Assurance
- **Checklists**: Never miss important steps
- **Reviews**: Systematic code review processes
- **Testing**: Automated test generation and validation
- **Security**: Built-in security check workflows

## Prerequisites

### Required
- Claude Code installed and configured
- Access to project `.claude/` directory
- Basic understanding of markdown formatting
- Knowledge of workflows you want to automate

### Recommended
- Familiarity with slash command syntax
- Understanding of your project's conventions
- Team consensus on workflows (for team commands)
- Version control for command files

### Knowledge
- Development workflows and best practices
- Your project's specific requirements
- Common pain points in your development process
- Team standards and conventions

## Understanding Slash Commands

### What Are Slash Commands?

Slash commands are **custom prompts stored as markdown files** that expand into detailed instructions when invoked in Claude Code.

**Basic Concept**:
```
/.claude/commands/review-code.md → /review-code → [Full review checklist]
```

### Command Structure

**File Location**: `.claude/commands/<command-name>.md`

**Basic Format**:
```markdown
<!-- Optional: Command metadata -->
<!--
name: command-name
description: What this command does
-->

# Main prompt that Claude will receive

Your detailed instructions here...
```

### How Commands Work

1. **Create**: Write markdown file in `.claude/commands/`
2. **Name**: Filename becomes command name (minus `.md`)
3. **Invoke**: Type `/command-name` in Claude Code
4. **Expand**: Command content replaces the slash command
5. **Execute**: Claude follows the instructions

**Example**:
```bash
# You create:
.claude/commands/review-pr.md

# You type:
/review-pr

# Claude receives:
[Full content of review-pr.md as instructions]
```

## Instructions

### Step 1: Create Commands Directory

Set up the directory structure for custom commands:

```bash
# Create commands directory
mkdir -p .claude/commands

# Verify structure
ls -la .claude/
```

**Expected structure**:
```
project-root/
├── .claude/
│   ├── CLAUDE.md              # Project instructions
│   └── commands/              # Custom commands directory
│       ├── review-code.md     # Code review command
│       ├── test-feature.md    # Test generation command
│       └── deploy-check.md    # Deployment checklist
```

### Step 2: Identify Workflow to Automate

Before creating a command, identify the workflow:

**Questions to Ask**:
- What steps do I repeat frequently?
- What could I automate or standardize?
- What do team members ask about repeatedly?
- What checklists do I use manually?
- What takes too long or is error-prone?

**Example Workflows to Automate**:
- Code review checklists
- Test case generation
- Documentation updates
- Bug fix workflows
- Feature implementation templates
- Deployment preparation
- Security audits
- Performance optimization

### Step 3: Write Your First Command

Create a simple command to understand the format.

**Example: Code Review Command**

Create `.claude/commands/review-code.md`:

```markdown
# Code Review Checklist

Perform a comprehensive code review following these criteria:

## 1. Code Quality
- [ ] Code follows project style guidelines
- [ ] Functions are well-named and focused
- [ ] No obvious code smells or anti-patterns
- [ ] Appropriate use of design patterns
- [ ] DRY principle followed (no duplication)

## 2. Functionality
- [ ] Code solves the stated problem
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs or logic errors

## 3. Testing
- [ ] Tests are included for new functionality
- [ ] Existing tests still pass
- [ ] Test coverage is adequate
- [ ] Tests follow naming conventions

## 4. Documentation
- [ ] Functions have docstrings
- [ ] Complex logic is commented
- [ ] README updated if needed
- [ ] API documentation updated

## 5. Security
- [ ] No obvious security vulnerabilities
- [ ] Input validation is present
- [ ] Sensitive data is protected
- [ ] Dependencies are secure

## 6. Performance
- [ ] No obvious performance issues
- [ ] Appropriate data structures used
- [ ] Database queries are optimized
- [ ] No unnecessary computation

## Actions

Review the code and provide:
1. **Summary**: Overall assessment of code quality
2. **Issues Found**: Specific problems categorized by severity
3. **Recommendations**: Concrete suggestions for improvement
4. **Approval Status**: Ready to merge, needs changes, or needs discussion
```

### Step 4: Test Your Command

Test the command in Claude Code:

```bash
# In Claude Code chat:
/review-code

# Claude will receive the full checklist and perform review
```

**Verify**:
- [ ] Command is recognized
- [ ] Content expands correctly
- [ ] Instructions are clear to Claude
- [ ] Output meets your needs

### Step 5: Add Command Parameters

Make commands flexible with parameters.

**Example: Test Generation with Parameters**

Create `.claude/commands/generate-tests.md`:

```markdown
# Generate Test Cases

Generate comprehensive test cases for the specified functionality.

## Instructions

When this command is invoked as `/generate-tests <module-name>`:

1. **Analyze Module**: Examine the module/function/class specified
2. **Identify Test Cases**: Determine what needs testing
3. **Generate Tests**: Create test code with these characteristics:
   - Follow project testing conventions
   - Include unit tests for individual functions
   - Add integration tests for workflows
   - Cover edge cases and error conditions
   - Use appropriate fixtures and mocks
   - Follow AAA pattern (Arrange-Act-Assert)

4. **Test Categories**:
   - **Happy Path**: Normal, expected usage
   - **Edge Cases**: Boundaries, limits, special values
   - **Error Cases**: Invalid inputs, exceptions
   - **Integration**: Component interactions

5. **Test Quality**:
   - Clear, descriptive test names
   - Comprehensive coverage (aim for 90%+)
   - Fast execution (< 100ms per test)
   - Independent tests (no shared state)
   - Deterministic results

## Output Format

Provide:
1. Test file location and name
2. Complete test code ready to use
3. Coverage report showing what's tested
4. Instructions for running the tests
5. Any additional test data or fixtures needed

## Example Usage

```bash
/generate-tests src/auth/jwt_service.py
/generate-tests UserController
/generate-tests calculateOrderTotal
```
```

### Step 6: Create Advanced Commands

Build complex commands with conditional logic and workflows.

**Example: Bug Fix Workflow**

Create `.claude/commands/fix-bug.md`:

```markdown
# Bug Fix Workflow

Guide through systematic bug fixing process.

## Phase 1: Understand the Bug

1. **Reproduce**: Can you reproduce the bug?
   - Ask for: Steps to reproduce, expected vs actual behavior
   - Request: Stack traces, error messages, logs

2. **Scope**: What's affected?
   - Identify affected components
   - Determine severity (critical, major, minor)
   - Check if bug exists in other areas

3. **Root Cause**: Why is it happening?
   - Trace through execution flow
   - Identify where behavior diverges
   - Document root cause clearly

## Phase 2: Create Reproduction Test

**CRITICAL**: Write a failing test first!

1. Create test file in `tests/bug_fixes/`
2. Name: `test_bug_<issue-number>_<description>.py`
3. Test must:
   - Reproduce the bug (fail initially)
   - Be minimal and focused
   - Have clear assertion showing expected behavior

Example:
```python
def test_bug_123_division_by_zero_in_refund():
    """Test that refund handles zero quantity items."""
    # Arrange
    order = create_order_with_zero_quantity_item()

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot process zero quantity"):
        calculate_refund(order)
```

## Phase 3: Implement Fix

1. **Fix**: Implement minimal fix to make test pass
2. **Verify**: Ensure test now passes
3. **Regression**: Run full test suite
4. **Review**: Check for similar bugs elsewhere

## Phase 4: Documentation

1. **Code Comments**: Add inline comments explaining the fix
2. **DEVLOG**: Update with:
   - Bug description and root cause
   - Solution approach
   - Test iterations
3. **Commit Message**: Clear description

## Phase 5: Final Checklist

- [ ] Failing test created and committed
- [ ] Fix implemented (test passes)
- [ ] Full test suite passes
- [ ] Similar bugs checked and fixed
- [ ] DEVLOG.md updated
- [ ] Code reviewed for quality
- [ ] Ready to commit

## Commit Format

```bash
git commit -m "fix: <description>

Bug: <issue number or description>
Root Cause: <why bug occurred>
Solution: <how it was fixed>
Tests: Added test_bug_<number>_<description>

Closes #<issue-number>"
```

Follow this workflow step by step. Don't skip phases.
```

### Step 7: Organize Commands by Category

Structure commands for easy discovery and maintenance.

**Recommended Organization**:

```
.claude/commands/
├── code-quality/
│   ├── review-code.md
│   ├── refactor-code.md
│   └── optimize-performance.md
├── testing/
│   ├── generate-tests.md
│   ├── test-coverage.md
│   └── integration-tests.md
├── documentation/
│   ├── generate-api-docs.md
│   ├── update-readme.md
│   └── add-docstrings.md
├── workflows/
│   ├── fix-bug.md
│   ├── deploy-check.md
│   └── pre-commit.md
└── quick-commands/
    ├── format-code.md
    ├── check-deps.md
    └── run-tests.md
```

**Note**: Currently Claude Code reads all `.md` files in `.claude/commands/` directly. Subdirectories are for **organizational purposes** in your file system but commands should still work.

### Step 8: Add Command Documentation

Create an index of available commands.

**Create `.claude/commands/README.md`**:

```markdown
# Custom Commands Index

## Code Quality
- `/review-code` - Comprehensive code review checklist
- `/refactor-code` - Systematic refactoring guide
- `/optimize-performance` - Performance optimization workflow

## Testing
- `/generate-tests` - Generate comprehensive test cases
- `/test-coverage` - Analyze and improve test coverage
- `/integration-tests` - Create integration test suite

## Documentation
- `/generate-api-docs` - Generate API documentation
- `/update-readme` - Update README with latest changes
- `/add-docstrings` - Add/improve function docstrings

## Workflows
- `/fix-bug` - Systematic bug fixing workflow
- `/deploy-check` - Pre-deployment checklist
- `/pre-commit` - Pre-commit quality checks

## Usage

Type `/` followed by command name to invoke.
Example: `/review-code`
```

### Step 9: Share Commands with Team

For team projects, version control your commands.

**Add to Git**:
```bash
# Add commands to version control
git add .claude/commands/

# Commit
git commit -m "feat: add custom Claude Code commands

Add standardized commands for:
- Code review workflow
- Test generation
- Bug fix process
- Deployment checks"

# Push
git push origin main
```

**Team Benefits**:
- Everyone uses same workflows
- New team members learn conventions
- Continuous improvement of processes
- Shared tribal knowledge

### Step 10: Maintain and Improve Commands

Keep commands up-to-date and effective.

**Maintenance Checklist**:
- [ ] Review commands quarterly
- [ ] Update based on team feedback
- [ ] Add new commands for new workflows
- [ ] Archive unused commands
- [ ] Keep instructions clear and current

**Feedback Loop**:
1. Use commands in daily work
2. Note what works and what doesn't
3. Gather team feedback
4. Iterate and improve
5. Share improvements

## Command Patterns

### Pattern 1: Checklist Command

**Use Case**: Systematic review or validation process

**Structure**:
```markdown
# [Task Name] Checklist

Complete all items before [action].

## Category 1
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## Category 2
- [ ] Item 1
- [ ] Item 2

## Actions

Provide analysis showing:
- Items completed
- Items needing attention
- Overall assessment
```

**Example Use Cases**:
- Code review checklist
- Deployment readiness check
- Security audit checklist
- Performance review checklist

### Pattern 2: Workflow Command

**Use Case**: Multi-phase process with dependencies

**Structure**:
```markdown
# [Workflow Name]

Follow this workflow step-by-step.

## Phase 1: [Name]
1. Do this first
2. Then do this
3. Verify result

## Phase 2: [Name]
**Prerequisite**: Complete Phase 1

1. Next step
2. Another step
3. Verify result

## Phase 3: [Name]
**Prerequisite**: Complete Phase 2

1. Final steps
2. Validation
3. Completion

## Success Criteria
- [ ] All phases completed
- [ ] Quality checks passed
- [ ] Documentation updated
```

**Example Use Cases**:
- Bug fix workflow
- Feature implementation process
- Refactoring procedure
- Database migration workflow

### Pattern 3: Generation Command

**Use Case**: Create boilerplate code, tests, or documentation

**Structure**:
```markdown
# Generate [Artifact]

Generate [type of artifact] following project conventions.

## Inputs Required
- Parameter 1: Description
- Parameter 2: Description

## Generation Rules
1. Follow [standard/convention]
2. Include [required elements]
3. Format as [style]

## Output Format
Provide:

1. Complete [artifact] ready to use
2. File location recommendation
3. Usage instructions
4. Integration steps

## Quality Standards
- Meets [standard]
- Includes [requirement]
- Follows [convention]
```

**Example Use Cases**:
- Generate test cases
- Create API documentation
- Generate database models
- Create boilerplate classes

### Pattern 4: Analysis Command

**Use Case**: Examine code and provide insights

**Structure**:
```markdown
# Analyze [Aspect]

Perform analysis of [aspect] in the codebase.

## Analysis Dimensions

### 1. [Dimension 1]
Look for:

- Pattern 1
- Pattern 2
- Red flags

### 2. [Dimension 2]
Evaluate:

- Metric 1
- Metric 2
- Best practices

### 3. [Dimension 3]
Assess:

- Quality indicator 1
- Quality indicator 2

## Report Format

Provide:
1. **Summary**: Overall assessment (1-2 sentences)
2. **Findings**: Organized by severity
   - Critical issues
   - Important improvements
   - Nice-to-haves
3. **Metrics**: Quantitative measurements
4. **Recommendations**: Prioritized action items
5. **Next Steps**: Concrete tasks
```

**Example Use Cases**:
- Security analysis
- Performance analysis
- Code quality assessment
- Dependency audit

### Pattern 5: Interactive Command

**Use Case**: Guided interview or configuration process

**Structure**:
```markdown
# [Interactive Process]

Guide user through [process] with questions and responses.

## Step 1: Initial Questions

Ask:
- Question 1?
- Question 2?
- Question 3?

Wait for responses before proceeding.

## Step 2: Based on Responses

If [condition 1]:
  Do [action A]
  Ask [follow-up questions]

If [condition 2]:
  Do [action B]
  Ask [different follow-up]

## Step 3: Generate Solution

Based on all responses:
1. Create [deliverable]
2. Explain [rationale]
3. Provide [next steps]

## Completion

Confirm:
- All questions answered
- Solution meets requirements
- User is satisfied
```

**Example Use Cases**:
- Project initialization wizard
- Configuration generator
- Architecture decision guide
- Technology selection assistant

## Real-World Command Examples

### Example 1: Pre-Commit Quality Check

**File**: `.claude/commands/pre-commit.md`

```markdown
# Pre-Commit Quality Check

Perform comprehensive quality checks before committing code.

## 1. Code Formatting

Check that code follows style guidelines:
- Run formatters (Black for Python, Prettier for JS, etc.)
- Verify line length compliance (88 chars)
- Check import organization
- Validate indentation consistency

## 2. Linting

Run static analysis:
- Check for syntax errors
- Validate type hints
- Check for common anti-patterns
- Verify naming conventions

## 3. Testing

Ensure tests pass:
- Run all unit tests
- Verify test coverage > 80%
- Check that new code has tests
- Validate test naming conventions

## 4. Documentation

Check documentation:
- All new functions have docstrings
- Complex logic is commented
- README updated if needed
- CHANGELOG updated

## 5. Security

Security validation:
- No hardcoded secrets or API keys
- No obvious vulnerabilities
- Dependencies are up-to-date
- Input validation present

## 6. Git Hygiene

Version control checks:
- No debug code or console.logs
- No commented-out code
- .gitignore is complete
- Commit message is clear

## Output

Provide:
1. **Status**: PASS or FAIL for each category
2. **Issues**: List of problems found
3. **Fixes**: Automated fixes applied
4. **Manual**: Issues requiring manual intervention
5. **Ready**: Overall ready-to-commit assessment

If all checks pass: "Ready to commit ✅"
If issues found: "Fix these issues before committing ⚠️"
```

**Usage**: `/pre-commit` before every `git commit`

### Example 2: API Endpoint Generator

**File**: `.claude/commands/create-api-endpoint.md`

```markdown
# Create API Endpoint

Generate a complete REST API endpoint following project conventions.

## Required Information

Please provide:
1. **Endpoint URL**: e.g., `/api/users/:id`
2. **HTTP Method**: GET, POST, PUT, PATCH, DELETE
3. **Purpose**: What does this endpoint do?
4. **Request Body**: Schema (if POST/PUT/PATCH)
5. **Response Body**: Schema
6. **Authentication**: Required? Type?

## Generation Process

### 1. Route Definition
Create route in appropriate router file:
```python
@router.post("/api/users")
@authenticate
async def create_user(user_data: UserCreate):
    """Create a new user."""
    pass
```

### 2. Request Validation
Define Pydantic model for request:
```python
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
```

### 3. Controller/Handler
Implement business logic:

- Validate input
- Call service layer
- Handle errors
- Return response

### 4. Service Layer
Business logic implementation:

- Database operations
- Validation logic
- External API calls
- Data transformation

### 5. Tests
Generate test cases:

- Happy path test
- Invalid input tests
- Authentication tests
- Edge case tests
- Integration tests

### 6. Documentation
Generate:

- OpenAPI/Swagger documentation
- Request/response examples
- Error code documentation
- Usage instructions

## Output

Provide complete, production-ready code:
1. Route definition file
2. Validation models
3. Controller implementation
4. Service layer code
5. Comprehensive tests
6. API documentation
7. Integration instructions

## Standards

Ensure code follows:
- Project architecture patterns
- RESTful API conventions
- Security best practices
- Error handling standards
- Testing requirements
```

**Usage**: `/create-api-endpoint` when adding new API routes

### Example 3: Database Migration Guide

**File**: `.claude/commands/create-migration.md`

```markdown
# Create Database Migration

Guide through creating a safe database migration.

## Phase 1: Plan Migration

### 1. Define Changes
What needs to change?

- [ ] Add table
- [ ] Modify table
- [ ] Remove table
- [ ] Add column
- [ ] Modify column
- [ ] Remove column
- [ ] Add index
- [ ] Add constraint

### 2. Assess Impact
- Data volume affected
- Downtime required
- Rollback strategy
- Dependencies on other tables

### 3. Migration Strategy
Choose approach:

- **Non-breaking**: Add new, deprecate old
- **Breaking**: Requires downtime
- **Multi-phase**: Gradual transition

## Phase 2: Write Migration

### 1. Up Migration
Write migration code:
```python
def upgrade():
    """Apply migration."""
    op.add_column('users',
        sa.Column('email_verified', sa.Boolean(),
        nullable=False, server_default='false'))
    op.create_index('ix_users_email_verified',
        'users', ['email_verified'])
```

### 2. Down Migration
Write rollback:
```python
def downgrade():
    """Rollback migration."""
    op.drop_index('ix_users_email_verified', 'users')
    op.drop_column('users', 'email_verified')
```

### 3. Data Migration
If needed, add data transformation:
```python
def upgrade():
    # Schema change
    op.add_column('users', sa.Column('full_name', sa.String(200)))

    # Data migration
    connection = op.get_bind()
    connection.execute("""
        UPDATE users
        SET full_name = CONCAT(first_name, ' ', last_name)
    """)
```

## Phase 3: Test Migration

### 1. Test Database
```bash
# Apply migration to test database
alembic upgrade head

# Verify schema
psql test_db -c "\d users"

# Verify data
psql test_db -c "SELECT * FROM users LIMIT 5"

# Test rollback
alembic downgrade -1

# Verify rollback
psql test_db -c "\d users"
```

### 2. Performance Test
- Measure migration time on copy of production data
- Check for locks
- Monitor resource usage
- Verify indexes are created

### 3. Application Test
- Deploy code with migration
- Run integration tests
- Verify functionality
- Check for errors

## Phase 4: Documentation

Document:
- Migration purpose
- Breaking changes
- Downtime estimate
- Rollback procedure
- Monitoring points

## Phase 5: Deployment Checklist

Before deploying to production:
- [ ] Migration tested on staging
- [ ] Rollback tested
- [ ] Team notified of deployment
- [ ] Backup created
- [ ] Downtime scheduled (if needed)
- [ ] Monitoring ready
- [ ] Rollback plan documented

## Execution

Provide:
1. Complete migration code (up and down)
2. Test commands
3. Deployment instructions
4. Rollback procedure
5. Monitoring recommendations

Remember: Migrations are permanent - test thoroughly!
```

**Usage**: `/create-migration` when changing database schema

### Example 4: Refactoring Workflow

**File**: `.claude/commands/refactor.md`

```markdown
# Code Refactoring Workflow

Systematic approach to refactoring code safely.

## Step 1: Identify Refactoring Target

What needs refactoring?
- Large function/method (> 50 lines)
- Duplicated code (DRY violation)
- Complex conditional logic (high cyclomatic complexity)
- Poor naming
- Tight coupling
- Low cohesion

## Step 2: Ensure Test Coverage

**CRITICAL**: Before refactoring, ensure comprehensive tests exist.

```bash
# Check current coverage
pytest --cov=src --cov-report=html
```

Requirements:
- [ ] Target code has > 80% test coverage
- [ ] Tests are passing
- [ ] Tests are comprehensive (not just line coverage)

If insufficient tests:
1. STOP
2. Write tests first
3. Ensure all tests pass
4. THEN proceed with refactoring

## Step 3: Plan Refactoring

Choose refactoring technique:

### Extract Method
Break large function into smaller functions:
```python
# Before
def process_order(order):
    # 50 lines of code

# After
def process_order(order):
    validate_order(order)
    calculate_totals(order)
    apply_discounts(order)
    charge_payment(order)
    send_confirmation(order)
```

### Extract Class
Separate concerns into classes:
```python
# Before
class UserService:
    def create_user(self): ...
    def send_email(self): ...
    def format_address(self): ...

# After
class UserService:
    def __init__(self):
        self.email_service = EmailService()
        self.address_formatter = AddressFormatter()
```

### Simplify Conditional
Replace complex conditionals:
```python
# Before
if (user.age > 18 and user.country == "US"
    and user.verified and not user.banned):
    allow_access()

# After
if user.can_access():
    allow_access()
```

### Remove Duplication
Extract common code:
```python
# Before: Duplication in multiple functions
def format_user_name(user):
    return f"{user.first_name} {user.last_name}".strip()

def format_admin_name(admin):
    return f"{admin.first_name} {admin.last_name}".strip()

# After: Shared utility
def format_full_name(person):
    return f"{person.first_name} {person.last_name}".strip()
```

## Step 4: Refactor Incrementally

Apply refactoring in small steps:

1. **Small Change**: Make one refactoring
2. **Run Tests**: Ensure all tests still pass
3. **Commit**: Commit the working refactoring
4. **Repeat**: Next small refactoring

**NEVER**:
- Refactor multiple things at once
- Skip running tests
- Make large changes without committing

## Step 5: Verify Improvements

Check that refactoring improved code:

### Code Metrics
- Lines of code reduced
- Cyclomatic complexity decreased
- Duplication eliminated
- Function length reduced

### Code Quality
- [ ] Easier to understand
- [ ] Better named
- [ ] More modular
- [ ] More testable
- [ ] Follows SOLID principles

### Test Status
- [ ] All tests still pass
- [ ] No new bugs introduced
- [ ] Test coverage maintained or improved

## Step 6: Document Changes

Update documentation:
- Add comments for complex logic
- Update function docstrings
- Update architectural docs
- Note in DEVLOG.md

Example DEVLOG entry:
```markdown
### Refactoring: UserService

**Issue**: UserService class had grown to 500 lines with multiple responsibilities

**Changes**:
- Extracted EmailService (email operations)
- Extracted ValidationService (validation logic)
- Extracted AddressFormatter (formatting utilities)

**Result**:
- UserService reduced to 150 lines
- Improved testability (can mock services)
- Better separation of concerns
- All tests still pass

**Tests**: 45 tests, 95% coverage maintained
```

## Step 7: Code Review

Before considering refactoring complete:
- [ ] Run `/pre-commit` checks
- [ ] Request peer review
- [ ] Verify performance not degraded
- [ ] Check for introduced bugs

## Common Refactoring Patterns

### Long Method
- Extract smaller methods
- Each method does one thing

### Long Parameter List
- Group parameters into object
- Use builder pattern

### Large Class
- Extract classes by responsibility
- Follow Single Responsibility Principle

### Feature Envy
- Move method to appropriate class
- Keep data and behavior together

### Primitive Obsession
- Create value objects
- Encapsulate behavior with data

## Success Criteria

- [ ] Code is more readable
- [ ] Functions are smaller and focused
- [ ] Duplication is eliminated
- [ ] Names are clear and descriptive
- [ ] All tests pass
- [ ] No performance regression
- [ ] Team agrees improvement is valuable

Remember: Refactoring should make code better, not just different!
```

**Usage**: `/refactor` when improving existing code structure

### Example 5: Performance Optimization

**File**: `.claude/commands/optimize-performance.md`

```markdown
# Performance Optimization Workflow

Systematic approach to optimizing code performance.

## Step 1: Measure First

**Rule**: Never optimize without measuring!

### 1.1 Profile the Code
```python
# Python example
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = slow_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 1.2 Identify Bottlenecks
Look for:

- Functions taking most time
- Database queries (N+1 problems)
- I/O operations
- Unnecessary computations
- Memory allocations

### 1.3 Establish Baseline
Record current performance:

- Execution time
- Memory usage
- Database query count
- API call count
- CPU usage

## Step 2: Set Performance Goals

Define targets:
- Target response time (e.g., < 200ms)
- Maximum memory usage (e.g., < 100MB)
- Throughput goal (e.g., 1000 req/sec)
- Database query limit (e.g., < 5 queries)

## Step 3: Optimize Systematically

Apply optimizations in order of impact:

### 3.1 Algorithm Optimization
Change algorithm complexity:
```python
# Before: O(n²)
def find_duplicates(items):
    duplicates = []
    for i, item in enumerate(items):
        for j, other in enumerate(items[i+1:]):
            if item == other:
                duplicates.append(item)
    return duplicates

# After: O(n)
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

### 3.2 Database Optimization
```python
# Before: N+1 query problem
users = User.query.all()
for user in users:
    print(user.profile.bio)  # Separate query for each user!

# After: Eager loading
users = User.query.options(joinedload(User.profile)).all()
for user in users:
    print(user.profile.bio)  # No additional queries
```

### 3.3 Caching
```python
from functools import lru_cache

# Cache expensive computations
@lru_cache(maxsize=1000)
def expensive_calculation(n):
    # Complex calculation
    return result
```

### 3.4 Lazy Evaluation
```python
# Before: Eager evaluation (processes everything)
results = [process_item(item) for item in huge_list]
return results[0]  # Only needed first item!

# After: Generator (lazy evaluation)
results = (process_item(item) for item in huge_list)
return next(results)  # Only processes first item
```

### 3.5 Batch Operations
```python
# Before: Individual operations
for item in items:
    database.save(item)  # Separate database call each time

# After: Batch operation
database.bulk_save(items)  # Single database call
```

### 3.6 Asynchronous Operations
```python
# Before: Sequential API calls
result1 = api.fetch_user(id1)
result2 = api.fetch_user(id2)
result3 = api.fetch_user(id3)

# After: Concurrent API calls
import asyncio

async def fetch_all():
    results = await asyncio.gather(
        api.fetch_user(id1),
        api.fetch_user(id2),
        api.fetch_user(id3)
    )
    return results
```

## Step 4: Measure Impact

After each optimization:

### 4.1 Re-run Profiler
```python
# Measure optimized version
profiler = cProfile.Profile()
profiler.enable()
result = optimized_function()
profiler.disable()
stats = pstats.Stats(profiler)
stats.print_stats()
```

### 4.2 Compare Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Time | 5.2s | 0.8s | 85% faster |
| Memory | 500MB | 50MB | 90% less |
| DB Queries | 1001 | 1 | 99.9% reduction |

### 4.3 Verify Correctness
- [ ] All tests still pass
- [ ] Output is identical
- [ ] No bugs introduced
- [ ] Edge cases still handled

## Step 5: Document Optimization

Record in DEVLOG.md:
```markdown
### Performance Optimization: User List API

**Problem**: User list endpoint taking 5+ seconds with 1000 users

**Profiling Results**:
- 95% of time in database queries
- N+1 query problem (1001 total queries)

**Optimizations Applied**:
1. Added eager loading for user profiles
2. Implemented query result caching (5-minute TTL)
3. Added pagination (max 100 users per page)

**Results**:
- Response time: 5.2s → 0.2s (96% faster)
- Database queries: 1001 → 2 (99.8% reduction)
- Memory usage: 500MB → 50MB (90% reduction)

**Trade-offs**:
- Added Redis dependency for caching
- 5-minute cache may show stale data
- Pagination requires client-side changes
```

## Step 6: Performance Testing

Create performance test suite:

```python
import time
import pytest

def test_user_list_performance():
    """Test that user list endpoint responds in < 200ms."""
    start = time.time()
    response = client.get("/api/users")
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 0.2, f"Too slow: {elapsed:.3f}s"

def test_user_list_database_queries():
    """Test that user list makes <= 5 database queries."""
    with query_counter() as counter:
        response = client.get("/api/users")

    assert counter.count <= 5, f"Too many queries: {counter.count}"
```

## Common Performance Patterns

### Pattern: Database Query Optimization
- Use select_related() / prefetch_related()
- Add database indexes
- Avoid N+1 queries
- Use connection pooling
- Implement query result caching

### Pattern: Computational Optimization
- Cache expensive calculations
- Use appropriate data structures
- Avoid unnecessary loops
- Leverage built-in functions
- Use generators for large datasets

### Pattern: Memory Optimization
- Process data in chunks
- Use generators instead of lists
- Release resources explicitly
- Avoid memory leaks
- Monitor memory growth

### Pattern: I/O Optimization
- Batch operations
- Use asynchronous I/O
- Implement caching
- Compress data transfer
- Minimize network calls

## Warning Signs

Stop and reconsider if:
- Code becomes significantly more complex
- Tests start failing
- Memory usage increases
- "Optimization" makes code slower
- Team can't understand the changes

## Success Criteria

- [ ] Performance goals achieved
- [ ] All tests pass
- [ ] Code remains readable
- [ ] No new bugs introduced
- [ ] Trade-offs documented
- [ ] Performance tests added
- [ ] Team understands changes

Remember: Premature optimization is the root of all evil. Measure, optimize, measure again!
```

**Usage**: `/optimize-performance` when addressing performance issues

### Example 6: Security Audit

**File**: `.claude/commands/security-audit.md`

```markdown
# Security Audit Checklist

Comprehensive security review of code changes.

## 1. Authentication & Authorization

### Authentication
- [ ] User authentication is required for protected endpoints
- [ ] Password hashing uses strong algorithm (bcrypt, Argon2)
- [ ] Password complexity requirements enforced
- [ ] Account lockout after failed attempts
- [ ] Session management is secure
- [ ] JWT tokens are signed and validated

### Authorization
- [ ] Authorization checks are present
- [ ] Users can only access their own resources
- [ ] Role-based access control (RBAC) implemented
- [ ] Privilege escalation prevented
- [ ] API endpoints validate permissions

## 2. Input Validation

### User Input
- [ ] All user input is validated
- [ ] Input length limits enforced
- [ ] Type validation present
- [ ] Format validation (email, phone, etc.)
- [ ] Reject unexpected input

### Injection Prevention
- [ ] SQL injection prevented (parameterized queries)
- [ ] NoSQL injection prevented
- [ ] Command injection prevented
- [ ] LDAP injection prevented
- [ ] XPath injection prevented

### Cross-Site Scripting (XSS)
- [ ] Output encoding implemented
- [ ] HTML entities escaped
- [ ] Content Security Policy (CSP) configured
- [ ] User-generated content sanitized
- [ ] No eval() or dangerous functions

## 3. Sensitive Data

### Storage
- [ ] Passwords are hashed, not encrypted
- [ ] Sensitive data encrypted at rest
- [ ] Encryption keys stored securely
- [ ] PII (Personally Identifiable Information) protected
- [ ] Credit card data not stored (use tokenization)

### Transmission
- [ ] HTTPS enforced for all connections
- [ ] TLS 1.2+ required
- [ ] Sensitive data not in URLs
- [ ] Sensitive data not in logs
- [ ] Secure cookies (HttpOnly, Secure flags)

### Secrets Management
- [ ] No hardcoded API keys
- [ ] No hardcoded passwords
- [ ] No secrets in code
- [ ] Environment variables used
- [ ] Secrets manager used (AWS Secrets, Vault, etc.)

## 4. Error Handling

- [ ] Error messages don't expose sensitive info
- [ ] Stack traces not shown to users
- [ ] Errors logged securely
- [ ] Database errors don't leak schema
- [ ] Generic error messages for auth failures

## 5. Dependencies

### Third-Party Libraries
- [ ] Dependencies are up-to-date
- [ ] No known vulnerabilities (run npm audit, pip-audit)
- [ ] Unused dependencies removed
- [ ] Licenses reviewed
- [ ] Supply chain security considered

### Dependency Management
```bash
# Python
pip-audit

# JavaScript
npm audit
npm audit fix

# Java
mvn dependency-check:check
```

## 6. API Security

- [ ] Rate limiting implemented
- [ ] CORS configured properly
- [ ] API authentication required
- [ ] Request size limits enforced
- [ ] API versioning implemented
- [ ] Deprecated endpoints removed

## 7. File Operations

- [ ] File upload validation (type, size)
- [ ] File path traversal prevented
- [ ] Uploaded files scanned for malware
- [ ] File permissions are restrictive
- [ ] Temporary files cleaned up

## 8. Session Management

- [ ] Session IDs are random and unpredictable
- [ ] Session timeout implemented
- [ ] Sessions invalidated on logout
- [ ] Session fixation prevented
- [ ] CSRF tokens implemented

## 9. Logging & Monitoring

- [ ] Security events logged
- [ ] Authentication attempts logged
- [ ] Sensitive data not logged
- [ ] Logs stored securely
- [ ] Log injection prevented
- [ ] Monitoring alerts configured

## 10. Database Security

- [ ] Parameterized queries used (no string concatenation)
- [ ] Least privilege database user
- [ ] Database credentials secured
- [ ] Database backups encrypted
- [ ] Connection strings not in code

## Vulnerability Scan

Run automated security scanners:

```bash
# Python
bandit -r src/
safety check

# JavaScript
npm audit
snyk test

# General
# Run OWASP ZAP or Burp Suite for web applications
```

## Threat Modeling

Consider common attack vectors:

### OWASP Top 10
1. Broken Access Control
2. Cryptographic Failures
3. Injection
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Authentication Failures
8. Software & Data Integrity Failures
9. Logging & Monitoring Failures
10. Server-Side Request Forgery (SSRF)

## Report Format

Provide security audit report:

### Summary
- Overall security posture
- Critical issues found
- High-priority issues
- Medium-priority issues
- Low-priority issues

### Findings

For each issue:
- **Severity**: Critical/High/Medium/Low
- **Category**: Auth, Injection, XSS, etc.
- **Location**: File and line number
- **Description**: What is vulnerable
- **Impact**: What could happen
- **Remediation**: How to fix
- **References**: OWASP, CWE links

### Recommendations

Prioritized list of security improvements:
1. Critical fixes (fix immediately)
2. High-priority improvements
3. Security enhancements
4. Best practices to adopt

## Success Criteria

- [ ] No critical vulnerabilities
- [ ] High-priority issues addressed
- [ ] Security best practices followed
- [ ] Automated scanning integrated
- [ ] Security documentation updated

Remember: Security is not a feature, it's a requirement!
```

**Usage**: `/security-audit` before releases or regularly

### Example 7: Deployment Checklist

**File**: `.claude/commands/deploy-check.md`

```markdown
# Deployment Readiness Checklist

Verify application is ready for production deployment.

## 1. Code Quality

### Testing
- [ ] All tests pass
- [ ] Test coverage > 80%
- [ ] Integration tests pass
- [ ] End-to-end tests pass
- [ ] No flaky tests
- [ ] Performance tests pass

### Code Review
- [ ] All changes reviewed
- [ ] Review comments addressed
- [ ] No "TODO" or "FIXME" in critical paths
- [ ] Code follows style guidelines
- [ ] No debug code or console.logs

### Static Analysis
```bash
# Run linting
npm run lint        # JavaScript
flake8 src/         # Python
mvn checkstyle:check  # Java

# Type checking
tsc --noEmit        # TypeScript
mypy src/           # Python
```

## 2. Documentation

- [ ] README updated
- [ ] CHANGELOG updated with version
- [ ] API documentation current
- [ ] Configuration documented
- [ ] Environment variables documented
- [ ] Deployment guide updated

## 3. Database

### Migrations
- [ ] Migrations tested on staging
- [ ] Migrations are reversible
- [ ] Data migration tested
- [ ] Backup strategy ready
- [ ] Downtime estimated

### Performance
- [ ] Database indexes optimized
- [ ] Slow queries identified and fixed
- [ ] Connection pooling configured
- [ ] Query performance tested

## 4. Configuration

### Environment
- [ ] Environment variables configured
- [ ] Secrets stored in secret manager
- [ ] Configuration for each environment (dev, staging, prod)
- [ ] Feature flags configured
- [ ] No hardcoded values

### Infrastructure
- [ ] Resource limits configured
- [ ] Auto-scaling configured
- [ ] Health checks configured
- [ ] Monitoring alerts configured
- [ ] Backup policies in place

## 5. Security

- [ ] Security audit completed (`/security-audit`)
- [ ] Vulnerabilities addressed
- [ ] Dependencies updated
- [ ] SSL/TLS certificates valid
- [ ] Security headers configured
- [ ] CORS configured correctly
- [ ] Rate limiting in place

## 6. Performance

- [ ] Performance testing completed
- [ ] Load testing passed
- [ ] Response times acceptable
- [ ] Memory usage optimized
- [ ] Database queries optimized
- [ ] Caching implemented
- [ ] CDN configured (if needed)

## 7. Monitoring

### Logging
- [ ] Application logging configured
- [ ] Log aggregation set up
- [ ] Log retention policy set
- [ ] Error tracking configured (Sentry, Rollbar, etc.)

### Metrics
- [ ] Application metrics configured
- [ ] Infrastructure metrics monitored
- [ ] Custom business metrics tracked
- [ ] Dashboards created

### Alerting
- [ ] Critical alerts configured
- [ ] On-call rotation set up
- [ ] Alert thresholds tuned
- [ ] Runbooks created

## 8. Disaster Recovery

- [ ] Backup strategy implemented
- [ ] Backup restoration tested
- [ ] Rollback plan documented
- [ ] Incident response plan ready
- [ ] Team contact information current

## 9. Dependencies

### Third-Party Services
- [ ] API keys configured
- [ ] Service quotas checked
- [ ] Rate limits understood
- [ ] Fallback strategies ready
- [ ] Service SLAs reviewed

### Infrastructure
- [ ] DNS configured
- [ ] Load balancer configured
- [ ] CDN configured
- [ ] Email service configured
- [ ] Storage configured

## 10. Compliance

- [ ] GDPR compliance verified (if applicable)
- [ ] Data retention policies implemented
- [ ] User consent mechanisms in place
- [ ] Privacy policy updated
- [ ] Terms of service updated

## Pre-Deployment Steps

### 1. Final Testing
```bash
# Run full test suite
npm test
pytest

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e
```

### 2. Build Application
```bash
# Production build
npm run build
python setup.py bdist_wheel

# Verify build
ls -lh dist/
```

### 3. Deploy to Staging
```bash
# Deploy to staging
./deploy.sh staging

# Smoke test staging
curl https://staging.example.com/health

# Run tests against staging
ENVIRONMENT=staging npm run test:integration
```

### 4. Staging Validation
- [ ] Staging deployment successful
- [ ] Smoke tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Stakeholder approval obtained

## Deployment

### Deployment Process
```bash
# 1. Tag release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# 2. Deploy to production
./deploy.sh production

# 3. Monitor deployment
./scripts/monitor-deployment.sh
```

### Rollout Strategy
- [ ] Deployment strategy chosen (blue/green, canary, rolling)
- [ ] Rollout percentage defined
- [ ] Success criteria defined
- [ ] Rollback triggers defined

## Post-Deployment

### Immediate Checks (within 15 minutes)
- [ ] Deployment successful
- [ ] Health checks passing
- [ ] Error rates normal
- [ ] Response times acceptable
- [ ] No critical alerts

### Short-term Monitoring (24 hours)
- [ ] Application stability
- [ ] Performance metrics
- [ ] Error rates
- [ ] User feedback
- [ ] Business metrics

### Documentation
- [ ] Deployment notes recorded
- [ ] Issues encountered documented
- [ ] Lessons learned captured
- [ ] Team notified of deployment

## Rollback Plan

If deployment fails:

```bash
# 1. Initiate rollback
./deploy.sh production --rollback

# 2. Verify rollback
curl https://api.example.com/health

# 3. Investigate issue
./scripts/debug-deployment.sh

# 4. Notify team
# Send incident notification
```

### Rollback Criteria
Rollback if:

- Error rate > 5%
- Response time > 2x normal
- Health checks failing
- Critical functionality broken
- Database issues

## Communication

### Before Deployment
- [ ] Team notified of deployment window
- [ ] Stakeholders informed
- [ ] Maintenance window scheduled (if needed)
- [ ] Support team briefed

### During Deployment
- [ ] Status updates posted
- [ ] Progress communicated
- [ ] Issues escalated quickly

### After Deployment
- [ ] Success announced
- [ ] Release notes shared
- [ ] Team thanked

## Final Checklist

- [ ] All pre-deployment checks completed
- [ ] Staging validated successfully
- [ ] Team is ready
- [ ] Rollback plan in place
- [ ] Monitoring active
- [ ] Communication plan executed

**Status**: READY / NOT READY

If READY: Proceed with deployment ✅
If NOT READY: Address blockers before deploying ⚠️
```

**Usage**: `/deploy-check` before every production deployment

### Example 8: Code Documentation Generator

**File**: `.claude/commands/document-code.md`

```markdown
# Generate Code Documentation

Automatically generate comprehensive documentation for code.

## Documentation Types

Which type of documentation?
1. **Function/Method Docstrings**
2. **Class Documentation**
3. **Module Documentation**
4. **API Documentation**
5. **Architecture Documentation**

## 1. Function/Method Docstrings

Generate docstrings following project conventions:

### Python (Google Style)
```python
def calculate_order_total(items: List[Item], tax_rate: float = 0.08) -> Decimal:
    """
    Calculate the total cost of an order including tax.

    Calculates the subtotal of all items, applies the tax rate,
    and returns the final total rounded to 2 decimal places.

    Args:
        items: List of Item objects in the order
        tax_rate: Tax rate as decimal (default: 0.08 for 8%)

    Returns:
        Order total as Decimal rounded to 2 decimal places

    Raises:
        ValueError: If tax_rate is negative or > 1
        ValueError: If items list is empty

    Examples:
        >>> items = [Item(price=10.00), Item(price=20.00)]
        >>> calculate_order_total(items, tax_rate=0.08)
        Decimal('32.40')

    Note:
        Tax is calculated on subtotal, not per-item.
        All prices should be in the same currency.

    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
```

### JavaScript (JSDoc)
```javascript
/**

 * Calculate the total cost of an order including tax.
 *

 * Calculates the subtotal of all items, applies the tax rate,
 * and returns the final total rounded to 2 decimal places.
 *

 * @param {Array<Item>} items - List of items in the order
 * @param {number} [taxRate=0.08] - Tax rate as decimal (default 8%)
 * @returns {number} Order total rounded to 2 decimal places
 * @throws {Error} If tax rate is negative or > 1
 * @throws {Error} If items array is empty
 *

 * @example
 * const items = [{ price: 10.00 }, { price: 20.00 }];
 * calculateOrderTotal(items, 0.08);
 * // Returns: 32.40
 *

 * @author Benjamin Dourthe <benjamin@adonamed.com>
 */
function calculateOrderTotal(items, taxRate = 0.08) {
  // Implementation
}
```

### Java (Javadoc)
```java
/**

 * Calculate the total cost of an order including tax.
 *

 * <p>Calculates the subtotal of all items, applies the tax rate,
 * and returns the final total rounded to 2 decimal places.</p>
 *

 * @param items List of items in the order
 * @param taxRate Tax rate as decimal (e.g., 0.08 for 8%)
 * @return Order total as BigDecimal rounded to 2 decimal places
 * @throws IllegalArgumentException if tax rate is negative or > 1
 * @throws IllegalArgumentException if items list is empty
 *

 * @see Item
 * @since 1.0
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */
public BigDecimal calculateOrderTotal(List<Item> items, double taxRate) {
  // Implementation
}
```

## 2. Class Documentation

Generate comprehensive class documentation:

```python
class OrderProcessor:
    """
    Process customer orders through the complete order lifecycle.

    The OrderProcessor handles order validation, inventory checking,
    payment processing, and order fulfillment. It coordinates between
    multiple services to ensure orders are processed correctly.

    Attributes:
        inventory_service (InventoryService): Service for inventory operations
        payment_service (PaymentService): Service for payment processing
        notification_service (NotificationService): Service for notifications
        logger (Logger): Logger instance for order processing events

    Example:
        >>> processor = OrderProcessor(
        ...     inventory_service=InventoryService(),
        ...     payment_service=PaymentService(),
        ...     notification_service=NotificationService()
        ... )
        >>> order = Order(items=[Item(id=1, quantity=2)])
        >>> result = processor.process_order(order)
        >>> print(result.status)
        'completed'

    Note:
        This class is not thread-safe. Use separate instances for
        concurrent order processing.

    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)

    Version:
        1.2.0

    Since:
        0.1.0
    """
```

## 3. Module Documentation

Generate module-level documentation:

```python
"""
Order processing module for e-commerce platform.

This module provides classes and functions for processing customer orders,
including validation, payment processing, inventory management, and
order fulfillment.

Classes:
    OrderProcessor: Main class for order processing
    OrderValidator: Validates order data
    PaymentHandler: Handles payment processing

Functions:
    calculate_order_total: Calculate order total with tax
    validate_shipping_address: Validate shipping address format
    apply_discount_code: Apply discount code to order

Exceptions:
    OrderValidationError: Raised when order validation fails
    PaymentError: Raised when payment processing fails
    InsufficientInventoryError: Raised when inventory is insufficient

Usage:
    from order_processing import OrderProcessor, Order

    processor = OrderProcessor()
    order = Order(items=[...])
    result = processor.process_order(order)

Configuration:
    Set these environment variables:

    - PAYMENT_API_KEY: Payment gateway API key
    - INVENTORY_API_URL: Inventory service URL
    - ORDER_TIMEOUT: Order processing timeout in seconds

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)

Version:
    1.2.0

Since:
    0.1.0

License:
    MIT
"""
```

## 4. API Documentation

Generate API endpoint documentation:

```markdown
## POST /api/orders

Create a new order.

### Description

Creates a new order for the authenticated user. Validates inventory
availability, processes payment, and initiates order fulfillment.

### Authentication

Requires valid JWT token in Authorization header:
```
Authorization: Bearer <token>
```

### Request

#### Headers
- `Content-Type`: `application/json`
- `Authorization`: `Bearer <JWT token>`

#### Body
```json
{
  "items": [
    {
      "product_id": "prod_123",
      "quantity": 2,
      "price": 29.99
    }
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94105",
    "country": "US"
  },
  "payment_method": {
    "type": "credit_card",
    "token": "tok_visa_4242"
  },
  "discount_code": "SAVE10"
}
```

### Response

#### Success (201 Created)
```json
{
  "order_id": "ord_abc123",
  "status": "processing",
  "subtotal": 59.98,
  "tax": 4.80,
  "discount": 6.00,
  "total": 58.78,
  "estimated_delivery": "2025-10-25",
  "created_at": "2025-10-20T10:30:00Z"
}
```

#### Error (400 Bad Request)
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid shipping address",
    "details": {
      "field": "shipping_address.zip",
      "issue": "Invalid ZIP code format"
    }
  }
}
```

#### Error (402 Payment Required)
```json
{
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment processing failed",
    "details": {
      "reason": "Insufficient funds"
    }
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_INPUT` | Request validation failed |
| `INSUFFICIENT_INVENTORY` | Not enough inventory |
| `PAYMENT_FAILED` | Payment processing failed |
| `INVALID_DISCOUNT_CODE` | Discount code not valid |

### Rate Limiting

- 100 requests per hour per user
- 429 status code when limit exceeded
- `Retry-After` header indicates wait time

### Examples

#### cURL
```bash
curl -X POST https://api.example.com/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "items": [{"product_id": "prod_123", "quantity": 2}],
    "shipping_address": {...},
    "payment_method": {...}
  }'
```

#### Python
```python
import requests

response = requests.post(
    "https://api.example.com/api/orders",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "items": [{"product_id": "prod_123", "quantity": 2}],
        "shipping_address": {...},
        "payment_method": {...}
    }
)

order = response.json()
print(f"Order created: {order['order_id']}")
```

#### JavaScript
```javascript
const response = await fetch('https://api.example.com/api/orders', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    items: [{product_id: 'prod_123', quantity: 2}],
    shipping_address: {...},
    payment_method: {...}
  })
});

const order = await response.json();
console.log(`Order created: ${order.order_id}`);
```
```

## 5. Architecture Documentation

Generate high-level architecture documentation:

```markdown
# Order Processing Architecture

## Overview

The order processing system handles the complete order lifecycle from
creation to fulfillment. It is designed for high availability,
scalability, and fault tolerance.

## Components

### API Layer
- **Technology**: Express.js (Node.js)
- **Responsibility**: Handle HTTP requests, authentication, validation
- **Scaling**: Horizontal (multiple instances behind load balancer)

### Business Logic Layer
- **Technology**: Python (FastAPI)
- **Responsibility**: Order processing, business rules, orchestration
- **Scaling**: Horizontal (stateless design)

### Data Layer
- **Database**: PostgreSQL 14
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ
- **Responsibility**: Data persistence, caching, async processing

### External Services
- **Payment Gateway**: Stripe API
- **Inventory Service**: Internal microservice
- **Notification Service**: SendGrid, Twilio

## Data Flow

```
┌─────────┐     ┌─────────┐     ┌──────────────┐
│ Client  │────▶│   API   │────▶│   Business   │
└─────────┘     └─────────┘     │   Logic      │
                                 └──────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
             ┌──────────┐       ┌──────────┐       ┌──────────┐
             │ Database │       │  Cache   │       │  Queue   │
             └──────────┘       └──────────┘       └──────────┘
```

## Error Handling

- Retries: 3 attempts with exponential backoff
- Circuit breaker: Opens after 5 consecutive failures
- Fallback: Degraded service mode when dependencies fail
- Logging: All errors logged with context

## Security

- Authentication: JWT tokens (15-minute expiry)
- Authorization: Role-based access control (RBAC)
- Rate limiting: 100 requests/hour per user
- Data encryption: TLS 1.3 in transit, AES-256 at rest

## Monitoring

- Metrics: Prometheus
- Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
- Tracing: Jaeger
- Alerting: PagerDuty

## Deployment

- Infrastructure: AWS (EC2, RDS, ElastiCache)
- Container: Docker
- Orchestration: Kubernetes
- CI/CD: GitHub Actions
- Deployment: Blue/green with canary releases
```

## Generation Process

1. **Analyze Code**: Examine the code to document
2. **Identify Components**: Functions, classes, modules, APIs
3. **Extract Information**: Parameters, returns, exceptions, examples
4. **Follow Conventions**: Use project documentation style
5. **Generate Documentation**: Complete, accurate, helpful docs
6. **Validate**: Ensure documentation is correct and clear

## Documentation Standards

### Required Elements
- [ ] Clear description of what code does
- [ ] All parameters documented
- [ ] Return values documented
- [ ] Exceptions documented
- [ ] Examples provided
- [ ] Author information
- [ ] Version/date information (if applicable)

### Quality Standards
- [ ] Accurate (matches implementation)
- [ ] Complete (covers all functionality)
- [ ] Clear (easy to understand)
- [ ] Concise (no unnecessary verbosity)
- [ ] Consistent (follows project style)
- [ ] Helpful (provides value to readers)

## Output

Provide generated documentation in appropriate format:
- Inline docstrings for functions/classes
- Markdown for API/architecture docs
- HTML/PDF for publishable documentation

Include:
1. Complete documentation text
2. Location where it should be added
3. Any additional files to create
4. Instructions for building/publishing docs (if applicable)
```

**Usage**: `/document-code` when adding or updating documentation

### Example 9: Git Commit Message Generator

**File**: `.claude/commands/commit-message.md`

```markdown
# Generate Commit Message

Generate a clear, descriptive commit message following Conventional Commits format.

## Analysis

First, analyze the staged changes:
```bash
# Show staged changes
git diff --cached
```

## Commit Message Format

```
<type>(<scope>): <short description>

<body - optional but recommended>

<footer - optional>
```

## Commit Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature added |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code formatting (no logic change) |
| `refactor` | Code refactoring |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `build` | Build system changes |

## Generation Rules

### 1. Analyze Changes
- What files changed?
- What functionality changed?
- Why was the change made?
- What problem does it solve?

### 2. Choose Type
Based on changes:

- New feature → `feat`
- Bug fix → `fix`
- Refactoring → `refactor`
- Tests → `test`
- Documentation → `docs`
- Multiple types → Split into separate commits!

### 3. Determine Scope
Scope identifies affected component:

- `auth` - Authentication/authorization
- `api` - API endpoints
- `db` - Database
- `ui` - User interface
- `config` - Configuration
- Module/feature name

### 4. Write Subject
- Max 50 characters
- Start with lowercase
- No period at end
- Imperative mood ("add" not "added")
- Clear and specific

### 5. Write Body (if needed)
- Explain WHY, not WHAT (code shows what)
- Wrap at 72 characters
- Separate paragraphs with blank lines
- Include context and reasoning

### 6. Add Footer (if applicable)
- Reference issues: `Closes #123`
- Breaking changes: `BREAKING CHANGE: ...`
- Co-authors: `Co-authored-by: Name <email>`

## Examples

### Example 1: New Feature
```
feat(auth): add JWT token refresh endpoint

Add endpoint to refresh JWT tokens without re-authentication.
Tokens expire after 15 minutes but can be refreshed for 7 days.

This improves UX by not forcing users to log in frequently
while maintaining security through short-lived access tokens.

Closes #234
```

### Example 2: Bug Fix
```
fix(api): prevent division by zero in refund calculation

When processing partial refunds with zero quantity items,
the calculation would crash. Add validation to skip zero
quantity items before performing division.

Root cause: Missing null/zero check before division operation.

Fixes #456
```

### Example 3: Refactoring
```
refactor(db): extract database queries to repository layer

Move database queries from service layer to new repository
classes. This improves testability and follows repository
pattern for better separation of concerns.

No behavior changes - all existing tests pass.
```

### Example 4: Documentation
```
docs(api): add authentication examples to API guide

Add code examples for JWT authentication in Python,
JavaScript, and Java. Include common error scenarios
and troubleshooting steps.
```

### Example 5: Multiple Changes
If changes include both feature and fix, create TWO commits:

Commit 1:
```
feat(order): add order cancellation endpoint
```

Commit 2:
```
fix(order): handle edge case in refund calculation
```

## Generation Process

Based on the staged changes:

1. **Identify main change**: What is the primary modification?
2. **Choose type**: Select appropriate commit type
3. **Determine scope**: Identify affected component
4. **Write subject**: Clear, concise description
5. **Add body**: Explain reasoning and context
6. **Add footer**: Reference issues, breaking changes

## Output

Provide:
1. **Suggested commit message**: Complete message ready to use
2. **Explanation**: Why this message is appropriate
3. **Command**: Exact git command to run

Example output:
```bash
# Suggested commit message:
git commit -m "feat(auth): implement two-factor authentication

Add support for TOTP-based two-factor authentication.
Users can enable 2FA in account settings and will be
prompted for a verification code after password entry.

Uses speakeasy library for TOTP generation and validation.
QR codes generated with qrcode library.

Closes #145"

# Alternative if you want to edit:
git commit
# (Opens editor with suggested message)
```

## Quality Checks

Before finalizing commit message:
- [ ] Type is appropriate for changes
- [ ] Scope accurately identifies component
- [ ] Subject is clear and under 50 chars
- [ ] Body explains WHY (if needed)
- [ ] Issues are referenced
- [ ] Message follows Conventional Commits format
- [ ] No typos or grammatical errors

## Breaking Changes

If commit introduces breaking changes:
```
feat(api): change authentication endpoint format

BREAKING CHANGE: Authentication endpoint now returns
tokens in a nested object structure. Clients must
update to access tokens at response.data.tokens instead
of response.tokens.

Migration guide: docs/migrations/v2-auth.md

Closes #789
```

Generate the commit message now based on staged changes.
```

**Usage**: `/commit-message` before committing changes

### Example 10: Project Initialization Wizard

**File**: `.claude/commands/init-project.md`

```markdown
# Project Initialization Wizard

Interactive wizard to set up a new project with best practices.

## Step 1: Project Information

Answer these questions:
1. **Project name**: What is the project called?
2. **Project type**: Web app, API, library, CLI tool, mobile app?
3. **Programming language**: Python, JavaScript/TypeScript, Java, Go, C#, other?
4. **Description**: Brief description (1-2 sentences)
5. **License**: MIT, Apache 2.0, GPL, proprietary, other?
6. **Repository**: Git hosting (GitHub, GitLab, Bitbucket, none)?

## Step 2: Project Structure

Based on project type and language, create appropriate structure:

### Python Application
```
project_name/
├── .venv/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── core/
│       ├── __init__.py
│       └── ...
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── ...
├── docs/
├── .gitignore
├── README.md
├── CHANGELOG.md
├── DEVLOG.md
├── pyproject.toml
├── requirements.txt
└── setup.py
```

### JavaScript/TypeScript Application
```
project-name/
├── node_modules/
├── src/
│   ├── index.ts
│   └── ...
├── tests/
│   └── ...
├── dist/
├── docs/
├── .gitignore
├── README.md
├── CHANGELOG.md
├── package.json
├── tsconfig.json
└── jest.config.js
```

### Java Application
```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   └── resources/
│   └── test/
│       ├── java/
│       └── resources/
├── target/
├── docs/
├── .gitignore
├── README.md
├── CHANGELOG.md
├── pom.xml (Maven) or build.gradle (Gradle)
└── ...
```

## Step 3: Initialize Version Control

```bash
# Initialize Git
git init

# Create .gitignore
# (Generate appropriate .gitignore for language)

# Initial commit
git add .
git commit -m "chore: initial project setup"
```

## Step 4: Create Configuration Files

### Python: pyproject.toml
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
authors = [{name = "{author_name}", email = "{author_email}"}]
license = {text = "{license}"}
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=22.0",
    "flake8>=4.0",
    "mypy>=0.950"
]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### JavaScript: package.json
```json
{
  "name": "{project_name}",
  "version": "0.1.0",
  "description": "{description}",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src/**/*.ts",
    "format": "prettier --write src/**/*.ts"
  },
  "keywords": [],
  "author": "{author_name}",
  "license": "{license}",
  "devDependencies": {
    "@types/jest": "^29.0.0",
    "@typescript-eslint/eslint-plugin": "^5.0.0",
    "@typescript-eslint/parser": "^5.0.0",
    "eslint": "^8.0.0",
    "jest": "^29.0.0",
    "prettier": "^2.8.0",
    "typescript": "^5.0.0"
  }
}
```

## Step 5: Create Documentation Files

### README.md
```markdown
# {Project Name}

{Brief description}

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

### Prerequisites
- {Language} {version}+
- {Other requirements}

### Setup
    ```bash
    # Clone repository
    git clone {repo_url}
    cd {project_name}

    # Install dependencies
    {install_command}

    # Run tests
    {test_command}
    ```

## Usage

    ```{language}
    # Basic usage example
    ```

## Development

### Running Tests
    ```bash
    {test_command}
    ```

### Code Style
    ```bash
    {format_command}
    {lint_command}
    ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

{License}

## Authors

- {Author Name} - {email}
```

### CHANGELOG.md
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial project setup
```

### DEVLOG.md
```markdown
# Development Log

## Current Tasks

### High Priority
- [ ] Set up development environment
- [ ] Implement core functionality
- [ ] Add test suite

### Medium Priority
- [ ] Add documentation
- [ ] Set up CI/CD

### Low Priority
- [ ] Add examples
- [ ] Performance optimization

## Development History

### Project Setup
- **Date**: {current_date}
- **Initial Setup**: Created project structure with {language}
- **Architecture**: {brief architecture description}
```

## Step 6: Set Up Development Environment

### Python
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Unix/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### JavaScript/TypeScript
```bash
# Install dependencies
npm install

# or
yarn install
```

## Step 7: Set Up CI/CD (Optional)

### GitHub Actions Example
Create `.github/workflows/ci.yml`:
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up {Language}
      uses: {setup_action}
      with:
        {language}-version: {version}

    - name: Install dependencies
      run: {install_command}

    - name: Run tests
      run: {test_command}

    - name: Run linting
      run: {lint_command}
```

## Step 8: Initialize Testing Framework

### Python (pytest)
Create `tests/test_main.py`:
```python
"""Tests for main module."""
import pytest


def test_placeholder():
    """Placeholder test to verify testing framework."""
    assert True
```

### JavaScript (Jest)
Create `tests/index.test.ts`:
```typescript
describe('Placeholder', () => {
  test('should verify testing framework', () => {
    expect(true).toBe(true);
  });
});
```

## Step 9: Create .gitignore

Generate appropriate .gitignore:
```
# Dependencies
node_modules/
.venv/
venv/

# Build outputs
dist/
build/
*.pyc
__pycache__/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# Logs
*.log
logs/

# Test coverage
coverage/
.coverage
htmlcov/
```

## Step 10: Final Verification

Run checks to verify setup:
```bash
# {Language} specific checks
{verify_install_command}

# Run tests
{test_command}

# Check formatting
{format_command}

# Commit setup
git add .
git commit -m "chore: complete project initialization"
```

## Completion Checklist

- [ ] Project structure created
- [ ] Configuration files generated
- [ ] Documentation initialized (README, CHANGELOG, DEVLOG)
- [ ] Version control initialized
- [ ] Dependencies installed
- [ ] Testing framework set up
- [ ] CI/CD configured (optional)
- [ ] Development environment working
- [ ] Initial tests pass
- [ ] Initial commit made

## Next Steps

After initialization:
1. Review generated files and customize as needed
2. Add project-specific dependencies
3. Implement core functionality
4. Write tests
5. Update documentation
6. Set up remote repository (if using Git hosting)

Project initialization complete! Start coding! ✅
```

**Usage**: `/init-project` when starting a new project

## Common Pitfalls and Solutions

### Pitfall 1: Commands Too General

**Problem**: Commands try to do everything.

**Solution**: Create focused commands for specific workflows. It's better to have 10 specific commands than 1 generic command.

### Pitfall 2: Commands Too Long

**Problem**: Command files are thousands of lines.

**Solution**: Break complex commands into multiple specialized commands. Link related commands.

### Pitfall 3: Unclear Instructions

**Problem**: Claude doesn't understand what to do.

**Solution**: Use clear, explicit instructions. Include examples. Test commands before sharing.

### Pitfall 4: Missing Context

**Problem**: Commands don't have enough information.

**Solution**: Include all necessary context in the command. Reference relevant standards and conventions.

### Pitfall 5: Not Maintaining Commands

**Problem**: Commands become outdated and inaccurate.

**Solution**: Review and update commands regularly. Archive unused commands. Gather team feedback.

## Best Practices

### Command Design
- **Focused**: One command, one clear purpose
- **Clear**: Explicit instructions, no ambiguity
- **Complete**: Include all necessary information
- **Consistent**: Follow same format across commands
- **Maintainable**: Easy to update and improve

### Command Organization
- **Naming**: Use descriptive, lowercase-with-hyphens names
- **Grouping**: Organize by category or function
- **Indexing**: Maintain a README with command list
- **Versioning**: Track changes in version control
- **Documentation**: Explain when and how to use each command

### Team Collaboration
- **Consensus**: Get team agreement on workflows
- **Consistency**: Ensure everyone uses same commands
- **Training**: Onboard team members to command usage
- **Feedback**: Collect and act on team feedback
- **Evolution**: Continuously improve based on usage

### Testing Commands
- **Test Locally**: Try commands before sharing
- **Verify Output**: Ensure Claude produces desired results
- **Iterate**: Refine based on actual usage
- **Validate**: Confirm commands work for different scenarios
- **Monitor**: Track which commands are used and useful

## Success Criteria

- [ ] Commands are created in `.claude/commands/` directory
- [ ] Each command has clear purpose and instructions
- [ ] Commands follow Conventional Commits format (for commit commands)
- [ ] Commands are tested and produce expected results
- [ ] Documentation exists for command usage
- [ ] Team (if applicable) is trained on command usage
- [ ] Commands are maintained and updated regularly
- [ ] Feedback loop exists for continuous improvement
- [ ] Commands improve productivity and consistency
- [ ] Commands reduce errors and cognitive load

## Related Skills

- [`code-commit-workflow`](../code-commit-workflow/SKILL.md) - Git commit workflow that commands can automate
- [`test-driven-development`](../test-driven-development/SKILL.md) - TDD workflow commands can support
- [`create-claude-md`](../create-claude-md/SKILL.md) - Project instructions that work with commands
- [`plan-before-code`](../plan-before-code/SKILL.md) - Planning workflow commands
- [`code-review-security`](../code-review-security/SKILL.md) - Security review commands

## Additional Resources

### Claude Code Documentation
- [Claude Code Custom Commands](https://docs.anthropic.com/claude/docs/custom-commands) - Official documentation
- [Command Examples](https://github.com/anthropics/claude-code-examples) - Community examples

### Workflow Automation
- [GitHub Actions](https://docs.github.com/en/actions) - CI/CD automation
- [Pre-commit Hooks](https://pre-commit.com/) - Git hook automation
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message standard

### Team Collaboration
- [Documentation Guide](https://www.writethedocs.org/) - Documentation best practices
- [Code Review Best Practices](https://google.github.io/eng-practices/review/) - Google code review guide

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Claude Code best practices, development workflow patterns
