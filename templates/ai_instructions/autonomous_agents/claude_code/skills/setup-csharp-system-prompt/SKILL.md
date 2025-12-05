---
name: setup-csharp-system-prompt
description: Configure comprehensive C#/.NET development system prompt for Claude Code with best practices, standards, and workflows
version: 1.0.0
author: Benjamin Dourthe
language: C#
category: Configuration
priority: HIGH
tags: [csharp, dotnet, setup, system-prompt, configuration, standards, aspnetcore, entityframework]
---

# Setup C# System Prompt

Configure Claude Code with comprehensive C#/.NET development standards, best practices, and workflows optimized for production-quality enterprise applications.

## When to Use This Skill

Use this skill when you need to:

- Set up a new C#/.NET project with Claude Code

- Configure Claude Code for C#/.NET development

- Apply comprehensive C#/.NET development standards

- Establish consistent coding practices across C# projects

- Optimize Claude Code for ASP.NET Core, Entity Framework, and modern .NET workflows

## What This Skill Does

This skill helps you configure Claude Code with:

1. **C#/.NET Development Standards**

   - Modern C# 12 features (records, pattern matching, primary constructors)

   - PascalCase/camelCase naming conventions

   - Nullable reference types and async/await patterns

   - Class structure ordering and using directives organization

2. **Project Architecture Guidelines**

   - Clean Architecture structure (API, Core, Application, Infrastructure)

   - ASP.NET Core Web API patterns

   - Entity Framework Core configuration

   - Multi-project solution structure with .csproj templates

3. **Testing Framework**

   - xUnit/NUnit test patterns with Moq

   - Unit, integration, and API testing strategies

   - Arrange-Act-Assert (AAA) pattern

   - Test naming conventions and organization

4. **Development Workflow**

   - Task breakdown methodology

   - Iterative testing protocol with temporary tests

   - Quality gates and checklists

   - Version control best practices

5. **Code Quality Standards**

   - XML documentation comments (summary, params, returns, exceptions)

   - Comment guidelines (no meta-commentary or change tracking)

   - Error handling patterns with custom exceptions

   - Performance considerations and LINQ optimization

6. **ASP.NET Core Patterns**

   - Controller design with route attributes and HTTP methods

   - Service layer with dependency injection

   - Repository pattern with Entity Framework Core

   - Middleware, filters, and configuration management

7. **Entity Framework Core**

   - DbContext configuration and best practices

   - Migration management

   - Query optimization and projection

   - Connection string management in appsettings.json

8. **Code Quality Tools**

   - StyleCop analyzers for style enforcement

   - Roslyn analyzers for code quality

   - SonarAnalyzer for security and bugs

   - Code coverage with Coverlet

## Prerequisites

- Claude Code installed and configured

- .NET 8 SDK or later installed

- Basic understanding of C# and .NET development

- Project directory created (or ready to create new solution)

- SQL Server or alternative database (for EF Core projects)

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**

- Best for: Enterprise applications, full-stack web APIs, complex domain logic

- Features: Complete Clean Architecture guidance, extensive ASP.NET Core patterns, detailed EF Core configuration

- Token count: ~40,000 tokens

- File: `agent_prompts/autonomous_agents/claude_code/csharp/CLAUDE_comprehensive_40k.md`

**Condensed Version (~20k tokens)**

- Best for: Quick prototypes, class libraries, smaller microservices

- Features: Essential guidelines, core best practices, streamlined workflow

- Token count: ~20,000 tokens

- File: `agent_prompts/autonomous_agents/claude_code/csharp/CLAUDE_condensed_20k.md`

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the C# system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

1. Navigate to your project root directory

2. Copy the chosen system prompt file to `CLAUDE.md`:
   ```bash
   # For comprehensive version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/csharp/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/csharp/CLAUDE_condensed_20k.md ./CLAUDE.md
   ```
3. Claude Code will automatically detect and load this file

#### Method B: Global Configuration

