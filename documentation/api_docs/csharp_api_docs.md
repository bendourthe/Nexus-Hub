# C# API Documentation

## Objective
Create complete, accurate API documentation for .NET/ASP.NET Core APIs that enables developers to quickly understand and successfully integrate, including authentication flows, request formats, response structures, and error handling.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/api_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/api_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Endpoint Documentation
- [ ] All endpoints documented with HTTP methods
- [ ] Request/response models with C# types
- [ ] Route parameters, query strings, body documented
- [ ] Status codes and meanings explained
- [ ] Content types specified

### Authentication
- [ ] Authentication methods documented (JWT/OAuth2/Azure AD)
- [ ] Authorization policies explained
- [ ] Token management documented
- [ ] Claims and roles documented

### Request/Response
- [ ] DTO models documented
- [ ] Data annotations explained
- [ ] Validation attributes shown
- [ ] Example JSON payloads provided

### Error Handling
- [ ] Exception handling documented
- [ ] ProblemDetails format shown
- [ ] HTTP status code mappings
- [ ] Common error scenarios covered

### Examples
- [ ] HttpClient examples
- [ ] RestSharp examples
- [ ] Refit interface examples
- [ ] Complete integration examples

### Best Practices
- [ ] Rate limiting documented
- [ ] Pagination patterns explained
- [ ] API versioning (Asp.Versioning)
- [ ] Performance considerations

## Prompt Template

~~~markdown
# C#/.NET API Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/api_docs"
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

Generate comprehensive API documentation following this protocol:

## Phase 1: OpenAPI with Swashbuckle

### ASP.NET Core API Definition

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "My API",
        Version = "v1",
        Description = "API description"
    });

    // JWT Authentication
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });

    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();
