# CLAUDE.md - C# Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for C#/.NET development*

---

# Quick Start for Common Tasks

## Section Usage Map
- **Bug Fix**: Sections 1, 3, 9
- **New Feature**: Sections 1-5, 7
- **Refactoring**: Sections 3, 6, 9
- **Project Setup**: All sections

## Task-Specific Quick Reference
- **Fix a method**: Focus sections 3, 9
- **New project**: Use sections 2, 4, 5
- **Code review**: Apply sections 3, 10

## Context-Aware Behavior
- **For class libraries**: Minimal structure
- **For web APIs**: Full ASP.NET Core architecture
- **For debugging**: Focus on problem-solving

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation
- Minimal testing setup
- Focus on core functionality

### Full Mode (for new projects)
- Complete ASP.NET Core architecture
- Comprehensive testing
- Full documentation

## Claude Code Terminal Commands
- **Run tests**: `claude run dotnet test`
- **Build project**: `claude run dotnet build`
- **Start application**: `claude run dotnet run`
- **New project**: `claude init [project-name]`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding
- Never make assumptions about missing requirements
- Frame questions to gather specific technical requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work
- Explain implementation details, reasoning, and coding concepts
- Enable learning through understanding, not copy-paste
- Reference Microsoft documentation for non-obvious concepts

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions
- Analyze problems independently
- Compare alternatives and recommend best solution
- Clearly explain reasoning and trade-offs

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity
- **Code Modification**: Edit originals, don't create '_enhanced' versions
- **Codebase Cleanup**: Remove obsolete methods
- **Refactoring**: Consolidate duplicate logic

### Quality Assurance
- Review code for: quality, efficiency, best practices, security, performance
- If already optimal, confirm briefly with reasoning

### System Prompt Adherence
- Periodically review these instructions during long conversations
- Maintain consistency with all standards and workflows


# 2. Project Architecture
---

## Standard ASP.NET Core Web API Structure

```
ProjectName/
├── src/
│   ├── ProjectName.API/                # Web API project
│   │   ├── Controllers/
│   │   ├── Program.cs
│   │   ├── appsettings.json
│   │   └── appsettings.Development.json
│   ├── ProjectName.Core/               # Domain layer
│   │   ├── Entities/
│   │   ├── Interfaces/
│   │   ├── DTOs/
│   │   └── Exceptions/
│   ├── ProjectName.Application/        # Business logic
│   │   ├── Services/
│   │   ├── Validators/
│   │   └── Mappings/
│   └── ProjectName.Infrastructure/     # Data access
│       ├── Data/
│       ├── Repositories/
│       └── Migrations/
├── tests/
│   ├── ProjectName.UnitTests/
│   ├── ProjectName.IntegrationTests/
│   └── ProjectName.API.Tests/
├── ProjectName.sln
├── CHANGELOG.md
├── README.md
└── .gitignore
```

## Project Initialization Sequence

1. **Create solution**: `dotnet new sln -n ProjectName`
2. **Create projects**:
   - `dotnet new webapi -n ProjectName.API`
   - `dotnet new classlib -n ProjectName.Core`
   - `dotnet new classlib -n ProjectName.Application`
   - `dotnet new classlib -n ProjectName.Infrastructure`
3. **Add projects to solution**: `dotnet sln add src/**/*.csproj`
4. **Create test projects**: `dotnet new xunit -n ProjectName.UnitTests`
5. **Configure appsettings.json** with connection strings
6. **Create `.gitignore`** (bin/, obj/, .vs/)
7. **Create `CHANGELOG.md`** starting with version 0.1.0
8. **Create `README.md`** with setup instructions
9. **Set up Entity Framework migrations**

## Project File Template (.csproj)
```xml
<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <Version>0.1.0</Version>
    <Authors>Benjamin Dourthe</Authors>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\ProjectName.Application\ProjectName.Application.csproj" />
  </ItemGroup>

</Project>
```

## appsettings.json Template
```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=ProjectNameDb;Trusted_Connection=True;"
  },
  "AllowedHosts": "*"
}
```