Copy to your user's Claude directory for all C# projects:
```bash
# Windows
cp CLAUDE_comprehensive_40k.md %USERPROFILE%\.claude\CLAUDE.md

# macOS/Linux
cp CLAUDE_comprehensive_40k.md ~/.claude/CLAUDE.md
```

### Step 3: Verify Configuration

Test that the system prompt is active by asking Claude Code to:

1. **Create a simple service class** and observe if it follows the standards:
   ```
   "Create a UserService class with dependency injection and a method to get user by ID"
   ```

   Expected behavior:

   - Uses modern C# features (nullable reference types, async/await)

   - Includes XML documentation comments

   - Follows PascalCase naming conventions

   - Private fields use _camelCase with underscore prefix

   - Proper class structure order (fields, constructor, methods)

2. **Request project structure** and verify it matches standards:
   ```
   "Show me the recommended project structure for an ASP.NET Core Web API"
   ```

   Expected behavior:

   - Shows Clean Architecture structure (API, Core, Application, Infrastructure)

   - Includes solution file and proper project references

   - Shows test projects (UnitTests, IntegrationTests)

   - Includes CHANGELOG.md, README.md, .gitignore

3. **Ask about testing** and confirm it knows the framework:
   ```
   "How should I structure xUnit tests for the UserService?"
   ```

   Expected behavior:

   - Mentions xUnit with Moq for mocking

   - Describes Arrange-Act-Assert pattern

   - Explains test naming conventions (MethodName_Scenario_ExpectedResult)

   - Shows proper test class structure with constructor setup

4. **Verify Entity Framework knowledge**:
   ```
   "Create a DbContext for a User entity with proper configuration"
   ```

   Expected behavior:

   - Uses DbSet<T> properties

   - Includes OnModelCreating for configuration

   - Shows proper connection string usage

   - Includes navigation properties and relationships

### Step 4: Customize for Your Organization (Optional)

If you need to add organization-specific standards:

1. Open the CLAUDE.md file in your project

2. Add a new section at the end:
   ```markdown
   # Organization-Specific Standards

   ## Additional Requirements
   - [Your custom coding standards]

   - [Internal NuGet package preferences]

   - [Company security/compliance requirements]

   - [CI/CD pipeline requirements]
   ```
3. Save and restart Claude Code session

### Step 5: Commit to Version Control

Add the CLAUDE.md to your repository so team members have consistent configuration:

```bash
git add CLAUDE.md
git commit -m "Add Claude Code C#/.NET system prompt configuration"
git push
```

## Key Features of the C# System Prompt

### 1. Modern C# Features (C# 12 / .NET 8)

**Records for DTOs:**
```csharp
public record UserDto(
    int Id,
    string Name,
    string Email,
    DateTime CreatedAt
);
```

**Pattern Matching:**
```csharp
public string GetStatus(User user) => user.Role switch
{
    UserRole.Admin => "Administrator",
    UserRole.User => "Regular User",
    _ => throw new ArgumentException()
};
```

**Primary Constructors:**
```csharp
public class UserService(
    IUserRepository repository,
    ILogger<UserService> logger) : IUserService
{
    public async Task<User> GetByIdAsync(int id)
    {
        logger.LogInformation("Fetching user {Id}", id);
        return await repository.GetByIdAsync(id);
    }
}
```

**Nullable Reference Types:**
```csharp
#nullable enable

public async Task<User?> FindByEmailAsync(string email)
{
    return await _repository.GetByEmailAsync(email);
}
```

### 2. Clean Architecture Project Structure

```
ProjectName/
├── src/
│   ├── ProjectName.API/              # Web API layer
│   ├── ProjectName.Core/             # Domain entities
│   ├── ProjectName.Application/      # Business logic
│   └── ProjectName.Infrastructure/   # Data access
├── tests/
│   ├── ProjectName.UnitTests/
│   └── ProjectName.IntegrationTests/
├── ProjectName.sln
└── CHANGELOG.md
```