app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();
app.Run();
```

### Controller Implementation

```csharp
[ApiController]
[Route("api/v1/[controller]")]
[Produces("application/json")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;
    private readonly ILogger<UsersController> _logger;

    public UsersController(IUserService userService, ILogger<UsersController> logger)
    {
        _userService = userService;
        _logger = logger;
    }

    /// <summary>
    /// Get paginated list of users
    /// </summary>
    /// <param name="page">Page number (1-indexed)</param>
    /// <param name="pageSize">Number of items per page</param>
    /// <returns>Paginated list of users</returns>
    /// <response code="200">Returns the list of users</response>
    /// <response code="401">If the user is not authenticated</response>
    [HttpGet]
    [Authorize]
    [ProducesResponseType(typeof(PagedResult<UserResponse>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<PagedResult<UserResponse>>> GetUsers(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20)
    {
        var result = await _userService.GetUsersAsync(page, pageSize);
        return Ok(result);
    }

    /// <summary>
    /// Create a new user
    /// </summary>
    /// <param name="request">User creation request</param>
    /// <returns>Created user</returns>
    [HttpPost]
    [ProducesResponseType(typeof(UserResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserResponse>> CreateUser(
        [FromBody] CreateUserRequest request)
    {
        var user = await _userService.CreateUserAsync(request);
        return CreatedAtAction(nameof(GetUser), new { id = user.Id }, user);
    }

    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(UserResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    public async Task<ActionResult<UserResponse>> GetUser(int id)
    {
        var user = await _userService.GetUserByIdAsync(id);
        if (user == null)
        {
            return NotFound(new ProblemDetails
            {
                Title = "User not found",
                Detail = $"User with ID {id} was not found",
                Status = StatusCodes.Status404NotFound
            });
        }
        return Ok(user);
    }

    [HttpPut("{id:int}")]
    public async Task<IActionResult> UpdateUser(int id, [FromBody] UpdateUserRequest request)
    {
        await _userService.UpdateUserAsync(id, request);
        return NoContent();
    }

    [HttpDelete("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> DeleteUser(int id)
    {
        await _userService.DeleteUserAsync(id);
        return NoContent();
    }
}
```

### DTOs with Validation

```csharp
public record CreateUserRequest
{
    [Required(ErrorMessage = "Email is required")]
    [EmailAddress(ErrorMessage = "Invalid email format")]
    public string Email { get; init; } = string.Empty;

    [Required]
    [StringLength(100, MinimumLength = 1)]
    public string Name { get; init; } = string.Empty;

    [Required]
    [MinLength(8, ErrorMessage = "Password must be at least 8 characters")]
    public string Password { get; init; } = string.Empty;
}

public record UserResponse
{
    public int Id { get; init; }
    public string Email { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public DateTime CreatedAt { get; init; }
}

public record PagedResult<T>
{
    public List<T> Items { get; init; } = new();
    public int Page { get; init; }
    public int PageSize { get; init; }
    public int TotalCount { get; init; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}
```

## Phase 2: C# Client Examples

### HttpClient with Typed Client

```csharp
public interface IUserApiClient
{
    Task<PagedResult<UserResponse>> GetUsersAsync(int page = 1, int pageSize = 20);
    Task<UserResponse> CreateUserAsync(CreateUserRequest request);
    Task<UserResponse?> GetUserAsync(int id);
}

public class UserApiClient : IUserApiClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<UserApiClient> _logger;

    public UserApiClient(HttpClient httpClient, ILogger<UserApiClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<PagedResult<UserResponse>> GetUsersAsync(int page = 1, int pageSize = 20)
    {
        var response = await _httpClient.GetAsync($"/api/v1/users?page={page}&pageSize={pageSize}");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<PagedResult<UserResponse>>()
            ?? throw new InvalidOperationException("Response was null");
    }

    public async Task<UserResponse> CreateUserAsync(CreateUserRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync("/api/v1/users", request);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<UserResponse>()
            ?? throw new InvalidOperationException("Response was null");
    }

    public async Task<UserResponse?> GetUserAsync(int id)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/api/v1/users/{id}");
            if (response.StatusCode == HttpStatusCode.NotFound)
            {
                return null;
            }
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<UserResponse>();
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to get user {UserId}", id);
            throw;
        }
    }
}

// Registration in Program.cs
builder.Services.AddHttpClient<IUserApiClient, UserApiClient>(client =>
{
    client.BaseAddress = new Uri("https://api.example.com");
    client.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
    client.Timeout = TimeSpan.FromSeconds(30);
})
.AddPolicyHandler(GetRetryPolicy())
.AddPolicyHandler(GetCircuitBreakerPolicy());

static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
{
    return HttpPolicyExtensions
        .HandleTransientHttpError()
        .WaitAndRetryAsync(3, retryAttempt =>
            TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
}

static IAsyncPolicy<HttpResponseMessage> GetCircuitBreakerPolicy()
{
    return HttpPolicyExtensions
        .HandleTransientHttpError()
        .CircuitBreakerAsync(5, TimeSpan.FromSeconds(30));
}
```

### RestSharp Client

```csharp
public class RestSharpUserClient
{
    private readonly RestClient _client;

    public RestSharpUserClient(string baseUrl, string apiKey)
    {
        var options = new RestClientOptions(baseUrl)
        {
            Timeout = TimeSpan.FromSeconds(30)
        };
        _client = new RestClient(options);
        _client.AddDefaultHeader("Authorization", $"Bearer {apiKey}");
    }

    public async Task<PagedResult<UserResponse>?> GetUsersAsync(int page = 1, int pageSize = 20)
    {
        var request = new RestRequest("/api/v1/users")
            .AddQueryParameter("page", page)
            .AddQueryParameter("pageSize", pageSize);

        var response = await _client.ExecuteGetAsync<PagedResult<UserResponse>>(request);

        if (!response.IsSuccessful)
        {
            throw new HttpRequestException(
                $"Request failed with status {response.StatusCode}: {response.ErrorMessage}");
        }

        return response.Data;
    }

    public async Task<UserResponse?> CreateUserAsync(CreateUserRequest request)
    {
        var restRequest = new RestRequest("/api/v1/users", Method.Post)
            .AddJsonBody(request);

        var response = await _client.ExecutePostAsync<UserResponse>(restRequest);

        if (!response.IsSuccessful)
        {
            if (response.StatusCode == HttpStatusCode.BadRequest)
            {
                var error = JsonSerializer.Deserialize<ValidationProblemDetails>(
                    response.Content ?? "{}");
                throw new ValidationException($"Validation failed: {error}");
            }
            throw new HttpRequestException(
                $"Request failed: {response.StatusCode}");
        }

        return response.Data;
    }
}
```

### Refit Interface

```csharp
public interface IUserApi
{
    [Get("/api/v1/users")]
    Task<PagedResult<UserResponse>> GetUsers(
        [Query] int page = 1,
        [Query] int pageSize = 20);

    [Post("/api/v1/users")]
    Task<UserResponse> CreateUser([Body] CreateUserRequest request);

    [Get("/api/v1/users/{id}")]
    Task<UserResponse> GetUser(int id);

    [Put("/api/v1/users/{id}")]
    Task UpdateUser(int id, [Body] UpdateUserRequest request);

    [Delete("/api/v1/users/{id}")]
    Task DeleteUser(int id);
}

// Registration
builder.Services.AddRefitClient<IUserApi>()
    .ConfigureHttpClient(c =>
    {
        c.BaseAddress = new Uri("https://api.example.com");
        c.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
    })
    .AddPolicyHandler(GetRetryPolicy());

// Usage
public class UserService
{
    private readonly IUserApi _userApi;

    public UserService(IUserApi userApi)
    {
        _userApi = userApi;
    }

    public async Task<List<UserResponse>> GetAllUsersAsync()
    {
        try
        {
            var result = await _userApi.GetUsers(1, 100);
            return result.Items;
        }
        catch (ApiException ex) when (ex.StatusCode == HttpStatusCode.Unauthorized)
        {
            throw new UnauthorizedAccessException("Invalid API key");
        }
    }
}
```

## Phase 3: Authentication

```csharp
// JWT Authentication setup
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
        policy.RequireClaim("permission", "users.write"));
});
```

## Phase 4: Error Handling

```csharp
// Global exception handler middleware
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(
        RequestDelegate next,
        ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An unhandled exception occurred");
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var problemDetails = exception switch
        {
            ValidationException validationEx => new ValidationProblemDetails
            {
                Status = StatusCodes.Status400BadRequest,
                Title = "Validation error",
                Detail = validationEx.Message
            },
            NotFoundException notFoundEx => new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Resource not found",
                Detail = notFoundEx.Message
            },
            _ => new ProblemDetails
            {
                Status = StatusCodes.Status500InternalServerError,
                Title = "An error occurred",
                Detail = "An unexpected error occurred"
            }
        };

        context.Response.ContentType = "application/problem+json";
        context.Response.StatusCode = problemDetails.Status ?? 500;

        return context.Response.WriteAsJsonAsync(problemDetails);
    }
}

// Register middleware
app.UseMiddleware<ExceptionHandlingMiddleware>();
```

## Phase 5: Testing

```csharp
public class UsersControllerTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UsersControllerTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CreateUser_ValidRequest_ReturnsCreated()
    {
        // Arrange
        var request = new CreateUserRequest
        {
            Email = "test@example.com",
            Name = "Test User",
            Password = "password123"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/v1/users", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var user = await response.Content.ReadFromJsonAsync<UserResponse>();
        user.Should().NotBeNull();
        user!.Email.Should().Be(request.Email);
    }
}
```
```

---

## Best Practices

1. **Use ASP.NET Core Minimal APIs or Controllers**: Choose based on complexity
2. **Validation**: Use Data Annotations + FluentValidation
3. **DTOs**: Use records for immutability
4. **Exception Handling**: Use middleware for global handling
5. **Pagination**: Return PagedResult<T> consistently
6. **Documentation**: Use XML comments + Swashbuckle
7. **Testing**: Use WebApplicationFactory for integration tests
8. **Security**: Implement JWT/OAuth2 with ASP.NET Core Identity

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/api_docs/generated_docs
mkdir -p ${OUTPUT_DIR}/api_docs/templates
mkdir -p ${OUTPUT_DIR}/api_docs/assets
mkdir -p ${OUTPUT_DIR}/api_docs/exports
```

**Save files as follows**:


- Templates → `documentation/api_docs/templates/`

- Assets → `documentation/api_docs/assets/`

- Exports → `documentation/api_docs/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The API documentation should:
- Follow OpenAPI 3.0 standards
- Include ASP.NET Core-specific patterns
- Provide multiple .NET client examples
- Document validation and error handling
- Show authentication/authorization setup
- Include testing examples
- Target .NET/C# developers
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