# 3. Code Standards
---

## C# Style Guidelines

### Naming Conventions
```csharp
// Classes and Interfaces: PascalCase
public class UserService { }
public interface IUserRepository { }

// Methods and Properties: PascalCase
public User GetUserById(int id) { }
public string UserName { get; set; }

// Private fields: _camelCase with underscore prefix
private readonly IUserRepository _userRepository;

// Constants: PascalCase
public const int MaxRetryAttempts = 3;

// Parameters and local variables: camelCase
public void ProcessUser(User user, bool isActive) { }

// Namespaces: PascalCase with dots
namespace ProjectName.Application.Services;
```

### Class Structure Order
```csharp
public class UserService : IUserService
{
    // 1. Private fields
    private readonly IUserRepository _userRepository;
    private readonly ILogger<UserService> _logger;

    // 2. Constructors
    public UserService(
        IUserRepository userRepository,
        ILogger<UserService> logger)
    {
        _userRepository = userRepository;
        _logger = logger;
    }

    // 3. Public properties
    public bool IsInitialized { get; private set; }

    // 4. Public methods
    public async Task<UserDto> GetUserByIdAsync(int id)
    {
        _logger.LogInformation("Retrieving user {UserId}", id);
        var user = await _userRepository.GetByIdAsync(id);
        return MapToDto(user);
    }

    // 5. Protected methods
    protected virtual void ValidateUser(User user)
    {
        if (string.IsNullOrWhiteSpace(user.Email))
        {
            throw new ValidationException("Email is required");
        }
    }

    // 6. Private methods
    private UserDto MapToDto(User user)
    {
        return new UserDto
        {
            Id = user.Id,
            Name = user.Name,
            Email = user.Email
        };
    }
}
```

### Using Directives Organization
```csharp
// 1. System namespaces
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

// 2. Microsoft namespaces
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

// 3. Third-party packages
using AutoMapper;
using FluentValidation;

// 4. Project namespaces
using ProjectName.Core.Entities;
using ProjectName.Core.Interfaces;
using ProjectName.Application.DTOs;
```

### Modern C# Features (C# 12 / .NET 8)

#### Records
```csharp
// ✅ Good - Use records for DTOs
public record UserDto(
    int Id,
    string Name,
    string Email,
    DateTime CreatedAt
);

// ✅ With validation
public record CreateUserRequest(string Name, string Email)
{
    public CreateUserRequest : this(Name, Email)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(Name);
        ArgumentException.ThrowIfNullOrWhiteSpace(Email);
    }
}
```

#### Pattern Matching
```csharp
// ✅ Switch expressions
public string GetUserStatus(User user) => user.Role switch
{
    UserRole.Admin => "Administrator",
    UserRole.User => "Regular User",
    UserRole.Guest => "Guest",
    _ => throw new ArgumentException("Unknown role")
};

// ✅ Property patterns
public decimal CalculateDiscount(Order order) => order switch
{
    { Total: > 1000, IsPremium: true } => order.Total * 0.20m,
    { Total: > 500 } => order.Total * 0.10m,
    _ => 0m
};
```

#### Nullable Reference Types
```csharp
// ✅ Good - Enable nullable reference types
#nullable enable

public class UserService
{
    // Non-nullable - must be initialized
    private readonly IUserRepository _repository;

    // Nullable - can be null
    private User? _cachedUser;

    public async Task<User?> FindByEmailAsync(string email)
    {
        return await _repository.GetByEmailAsync(email);
    }

    public User GetUserById(int id)
    {
        return _repository.GetById(id)
            ?? throw new NotFoundException($"User {id} not found");
    }
}
```