### 3. ASP.NET Core Controller Pattern

```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserService _service;

    public UsersController(IUserService service) => _service = service;

    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(UserDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<UserDto>> GetUser(int id)
    {
        var user = await _service.GetByIdAsync(id);
        return Ok(user);
    }
}
```

### 4. xUnit Testing with Moq

```csharp
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _mockRepo;
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _mockRepo = new Mock<IUserRepository>();
        _sut = new UserService(_mockRepo.Object);
    }

    [Fact]
    public async Task GetByIdAsync_WithValidId_ReturnsUser()
    {
        // Arrange
        var expectedUser = new User { Id = 1, Name = "John" };
        _mockRepo.Setup(r => r.GetByIdAsync(1))
            .ReturnsAsync(expectedUser);

        // Act
        var result = await _sut.GetByIdAsync(1);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("John", result.Name);
    }
}
```

### 5. Entity Framework Core DbContext

```csharp
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name)
                .IsRequired()
                .HasMaxLength(100);
            entity.HasIndex(e => e.Email)
                .IsUnique();
        });
    }
}
```

### 6. Dependency Injection Configuration

```csharp
// Program.cs (.NET 8 minimal hosting)
var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUserService, UserService>();

var app = builder.Build();

// Configure middleware pipeline
app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

### 7. Code Quality Tools Configuration

**.editorconfig for StyleCop:**
```ini
[*.cs]
# Naming conventions
dotnet_naming_rule.private_fields_rule.severity = warning
dotnet_naming_rule.private_fields_rule.symbols = private_fields
dotnet_naming_rule.private_fields_rule.style = underscore_camel_case

# Code style
csharp_prefer_braces = true:warning
csharp_prefer_simple_using_statement = true:suggestion
```

**Add analyzers to .csproj:**
```xml
<ItemGroup>
  <PackageReference Include="StyleCop.Analyzers" Version="1.2.0-beta.507" />
  <PackageReference Include="SonarAnalyzer.CSharp" Version="9.12.0.78982" />
</ItemGroup>
```

### 8. Comment Standards

**No change-tracking or meta-commentary:**
```csharp
// BAD: Don't document changes
int result = Calculate(12);  // Changed from 10 to 12

// GOOD: Explain reasoning
int result = Calculate(12);  // Use 12 to match API rate limit threshold
```

### 9. Error Handling Patterns

```csharp
// Custom exception
public class NotFoundException : Exception
{
    public NotFoundException(string message) : base(message) { }
}

// Service with error handling
public async Task<UserDto> GetByIdAsync(int id)
{
    var user = await _repository.GetByIdAsync(id)
        ?? throw new NotFoundException($"User {id} not found");

    return MapToDto(user);
}

// Controller with error handling
[HttpGet("{id:int}")]
public async Task<ActionResult<UserDto>> GetUser(int id)
{
    try
    {
        var user = await _service.GetByIdAsync(id);
        return Ok(user);
    }
    catch (NotFoundException ex)
    {
        return NotFound(ex.Message);
    }
}
```

### 10. LINQ Query Optimization

```csharp
// Good - Use projection to reduce data transfer
public async Task<List<UserDto>> GetActiveUsersAsync()
{
    return await _context.Users
        .Where(u => u.IsActive)
        .Where(u => u.LastLogin > DateTime.UtcNow.AddDays(-30))
        .OrderBy(u => u.Name)
        .Select(u => new UserDto(u.Id, u.Name, u.Email, u.CreatedAt))
        .ToListAsync();
}

// Good - Use AsNoTracking for read-only queries
public async Task<User?> GetByIdAsync(int id)
{
    return await _context.Users
        .AsNoTracking()
        .FirstOrDefaultAsync(u => u.Id == id);
}
```

### 11. Iterative Testing Protocol

**CRITICAL: Test-Driven Problem Solving**

When implementing features or fixing bugs:

1. **Create temporary test scripts** in `tests/temp/` directory

2. **Write challenging tests** that thoroughly validate the solution

3. **Run tests and iterate** - if tests fail, modify implementation and document in DEVLOG.md

4. **Clean up** - delete all `tests/temp/` files after successful implementation

Example DEVLOG.md entry:
```markdown
### Feature: User Authentication
**Iteration 1**: Created tests/temp/UserAuthTests.cs

