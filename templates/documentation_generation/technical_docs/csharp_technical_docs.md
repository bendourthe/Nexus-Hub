---
template_id: csharp_technical_docs
template_name: Technical Docs - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: documentation
phase: technical_docs
difficulty: beginner
estimated_time_hours: 4-6
prerequisites: []
tools:

  - NUnit (4.2.2)
  - xUnit
  - MSTest
tags:

  - documentation
  - documentation
  - c#
---
# C# Technical Documentation

## Objective
Create comprehensive technical documentation that captures architecture decisions, system design, data flows, integration points, and development workflows for developers and technical stakeholders.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/technical_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/technical_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Architecture Documentation

- [ ] System architecture overview with diagrams

- [ ] Component responsibilities clearly defined

- [ ] Technology stack documented with rationale

- [ ] Architectural patterns explained

- [ ] Scalability and performance considerations

- [ ] Security architecture documented

### Design Decisions

- [ ] Key technical decisions documented with rationale

- [ ] Alternative approaches considered

- [ ] Trade-offs and constraints explained

- [ ] Decision timeline and context

- [ ] Impact assessment of decisions

### Module Organization

- [ ] Project/namespace structure explained

- [ ] Module dependencies mapped

- [ ] Public vs internal vs private interfaces defined

- [ ] Using directives documented

- [ ] Code organization principles

### Data Flow

- [ ] Data flow diagrams created

- [ ] State management documented

- [ ] Event flows explained

- [ ] Data transformation pipelines

- [ ] Error propagation paths

### Integration Points

- [ ] External API integrations documented

- [ ] Database schemas and migrations

- [ ] Message queue/event systems

- [ ] Third-party service dependencies

- [ ] Authentication/authorization flows

### Development Workflow

- [ ] Development environment setup

- [ ] Build and deployment process

- [ ] Testing strategy

- [ ] CI/CD pipeline documentation

- [ ] Release process

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Technical Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/technical_docs"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please create comprehensive technical documentation for this C#/.NET project following this protocol:

## Phase 1: Architecture Analysis

1. **System Architecture Overview**

   ```markdown
   # System Architecture

   ## Overview

   [Project Name] is built as a [monolith/microservice/library/framework] using .NET [version] that [high-level purpose].

   ## Architecture Style

   - **Pattern**: [Clean Architecture/Layered/CQRS/Vertical Slice/etc.]
   - **Framework**: [ASP.NET Core/Minimal APIs/.NET MAUI/WPF/etc.]
   - **Deployment**: [IIS/Kestrel/Azure App Service/Docker/Kubernetes]
   - **State Management**: [Stateless/stateful/hybrid]
   - **Communication**: [REST/gRPC/SignalR/Message Bus]

   ## Technology Stack

   | Layer | Technology | Version | Rationale |
   |-------|-----------|---------|-----------|
   | Runtime | .NET | 8.0 | LTS, performance, modern C# features |
   | Framework | ASP.NET Core | 8.0 | Cross-platform, high performance |
   | Database | SQL Server/PostgreSQL | Latest | Enterprise-grade, robust |
   | ORM | Entity Framework Core | 8.0 | LINQ support, migrations |
   | Testing | xUnit/NUnit | Latest | Industry standard |
   | API Docs | Swashbuckle | Latest | OpenAPI/Swagger generation |
   | DI Container | Built-in | - | Microsoft.Extensions.DependencyInjection |

   ## Security Architecture

   - **Authentication**: [JWT/OAuth2/Azure AD/IdentityServer]
   - **Authorization**: [Policy-based/Claims-based/Role-based]
   - **Data Protection**: [Data Protection API/Azure Key Vault]
   - **Secrets Management**: [User Secrets/Azure Key Vault/AWS Secrets Manager]
   ```

## Phase 2: Module Organization