#### LINQ and Async/Await
```csharp
// ✅ Good - Async LINQ with EF Core
public async Task<List<UserDto>> GetActiveUsersAsync()
{
    return await _context.Users
        .Where(u => u.IsActive)
        .Where(u => u.LastLogin > DateTime.UtcNow.AddDays(-30))
        .OrderBy(u => u.Name)
        .Select(u => new UserDto(u.Id, u.Name, u.Email, u.CreatedAt))
        .ToListAsync();
}

// ✅ Good - Parallel processing
public async Task<Dictionary<string, int>> GetUserCountByRoleAsync()
{
    var users = await _context.Users.ToListAsync();
    return users
        .AsParallel()
        .GroupBy(u => u.Role.ToString())
        .ToDictionary(g => g.Key, g => g.Count());
}
```

#### Primary Constructors (C# 12)
```csharp
// ✅ Good - Primary constructors for dependency injection
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



### Comment Guidelines

**Placement and Style:**
- **Above code blocks**: Comments explain why, not just what
- **No inline comments**: Avoid same-line comments unless extremely clear
- **No meta-commentary**: Don't document editing history
- **No change tracking**: Never add comments like "changed value to 12" or "updated parameter"
- **Descriptive**: Focus on logic, decision reasoning, and non-obvious behavior

**Prohibited Comment Patterns:**
```csharp
// BAD: Don't document changes
int result = Calculate(12);  // Changed from 10 to 12
string value = newValue;  // Updated to use newValue instead of oldValue

// GOOD: Explain reasoning
int result = Calculate(12);  // Use 12 to match API rate limit threshold
string value = newValue;  // Cache invalidation requires fresh value
```


### Comment Guidelines

**Placement and Style:**
- **Above code blocks**: Comments explain why, not just what
- **No inline comments**: Avoid same-line comments unless extremely clear
- **No meta-commentary**: Don't document editing history
- **No change tracking**: Never add comments like "changed value to 12" or "updated parameter"
- **Descriptive**: Focus on logic, decision reasoning, and non-obvious behavior

**Prohibited Comment Patterns:**
```csharp
// BAD: Don't document changes
int result = Calculate(12);  // Changed from 10 to 12
string value = newValue;  // Updated to use newValue instead of oldValue