- Tests failed: Password validation too weak

- Solution: Enhanced regex pattern

**Iteration 2**: Re-ran tests

- Tests failed: Edge case with special characters

- Solution: Added character escaping

**Iteration 3**: Final run

- All tests passed ✅

- Deleted tests/temp/UserAuthTests.cs

- Moved 3 test cases to tests/ProjectName.UnitTests/Services/UserServiceTests.cs
```

### 12. Command Preferences

**CRITICAL: Never run commands in chat. Always request user execution.**

Example:
```
Please run in your terminal:

1. Navigate to solution directory:
   cd ProjectName

2. Build solution:
   dotnet build

3. Run tests:
   dotnet test

4. Share any errors for assistance.
```

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the solution root directory (same level as .sln file) and restart Claude Code session

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version

### Issue: Standards Not Being Followed
**Solution**: Explicitly reference the standard in your request:
```
"Following the controller pattern in CLAUDE.md, create a UsersController with CRUD operations"
```

### Issue: Need Different Standards for Subproject
**Solution**: Create a project-specific CLAUDE.md in the subproject directory with overrides

### Issue: Entity Framework Not Recognized
**Solution**: Ensure you're working in a project with `Microsoft.EntityFrameworkCore` package reference

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with C#/.NET system prompt (CLAUDE.md in solution root)

- [ ] Verified configuration by testing service class generation

- [ ] Confirmed Clean Architecture project structure knowledge

- [ ] Validated xUnit testing framework understanding

- [ ] Confirmed ASP.NET Core controller pattern knowledge

- [ ] Verified Entity Framework Core DbContext configuration

- [ ] Optionally customized for organization-specific needs

- [ ] Committed CLAUDE.md to version control for team consistency

- [ ] Tested with a sample project creation request

- [ ] Verified modern C# features (records, pattern matching) are used

## Related Skills

- `generate-xml-docs`: Use after setup to document existing C# code

- `setup-test-infrastructure`: Establish xUnit testing framework following system prompt standards

- `code-review-quality`: Review C# code quality against configured standards

- `cleanup-csharp`: Clean up C# code following configured standards

- `setup-ef-migrations`: Configure Entity Framework Core migrations

## Additional Resources

- [C# Coding Conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)

- [.NET API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/dotnet/README.md)

- [ASP.NET Core Documentation](https://learn.microsoft.com/en-us/aspnet/core/)

- [Entity Framework Core Documentation](https://learn.microsoft.com/en-us/ef/core/)

- [xUnit Documentation](https://xunit.net/)

- [Moq Documentation](https://github.com/moq/moq4)

- [StyleCop Documentation](https://github.com/DotNetAnalyzers/StyleCopAnalyzers)

## Troubleshooting

### Q: Claude Code keeps suggesting Python patterns for my C# code
**A**: Ensure CLAUDE.md is in the correct location and restart the session. You may also need to explicitly mention "following C# best practices" in your request.

### Q: The comprehensive version is too long for my token budget
**A**: Switch to the condensed version, or create a custom version that includes only the sections most relevant to your project type.

### Q: How do I combine Python and C# system prompts for a polyglot project?
**A**: Create a combined CLAUDE.md that includes both language standards, organized by language-specific sections.

### Q: Claude Code isn't using modern C# features like records or primary constructors
**A**: Explicitly request modern features: "Using C# 12 records and primary constructors, create a UserDto class"

### Q: The system prompt suggests packages I don't want to use
**A**: Add an "Organization-Specific Standards" section to your CLAUDE.md specifying preferred packages and frameworks.

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
**Compatible with**: .NET 8+, C# 12