```markdown
# Project Structure

## Solution Structure

```
Solution.sln
├── src/
│   ├── MyApp.Api/                  # Web API project
│   │   ├── Controllers/            # API controllers
│   │   │   ├── UsersController.cs
│   │   │   └── ProductsController.cs
│   │   ├── Middleware/             # Custom middleware
│   │   │   ├── ExceptionHandlingMiddleware.cs
│   │   │   └── LoggingMiddleware.cs
│   │   ├── Filters/                # Action filters
│   │   │   └── ValidationFilter.cs
│   │   ├── Program.cs              # Application entry point
│   │   └── appsettings.json        # Configuration
│   │
│   ├── MyApp.Application/          # Application layer
│   │   ├── Services/               # Application services
│   │   │   ├── UserService.cs
│   │   │   └── ProductService.cs
│   │   ├── DTOs/                   # Data Transfer Objects
│   │   │   ├── UserDto.cs
│   │   │   ├── CreateUserRequest.cs
│   │   │   └── UserResponse.cs
│   │   ├── Interfaces/             # Service interfaces
│   │   │   └── IUserService.cs
│   │   ├── Validators/             # FluentValidation validators
│   │   │   └── CreateUserRequestValidator.cs
│   │   └── Mapping/                # AutoMapper profiles
│   │       └── UserProfile.cs
│   │
│   ├── MyApp.Domain/               # Domain layer
│   │   ├── Entities/               # Domain entities
│   │   │   ├── User.cs
│   │   │   ├── Product.cs
│   │   │   └── BaseEntity.cs
│   │   ├── ValueObjects/           # Value objects
│   │   │   ├── Email.cs
│   │   │   └── Money.cs
│   │   ├── Interfaces/             # Repository interfaces
│   │   │   └── IUserRepository.cs
│   │   ├── Specifications/         # Specification pattern
│   │   │   └── ActiveUsersSpec.cs
│   │   └── Exceptions/             # Domain exceptions
│   │       └── UserNotFoundException.cs
│   │
│   ├── MyApp.Infrastructure/       # Infrastructure layer
│   │   ├── Data/                   # Data access
│   │   │   ├── ApplicationDbContext.cs
│   │   │   ├── Repositories/       # Repository implementations
│   │   │   │   └── UserRepository.cs
│   │   │   ├── Configurations/     # EF Core configurations
│   │   │   │   └── UserConfiguration.cs
│   │   │   └── Migrations/         # EF migrations
│   │   ├── Services/               # Infrastructure services
│   │   │   ├── EmailService.cs
│   │   │   └── CacheService.cs
│   │   └── ExternalApis/           # External API clients
│   │       └── ExternalApiClient.cs
│   │
│   └── MyApp.Shared/               # Shared/cross-cutting
│       ├── Constants/
│       ├── Utilities/
│       └── Extensions/
│
└── tests/
    ├── MyApp.UnitTests/            # Unit tests
    ├── MyApp.IntegrationTests/     # Integration tests
    └── MyApp.FunctionalTests/      # End-to-end tests
```

## Layer Responsibilities

### API Layer (`MyApp.Api`)

- **Purpose**: HTTP/gRPC endpoints

- **Responsibilities**:
  - Route mapping
  - Request/response handling
  - Authentication/authorization
  - Input validation

- **Dependencies**: Application layer

- **Attributes**: `[ApiController]`, `[Route]`, `[HttpGet]`, `[Authorize]`

### Application Layer (`MyApp.Application`)

- **Purpose**: Business logic orchestration

- **Responsibilities**:
  - Use case implementation
  - DTO mapping
  - Validation (FluentValidation)
  - Transaction coordination

- **Dependencies**: Domain layer

- **Patterns**: CQRS, MediatR

### Domain Layer (`MyApp.Domain`)

- **Purpose**: Core business logic

- **Responsibilities**:
  - Entity definitions
  - Business rules
  - Domain events
  - Repository interfaces

- **Dependencies**: None (pure domain)

### Infrastructure Layer (`MyApp.Infrastructure`)

- **Purpose**: External concerns

- **Responsibilities**:
  - Database access (EF Core)
  - External API integration
  - File storage
  - Caching

- **Dependencies**: Domain layer

## Dependency Injection

```csharp
// Program.cs (Minimal API)
var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

// Register application services
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IUserRepository, UserRepository>();