// GOOD: Explain reasoning
int result = Calculate(12);  // Use 12 to match API rate limit threshold
string value = newValue;  // Cache invalidation requires fresh value
```


### ASP.NET Core Patterns

#### Controller
```csharp
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;
    private readonly ILogger<UsersController> _logger;

    public UsersController(
        IUserService userService,
        ILogger<UsersController> logger)
    {
        _userService = userService;
        _logger = logger;
    }

    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(UserDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<UserDto>> GetUser(int id)
    {
        try
        {
            var user = await _userService.GetUserByIdAsync(id);
            return Ok(user);
        }
        catch (NotFoundException)
        {
            return NotFound();
        }
    }

    [HttpPost]
    [ProducesResponseType(typeof(UserDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserDto>> CreateUser(
        [FromBody] CreateUserRequest request)
    {
        var user = await _userService.CreateAsync(request);
        return CreatedAtAction(
            nameof(GetUser),
            new { id = user.Id },
            user);
    }

    [HttpPut("{id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateUser(
        int id,
        [FromBody] UpdateUserRequest request)
    {
        await _userService.UpdateAsync(id, request);
        return NoContent();
    }

    [HttpDelete("{id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> DeleteUser(int id)
    {
        await _userService.DeleteAsync(id);
        return NoContent();
    }
}
```

#### Service Layer
```csharp
public interface IUserService
{
    Task<UserDto> GetUserByIdAsync(int id);
    Task<UserDto> CreateAsync(CreateUserRequest request);
    Task UpdateAsync(int id, UpdateUserRequest request);
    Task DeleteAsync(int id);
}

public class UserService : IUserService
{
    private readonly IUserRepository _repository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IMapper _mapper;
    private readonly ILogger<UserService> _logger;

    public UserService(
        IUserRepository repository,
        IUnitOfWork unitOfWork,
        IMapper mapper,
        ILogger<UserService> logger)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<UserDto> GetUserByIdAsync(int id)
    {
        _logger.LogDebug("Fetching user with ID {UserId}", id);

        var user = await _repository.GetByIdAsync(id)
            ?? throw new NotFoundException($"User with ID {id} not found");

        return _mapper.Map<UserDto>(user);
    }

    public async Task<UserDto> CreateAsync(CreateUserRequest request)
    {
        _logger.LogInformation("Creating new user with email {Email}", request.Email);

        // Validate unique email
        if (await _repository.ExistsByEmailAsync(request.Email))
        {
            throw new DuplicateException($"User with email {request.Email} already exists");
        }

        var user = new User
        {
            Name = request.Name,
            Email = request.Email,
            CreatedAt = DateTime.UtcNow
        };

        await _repository.AddAsync(user);
        await _unitOfWork.SaveChangesAsync();

        _logger.LogInformation("User created with ID {UserId}", user.Id);

        return _mapper.Map<UserDto>(user);
    }
}
```

#### Repository Pattern
```csharp
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(int id);
    Task<IEnumerable<T>> GetAllAsync();
    Task AddAsync(T entity);
    void Update(T entity);
    void Delete(T entity);
}

public interface IUserRepository : IRepository<User>
{
    Task<User?> GetByEmailAsync(string email);
    Task<bool> ExistsByEmailAsync(string email);
    Task<IEnumerable<User>> GetActiveUsersAsync();
}

public class UserRepository : IUserRepository
{
    private readonly ApplicationDbContext _context;

    public UserRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<User?> GetByIdAsync(int id)
    {
        return await _context.Users
            .FirstOrDefaultAsync(u => u.Id == id);
    }

    public async Task<User?> GetByEmailAsync(string email)
    {
        return await _context.Users
            .FirstOrDefaultAsync(u => u.Email == email);
    }

    public async Task<bool> ExistsByEmailAsync(string email)
    {
        return await _context.Users
            .AnyAsync(u => u.Email == email);
    }

    public async Task<IEnumerable<User>> GetActiveUsersAsync()
    {
        return await _context.Users
            .Where(u => u.IsActive)
            .ToListAsync();
    }

    public async Task AddAsync(User entity)
    {
        await _context.Users.AddAsync(entity);
    }

    public void Update(User entity)
    {
        _context.Users.Update(entity);
    }

    public void Delete(User entity)
    {
        _context.Users.Remove(entity);
    }

    public async Task<IEnumerable<User>> GetAllAsync()
    {
        return await _context.Users.ToListAsync();
    }
}
```

#### Entity Design
```csharp
public class User
{
    public int Id { get; set; }

    [Required]
    [MaxLength(100)]
    public string Name { get; set; } = string.Empty;

    [Required]
    [MaxLength(255)]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    public UserRole Role { get; set; } = UserRole.User;

    public bool IsActive { get; set; } = true;

    public DateTime CreatedAt { get; set; }

    public DateTime? UpdatedAt { get; set; }

    // Navigation properties
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}

public enum UserRole
{
    Guest,
    User,
    Admin
}
```

#### DbContext Configuration
```csharp
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<User>(entity =>
        {
            entity.ToTable("Users");

            entity.HasKey(e => e.Id);

            entity.Property(e => e.Name)
                .IsRequired()
                .HasMaxLength(100);

            entity.Property(e => e.Email)
                .IsRequired()
                .HasMaxLength(255);

            entity.HasIndex(e => e.Email)
                .IsUnique();

            entity.Property(e => e.Role)
                .HasConversion<string>()
                .HasMaxLength(20);

            entity.Property(e => e.CreatedAt)
                .HasDefaultValueSql("GETUTCDATE()");
        });
    }
}
```


# 4. Documentation Standards
---

## XML Documentation Comments

### Complex Methods
```csharp
/// <summary>
/// Processes user data with validation and transformation.
/// </summary>
/// <param name="request">The user creation request containing name and email.</param>
/// <param name="cancellationToken">Cancellation token for async operations.</param>
/// <returns>A task that represents the asynchronous operation. The task result contains the created user DTO.</returns>
/// <exception cref="ValidationException">Thrown when the request data is invalid.</exception>
/// <exception cref="DuplicateException">Thrown when the email already exists.</exception>
/// <remarks>
/// This method performs the following operations:
/// <list type="bullet">
/// <item><description>Validates input data according to business rules</description></item>
/// <item><description>Transforms data to the internal format</description></item>
/// <item><description>Saves to database with transactional guarantees</description></item>
/// </list>
/// </remarks>
/// <example>
/// <code>
/// var request = new CreateUserRequest("John Doe", "john@example.com");
/// var user = await service.CreateUserAsync(request);
/// </code>
/// </example>
public async Task<UserDto> CreateUserAsync(
    CreateUserRequest request,
    CancellationToken cancellationToken = default)
{
    // Implementation
}
```

### Simple Methods
```csharp
/// <summary>
/// Calculates the total price including tax.
/// </summary>
/// <param name="items">List of item prices.</param>
/// <returns>Total price with tax applied.</returns>
public decimal CalculateTotal(List<decimal> items)
{
    return items.Sum() * 1.1m;
}
```

### Class Documentation
```csharp
/// <summary>
/// Service layer for user management operations.
/// </summary>
/// <remarks>
/// This service handles all business logic related to user entities,
/// including CRUD operations, validation, and business rules enforcement.
/// All methods are asynchronous and support cancellation tokens.
/// </remarks>
public class UserService : IUserService
{
    // Implementation
}
```

## README.md Structure
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]

## Technologies
- .NET 8
- ASP.NET Core Web API
- Entity Framework Core
- SQL Server

## Installation

### Prerequisites
- .NET 8 SDK or higher
- SQL Server 2019+ or LocalDB
- Visual Studio 2022 or VS Code

### Setup
    ```bash
    git clone <REPO_URL>
    cd [project-name]
    dotnet restore
    dotnet build
    ```

**Note**: Your repository URL is stored in `.git/config`. To retrieve it:

```bash
git config --get remote.origin.url
```

### Database Setup
    ```bash
    dotnet ef database update
    ```

### Configuration
Update `appsettings.Development.json`:
    ```json
    {
      "ConnectionStrings": {
        "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=MyDb;Trusted_Connection=True;"
      }
    }
    ```

## Usage
    ```bash
    dotnet run --project src/ProjectName.API
    ```

## Testing
    ```bash
    dotnet test
    ```

## API Documentation
After starting the application, visit:
- Swagger UI: https://localhost:5001/swagger
- OpenAPI Spec: https://localhost:5001/swagger/v1/swagger.json
```

## CHANGELOG.md Structure
```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Improvements

### Fixed
- Bug fixes

### Removed
- Deprecated items
```


# 5. Testing Framework
---

## Test Structure

1. **Unit Tests**: Test individual methods with mocking
2. **Integration Tests**: Test with real database (in-memory or test DB)
3. **API Tests**: Test controllers with WebApplicationFactory
4. **End-to-End Tests**: Test complete user flows

## xUnit Test Template

```csharp
/// <summary>
/// Unit tests for UserService.
/// </summary>
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _mockRepository;
    private readonly Mock<IUnitOfWork> _mockUnitOfWork;
    private readonly Mock<IMapper> _mockMapper;
    private readonly Mock<ILogger<UserService>> _mockLogger;
    private readonly UserService _sut; // System Under Test

    public UserServiceTests()
    {
        _mockRepository = new Mock<IUserRepository>();
        _mockUnitOfWork = new Mock<IUnitOfWork>();
        _mockMapper = new Mock<IMapper>();
        _mockLogger = new Mock<ILogger<UserService>>();

        _sut = new UserService(
            _mockRepository.Object,
            _mockUnitOfWork.Object,
            _mockMapper.Object,
            _mockLogger.Object);
    }

    [Fact]
    public async Task GetUserByIdAsync_WithValidId_ReturnsUserDto()
    {
        // Arrange
        var userId = 1;
        var user = new User
        {
            Id = userId,
            Name = "John Doe",
            Email = "john@example.com"
        };
        var expectedDto = new UserDto(userId, "John Doe", "john@example.com", DateTime.UtcNow);

        _mockRepository
            .Setup(r => r.GetByIdAsync(userId))
            .ReturnsAsync(user);

        _mockMapper
            .Setup(m => m.Map<UserDto>(user))
            .Returns(expectedDto);

        // Act
        var result = await _sut.GetUserByIdAsync(userId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(userId, result.Id);
        Assert.Equal("John Doe", result.Name);
        _mockRepository.Verify(r => r.GetByIdAsync(userId), Times.Once);
    }

    [Fact]
    public async Task GetUserByIdAsync_WithInvalidId_ThrowsNotFoundException()
    {
        // Arrange
        var userId = 999;
        _mockRepository
            .Setup(r => r.GetByIdAsync(userId))
            .ReturnsAsync((User?)null);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<NotFoundException>(
            () => _sut.GetUserByIdAsync(userId));

        Assert.Contains(userId.ToString(), exception.Message);
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("invalid-email")]
    public async Task CreateAsync_WithInvalidEmail_ThrowsValidationException(string invalidEmail)
    {
        // Arrange
        var request = new CreateUserRequest("John Doe", invalidEmail);

        // Act & Assert
        await Assert.ThrowsAsync<ValidationException>(
            () => _sut.CreateAsync(request));
    }

    [Fact]
    public async Task CreateAsync_WithDuplicateEmail_ThrowsDuplicateException()
    {
        // Arrange
        var request = new CreateUserRequest("John Doe", "john@example.com");

        _mockRepository
            .Setup(r => r.ExistsByEmailAsync(request.Email))
            .ReturnsAsync(true);

        // Act & Assert
        await Assert.ThrowsAsync<DuplicateException>(
            () => _sut.CreateAsync(request));

        _mockRepository.Verify(r => r.AddAsync(It.IsAny<User>()), Times.Never);
    }
}
```

## Integration Testing
```csharp
public class UserServiceIntegrationTests : IClassFixture<DatabaseFixture>
{
    private readonly DatabaseFixture _fixture;
    private readonly IUserService _service;

    public UserServiceIntegrationTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
        _service = new UserService(
            new UserRepository(_fixture.Context),
            new UnitOfWork(_fixture.Context),
            new Mapper(new MapperConfiguration(cfg => cfg.AddProfile<MappingProfile>())),
            Mock.Of<ILogger<UserService>>());
    }

    [Fact]
    public async Task CreateAsync_WithValidData_SavesToDatabase()
    {
        // Arrange
        var request = new CreateUserRequest("Jane Doe", "jane@example.com");

        // Act
        var result = await _service.CreateAsync(request);

        // Assert
        Assert.NotNull(result);
        Assert.True(result.Id > 0);

        var savedUser = await _fixture.Context.Users.FindAsync(result.Id);
        Assert.NotNull(savedUser);
        Assert.Equal("Jane Doe", savedUser.Name);
    }
}

public class DatabaseFixture : IDisposable
{
    public ApplicationDbContext Context { get; }

    public DatabaseFixture()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        Context = new ApplicationDbContext(options);
        Context.Database.EnsureCreated();
    }

    public void Dispose()
    {
        Context.Database.EnsureDeleted();
        Context.Dispose();
    }
}
```

## API Testing
```csharp
public class UsersControllerTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;

    public UsersControllerTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetUser_WithValidId_Returns200AndUser()
    {
        // Arrange
        var userId = 1;

        // Act
        var response = await _client.GetAsync($"/api/users/{userId}");

        // Assert
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var user = JsonSerializer.Deserialize<UserDto>(content);

        Assert.NotNull(user);
        Assert.Equal(userId, user.Id);
    }

    [Fact]
    public async Task CreateUser_WithValidRequest_Returns201()
    {
        // Arrange
        var request = new CreateUserRequest("New User", "newuser@example.com");
        var jsonContent = JsonSerializer.Serialize(request);
        var httpContent = new StringContent(jsonContent, Encoding.UTF8, "application/json");

        // Act
        var response = await _client.PostAsync("/api/users", httpContent);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        Assert.NotNull(response.Headers.Location);
    }
}
```


# 6. Development Workflow
---

## Task Breakdown

### When to Use
- Projects >30 minutes
- Multi-component applications
- Complex features
- Integration tasks

### Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope]

### Prerequisites
- .NET 8 SDK installed
- SQL Server configured
- Entity Framework tools

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Outputs]
**Time**: [15-45 min]

**Prompt**:
```
[Instructions]
[Success criteria]

Complete and pause. Confirm before proceeding.
```
```

### Quality Gates
- [ ] Code compiles
- [ ] Tests passing
- [ ] No StyleCop warnings
- [ ] XML documentation complete


## Iterative Testing Protocol

**When implementing features or fixing bugs:**

1. **Create temp tests** in `tests/temp/` (e.g., `TempFeatureValidationTests.cs`)
2. **Write challenging tests** with edge cases
3. **Implement solution** following code standards
4. **Run tests and iterate**:
   - If FAIL: Document in DEVLOG.md, modify code, repeat
   - If PASS: Proceed to cleanup
5. **Delete temp tests** after successful implementation
6. **Document process** in DEVLOG.md with iteration count

**Benefits**: Ensures solutions work, documents problem-solving, prevents premature success claims, maintains clean repository



## Iterative Testing Protocol

**When implementing features or fixing bugs:**

1. **Create temp tests** in `tests/temp/` (e.g., `TempFeatureValidationTests.cs`)
2. **Write challenging tests** with edge cases
3. **Implement solution** following code standards
4. **Run tests and iterate**:
   - If FAIL: Document in DEVLOG.md, modify code, repeat
   - If PASS: Proceed to cleanup
5. **Delete temp tests** after successful implementation
6. **Document process** in DEVLOG.md with iteration count

**Benefits**: Ensures solutions work, documents problem-solving, prevents premature success claims, maintains clean repository



# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Pattern:
```
Please run in your terminal:

1. Build solution:
   dotnet build

2. Run tests:
   dotnet test

3. Share any errors for assistance.
```

## .NET CLI Commands

```bash
# Solution management
dotnet new sln -n ProjectName
dotnet sln add src/**/*.csproj

# Build
dotnet build
dotnet build --configuration Release
dotnet clean

# Testing
dotnet test
dotnet test --verbosity detailed
dotnet test --filter "FullyQualifiedName~UserService"

# Run application
dotnet run --project src/ProjectName.API
dotnet watch run --project src/ProjectName.API

# Entity Framework
dotnet ef migrations add InitialCreate
dotnet ef database update
dotnet ef migrations remove

# Package management
dotnet add package Microsoft.EntityFrameworkCore
dotnet restore
dotnet list package --outdated

# Publishing
dotnet publish -c Release -o ./publish
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:
- Modify CHANGELOG.md versions
- Update .csproj Version property
- Change README.md versions
- Create tags/releases

### Version Protocol

1. **Assess**: "Changes might warrant version update from X.Y.Z"
2. **Request**: "Should I update to [version]? Or handle manually?"
3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, docs
- **Minor (Y+1.0)**: New features
- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**


# 9. Implementation Examples
---

## Code Fix Request

**Structure:**
1. Analyze issue
2. Implement fix
3. Explain improvements
4. Provide integration steps

## Project Planning

**Structure:**
1. Break down components
2. Recommend architecture
3. Create subtask breakdown
4. Provide implementation guidance


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] Compiles without errors
- [ ] Follows C# conventions
- [ ] XML documentation present
- [ ] Proper exception handling
- [ ] No StyleCop warnings
- [ ] Tests included
- [ ] Async/await properly used
- [ ] Nullable reference types handled
- [ ] Performance considered
- [ ] Security checked

## Before Delivering Project
- [ ] Standard ASP.NET Core structure
- [ ] Solution file configured
- [ ] EF migrations setup
- [ ] All config files present
- [ ] Dependency injection configured
- [ ] Documentation complete
- [ ] Tests passing

---