// Add AutoMapper
builder.Services.AddAutoMapper(typeof(UserProfile));

// Add FluentValidation
builder.Services.AddValidatorsFromAssemblyContaining<CreateUserRequestValidator>();

var app = builder.Build();

// Configure middleware pipeline
app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
```
```

## Phase 3: Data Flow Documentation

```markdown
# Data Flow Example: User Creation

```csharp
// 1. API Controller
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;

    public UsersController(IUserService userService)
    {
        _userService = userService;
    }

    [HttpPost]
    public async Task<ActionResult<UserResponse>> CreateUser(
        [FromBody] CreateUserRequest request)
    {
        var result = await _userService.CreateUserAsync(request);
        return CreatedAtAction(nameof(GetUser), new { id = result.Id }, result);
    }
}

// 2. Application Service
public class UserService : IUserService
{
    private readonly IUserRepository _userRepository;
    private readonly IMapper _mapper;
    private readonly IValidator<CreateUserRequest> _validator;

    public UserService(
        IUserRepository userRepository,
        IMapper mapper,
        IValidator<CreateUserRequest> validator)
    {
        _userRepository = userRepository;
        _mapper = mapper;
        _validator = validator;
    }

    public async Task<UserResponse> CreateUserAsync(CreateUserRequest request)
    {
        // Validate
        var validationResult = await _validator.ValidateAsync(request);
        if (!validationResult.IsValid)
        {
            throw new ValidationException(validationResult.Errors);
        }

        // Check uniqueness
        if (await _userRepository.ExistsByEmailAsync(request.Email))
        {
            throw new DuplicateEmailException("Email already exists");
        }

        // Map to entity
        var user = _mapper.Map<User>(request);
        user.PasswordHash = HashPassword(request.Password);

        // Persist
        var createdUser = await _userRepository.AddAsync(user);
        await _userRepository.SaveChangesAsync();

        // Map to response
        return _mapper.Map<UserResponse>(createdUser);
    }
}

// 3. Repository
public class UserRepository : IUserRepository
{
    private readonly ApplicationDbContext _context;

    public UserRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<User> AddAsync(User user)
    {
        await _context.Users.AddAsync(user);
        return user;
    }

    public async Task<bool> ExistsByEmailAsync(string email)
    {
        return await _context.Users.AnyAsync(u => u.Email == email);
    }

    public async Task<int> SaveChangesAsync()
    {
        return await _context.SaveChangesAsync();
    }
}

// 4. Domain Entity
public class User : BaseEntity
{
    public string Email { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

// 5. EF Core Configuration
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("Users");

        builder.HasKey(u => u.Id);

        builder.Property(u => u.Email)
            .IsRequired()
            .HasMaxLength(255);

        builder.HasIndex(u => u.Email).IsUnique();

        builder.Property(u => u.Name)
            .IsRequired()
            .HasMaxLength(100);
    }
}
```
```

## Phase 4: Integration Points

```markdown
# Integration Points

## Database Configuration

```csharp
// ApplicationDbContext
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();
    public DbSet<Product> Products => Set<Product>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}

// appsettings.json
{
  "ConnectionStrings": {
    "Default": "Server=localhost;Database=MyAppDb;User Id=sa;Password=YourPassword;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
```

## External API Client

```csharp
public interface IExternalApiClient
{
    Task<ApiResponse> GetResourceAsync(string resourceId);
}

public class ExternalApiClient : IExternalApiClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<ExternalApiClient> _logger;

    public ExternalApiClient(HttpClient httpClient, ILogger<ExternalApiClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<ApiResponse> GetResourceAsync(string resourceId)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/resource/{resourceId}");
            response.EnsureSuccessStatusCode();

            return await response.Content.ReadFromJsonAsync<ApiResponse>()
                ?? throw new InvalidOperationException("Response was null");
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to fetch resource {ResourceId}", resourceId);
            throw new ExternalApiException($"Failed to fetch resource: {ex.Message}", ex);
        }
    }
}

// Registration in Program.cs
builder.Services.AddHttpClient<IExternalApiClient, ExternalApiClient>(client =>
{
    client.BaseAddress = new Uri(builder.Configuration["ExternalApi:BaseUrl"]!);
    client.DefaultRequestHeaders.Add("Authorization",
        $"Bearer {builder.Configuration["ExternalApi:ApiKey"]}");
    client.Timeout = TimeSpan.FromSeconds(30);
});
```

## Authentication & Authorization

```csharp
// JWT Configuration
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };
    });

// Policy-based authorization
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));

    options.AddPolicy("CanEditUsers", policy =>
        policy.RequireClaim("permission", "users.edit"));
});

// Controller usage
[Authorize(Policy = "AdminOnly")]
[HttpDelete("{id}")]
public async Task<IActionResult> DeleteUser(int id)
{
    await _userService.DeleteUserAsync(id);
    return NoContent();
}
```
```

## Phase 5: Development Workflow

```markdown
# Development Workflow

## Prerequisites

- .NET 8.0 SDK

- Visual Studio 2022 / VS Code / Rider

- SQL Server / PostgreSQL

- Docker (optional)

## Local Setup

```bash
# Clone repository
git clone https://github.com/org/project.git
cd project

# Restore packages
dotnet restore

# Update database
dotnet ef database update --project src/MyApp.Infrastructure

# Run application
dotnet run --project src/MyApp.Api

# Run tests
dotnet test
```

## Testing Strategy

```csharp
// Unit Test (xUnit + Moq)
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _userRepositoryMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _userRepositoryMock = new Mock<IUserRepository>();
        _mapperMock = new Mock<IMapper>();
        _sut = new UserService(_userRepositoryMock.Object, _mapperMock.Object);
    }

    [Fact]
    public async Task CreateUserAsync_ValidRequest_ReturnsUserResponse()
    {
        // Arrange
        var request = new CreateUserRequest { Email = "test@example.com" };
        _userRepositoryMock.Setup(x => x.ExistsByEmailAsync(It.IsAny<string>()))
            .ReturnsAsync(false);

        // Act
        var result = await _sut.CreateUserAsync(request);

        // Assert
        Assert.NotNull(result);
        _userRepositoryMock.Verify(x => x.AddAsync(It.IsAny<User>()), Times.Once);
    }
}

// Integration Test
public class UsersControllerIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UsersControllerIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CreateUser_ReturnsCreated()
    {
        // Arrange
        var request = new CreateUserRequest
        {
            Email = "test@example.com",
            Name = "Test User"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/users", request);

        // Assert
        response.EnsureSuccessStatusCode();
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
    }
}
```

## CI/CD Pipeline

```yaml
# GitHub Actions
name: .NET CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0.x'

      - name: Restore dependencies
        run: dotnet restore

      - name: Build
        run: dotnet build --no-restore

      - name: Test
        run: dotnet test --no-build --verbosity normal

      - name: Publish
        run: dotnet publish -c Release -o publish
```
```

---

## Best Practices

1. **Follow C# Coding Conventions**
   - PascalCase for classes, methods, properties
   - camelCase for parameters, local variables
   - Prefix interfaces with `I`
   - Use `async`/`await` for I/O operations

2. **Use Modern C# Features**
   - Record types for DTOs
   - Pattern matching
   - Null-coalescing operators
   - File-scoped namespaces

3. **Apply Clean Architecture**
   - Domain at center, no dependencies
   - Application layer orchestrates
   - Infrastructure implements interfaces
   - API layer is thin

4. **Comprehensive Testing**
   - Unit tests with xUnit/NUnit + Moq
   - Integration tests with WebApplicationFactory
   - Use FluentAssertions for readable assertions

5. **Performance Considerations**
   - Use `ValueTask` for hot paths
   - Configure EF Core query splitting
   - Implement caching strategically
   - Profile with BenchmarkDotNet

---

## Output Format Specifications

The technical documentation should:

- Provide high-level architecture overview with diagrams

- Document design decisions with rationale and alternatives

- Map module organization and dependencies clearly

- Illustrate data flows through the system

- Document all external integrations comprehensively

- Follow .NET and C# best practices

- Target technical audience (developers, architects)

~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
