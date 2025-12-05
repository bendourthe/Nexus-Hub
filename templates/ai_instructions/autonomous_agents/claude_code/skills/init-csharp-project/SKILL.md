---
name: init-csharp-project
description: Initialize complete C# project with .NET 8+, ASP.NET Core Web API, Entity Framework Core, and production-ready configuration
version: 1.0.0
author: Benjamin Dourthe
language: C#
category: Project Initialization
tags: [csharp, dotnet, aspnet-core, entity-framework, initialization, setup, project-structure]
priority: MEDIUM
template_source: agent_prompts/autonomous_agents/claude_code/csharp/
---

# Initialize C# Project

Create a complete, production-ready C# project with .NET 8+, ASP.NET Core Web API, Entity Framework Core, comprehensive testing framework, and documentation in minutes. Supports REST APIs, microservices, and Clean Architecture patterns.

## When to Use This Skill

Use this skill when you need to:

- ✅ Start a new C#/.NET project from scratch

- ✅ Set up ASP.NET Core Web API

- ✅ Initialize Entity Framework Core with migrations

- ✅ Establish Clean Architecture structure

- ✅ Configure testing framework (xUnit, NUnit, or MSTest)

- ✅ Set up authentication and authorization

- ✅ Create Docker configuration

- ✅ Initialize OpenAPI/Swagger documentation

- ✅ Set up CI/CD with GitHub Actions

## What This Skill Does

Creates a complete C# project structure following industry best practices:

### 1. Directory Structure

#### Web API (Standard Layout)
```
ProjectName/
├── src/
│   ├── ProjectName.Api/
│   │   ├── Controllers/
│   │   │   ├── v1/
│   │   │   │   └── TasksController.cs
│   │   │   └── HealthController.cs
│   │   ├── Middleware/
│   │   │   ├── ExceptionHandlingMiddleware.cs
│   │   │   └── RequestLoggingMiddleware.cs
│   │   ├── Filters/
│   │   ├── Extensions/
│   │   ├── Program.cs
│   │   ├── appsettings.json
│   │   ├── appsettings.Development.json
│   │   ├── appsettings.Production.json
│   │   └── ProjectName.Api.csproj
│   ├── ProjectName.Core/
│   │   ├── Entities/
│   │   ├── Interfaces/
│   │   ├── DTOs/
│   │   ├── Exceptions/
│   │   ├── Validators/
│   │   └── ProjectName.Core.csproj
│   ├── ProjectName.Application/
│   │   ├── Services/
│   │   ├── Mappings/
│   │   ├── Behaviors/
│   │   └── ProjectName.Application.csproj
│   └── ProjectName.Infrastructure/
│       ├── Data/
│       │   ├── ApplicationDbContext.cs
│       │   ├── Configurations/
│       │   └── Migrations/
│       ├── Repositories/
│       ├── Services/
│       └── ProjectName.Infrastructure.csproj
├── tests/
│   ├── ProjectName.UnitTests/
│   │   ├── Controllers/
│   │   ├── Services/
│   │   ├── Validators/
│   │   └── ProjectName.UnitTests.csproj
│   └── ProjectName.IntegrationTests/
│       ├── Api/
│       ├── Fixtures/
│       └── ProjectName.IntegrationTests.csproj
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── ProjectName.sln
├── global.json
├── Directory.Build.props
├── CHANGELOG.md
├── DEVLOG.md
├── README.md
└── CLAUDE.md
```

#### Clean Architecture (Advanced)
```
ProjectName/
├── src/
│   ├── ProjectName.API/                 # Presentation Layer
│   │   ├── Controllers/
│   │   ├── Middleware/
│   │   ├── Filters/
│   │   ├── Program.cs
│   │   └── ProjectName.API.csproj
│   ├── ProjectName.Domain/              # Domain Layer
│   │   ├── Entities/
│   │   ├── ValueObjects/
│   │   ├── Events/
│   │   ├── Exceptions/
│   │   └── ProjectName.Domain.csproj
│   ├── ProjectName.Application/         # Application Layer
│   │   ├── Common/
│   │   │   ├── Interfaces/
│   │   │   ├── Behaviors/
│   │   │   └── Mappings/
│   │   ├── Features/
│   │   │   └── Tasks/
│   │   │       ├── Commands/
│   │   │       │   ├── CreateTask/
│   │   │       │   └── UpdateTask/
│   │   │       └── Queries/
│   │   │           ├── GetTasks/
│   │   │           └── GetTaskById/
│   │   └── ProjectName.Application.csproj
│   └── ProjectName.Infrastructure/      # Infrastructure Layer
│       ├── Persistence/
│       │   ├── ApplicationDbContext.cs
│       │   ├── Configurations/
│       │   └── Migrations/
│       ├── Repositories/
│       ├── Services/
│       └── ProjectName.Infrastructure.csproj
├── tests/
│   ├── ProjectName.Domain.Tests/
│   ├── ProjectName.Application.Tests/
│   ├── ProjectName.Infrastructure.Tests/
│   └── ProjectName.API.Tests/
├── docker/
├── .github/
├── ProjectName.sln
└── [documentation files]
```

### 2. Configuration Files
- **ProjectName.sln**: Solution file with all projects

- **global.json**: .NET SDK version specification

- **Directory.Build.props**: Shared build properties

- **appsettings.json**: Application configuration with environments

- **.editorconfig**: Code style enforcement

- **.gitignore**: Comprehensive .NET ignore patterns

- **Dockerfile**: Container configuration

- **docker-compose.yml**: Multi-container setup

### 3. Documentation
- **README.md**: Installation, usage, and feature documentation

- **CHANGELOG.md**: Version history following Keep a Changelog format

- **DEVLOG.md**: Development task list and decision log

- **CLAUDE.md**: Claude Code project guidelines

- **Swagger UI**: Interactive API documentation

### 4. Testing Framework
- xUnit / NUnit / MSTest for unit testing

- Moq or NSubstitute for mocking

- FluentAssertions for readable assertions

- WebApplicationFactory for integration tests

- Coverlet for code coverage

- TestContainers for database testing

### 5. Development Tools
- Entity Framework Core for data access

- AutoMapper for object mapping

- FluentValidation for input validation

- MediatR for CQRS pattern (Clean Architecture)

- Serilog for structured logging

- Swagger/OpenAPI for API documentation

## Prerequisites

- .NET 8 SDK or later

- Visual Studio 2022+ / Rider / VS Code with C# extension

- Docker (optional, for containerization)

- SQL Server / PostgreSQL / SQLite (database)

- git (version control)

- (Optional) Claude Code for AI assistance

## Instructions

### Step 1: Define Project Requirements

Gather this information before initialization:

**Project Details**:

- **Name**: Project identifier (PascalCase)

- **Description**: One-line summary of purpose

- **Type**: Web API / Microservice / Clean Architecture

- **Architecture**: Standard / Clean Architecture / Vertical Slice

- **Database**: SQL Server / PostgreSQL / SQLite

**Dependencies**:

- Core dependencies (e.g., EF Core, AutoMapper)

- Authentication requirements

- External services (Redis, RabbitMQ, etc.)

**Features**:

- Key capabilities to document

- Initial version number (default: 0.1.0)

### Step 2: Invoke the Skill

#### Example: ASP.NET Core Web API
```
"Use the init-csharp-project skill to create a new ASP.NET Core Web API project.

Project Details:

- Name: TaskManagement

- Description: RESTful API for task management with ASP.NET Core

- Type: Web API

- Architecture: Standard

- Database: PostgreSQL

- .NET Version: 8.0

Dependencies:

- Entity Framework Core (database access)

- AutoMapper (object mapping)

- FluentValidation (input validation)

- Serilog (logging)

- Swagger/OpenAPI (documentation)

Features:

- User authentication with JWT

- Task CRUD operations

- Task categorization

- RESTful API design

- Health checks and monitoring

Please initialize the complete project structure with all configurations."
```

#### Example: Clean Architecture Project
```
"Use the init-csharp-project skill to create a new Clean Architecture project.

Project Details:

- Name: TaskManagement

- Description: Task management system with Clean Architecture

- Type: Web API

- Architecture: Clean Architecture with CQRS

- Database: SQL Server

- .NET Version: 8.0

Dependencies:

- Entity Framework Core

- MediatR (CQRS pattern)

- AutoMapper

- FluentValidation

- Serilog

- Swagger/OpenAPI

Features:

- CQRS with MediatR

- Domain-driven design

- Repository pattern

- Unit of Work pattern

- Comprehensive validation

Please initialize the complete Clean Architecture structure."
```

### Step 3: Review Generated Structure

The skill will create all files and directories. Verify:

```bash
# Check structure
tree TaskManagement/

# Navigate to project
cd TaskManagement

# Verify solution file
dotnet sln list
```

### Step 4: Build the Solution

```bash
# Restore dependencies
dotnet restore

# Build solution
dotnet build

# Build in Release mode
dotnet build -c Release

# Clean and rebuild
dotnet clean && dotnet build
```

### Step 5: Set Up Database

#### Update appsettings.Development.json
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Database=taskmanagement;Username=postgres;Password=password"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Debug",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "Jwt": {
    "SecretKey": "your-secret-key-at-least-32-characters-long",
    "Issuer": "TaskManagement.Api",
    "Audience": "TaskManagement.Api",
    "ExpirationMinutes": 60
  }
}
```

#### Create and Apply Migrations
```bash
# Add migration
dotnet ef migrations add InitialCreate --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api

# Update database
dotnet ef database update --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api

# View migrations
dotnet ef migrations list --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api
```

### Step 6: Run the Application

#### Development Mode
```bash
# Run API project
cd src/TaskManagement.Api
dotnet run

# Run with watch (hot reload)
dotnet watch run

# Run with specific environment
dotnet run --environment Production
```

#### Using Docker
```bash
# Build Docker image
docker build -t taskmanagement-api:latest -f docker/Dockerfile .

# Run with docker-compose
cd docker
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Step 7: Verify Setup

```bash
# Check application health
curl http://localhost:5000/health

# Access Swagger UI
# Open browser: http://localhost:5000/swagger

# Run all tests
dotnet test

# Run tests with coverage
dotnet test /p:CollectCoverage=true /p:CoverageReportFormat=opencover

# Generate coverage report
dotnet tool install -g dotnet-reportgenerator-globaltool
reportgenerator -reports:**/coverage.opencover.xml -targetdir:coverage-report
```

### Step 8: Initialize Git Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial project structure

- ASP.NET Core Web API setup

- Entity Framework Core configured

- Testing framework included

- Docker configuration added

- OpenAPI documentation setup

Generated with init-csharp-project skill"

# (Optional) Add remote and push
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 9: Start Development

Your project is now ready! Begin developing:

```bash
# Run in development mode
dotnet watch run --project src/TaskManagement.Api

# Run tests continuously
dotnet watch test --project tests/TaskManagement.UnitTests

# Format code
dotnet format

# Build for production
dotnet publish -c Release -o ./publish
```

## Generated File Contents

### TaskManagement.sln
```
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1

Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "src", "src", "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"
EndProject

Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "tests", "tests", "{B1C2D3E4-F5A6-7890-BCDE-FA1234567890}"
EndProject

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "TaskManagement.Api", "src\TaskManagement.Api\TaskManagement.Api.csproj", "{C1D2E3F4-A5B6-7890-CDEF-AB1234567890}"
EndProject

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "TaskManagement.Core", "src\TaskManagement.Core\TaskManagement.Core.csproj", "{D1E2F3A4-B5C6-7890-DEFA-BC1234567890}"
EndProject

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "TaskManagement.Application", "src\TaskManagement.Application\TaskManagement.Application.csproj", "{E1F2A3B4-C5D6-7890-EFAB-CD1234567890}"
EndProject

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "TaskManagement.Infrastructure", "src\TaskManagement.Infrastructure\TaskManagement.Infrastructure.csproj", "{F1A2B3C4-D5E6-7890-FABC-DE1234567890}"
EndProject

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "TaskManagement.UnitTests", "tests\TaskManagement.UnitTests\TaskManagement.UnitTests.csproj", "{A2B3C4D5-E6F1-7890-ABCD-EF1234567891}"
EndProject

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "TaskManagement.IntegrationTests", "tests\TaskManagement.IntegrationTests\TaskManagement.IntegrationTests.csproj", "{B2C3D4E5-F6A1-7890-BCDE-FA1234567891}"
EndProject

Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{C1D2E3F4-A5B6-7890-CDEF-AB1234567890}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{C1D2E3F4-A5B6-7890-CDEF-AB1234567890}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{C1D2E3F4-A5B6-7890-CDEF-AB1234567890}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{C1D2E3F4-A5B6-7890-CDEF-AB1234567890}.Release|Any CPU.Build.0 = Release|Any CPU
		{D1E2F3A4-B5C6-7890-DEFA-BC1234567890}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{D1E2F3A4-B5C6-7890-DEFA-BC1234567890}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{D1E2F3A4-B5C6-7890-DEFA-BC1234567890}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{D1E2F3A4-B5C6-7890-DEFA-BC1234567890}.Release|Any CPU.Build.0 = Release|Any CPU
		{E1F2A3B4-C5D6-7890-EFAB-CD1234567890}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{E1F2A3B4-C5D6-7890-EFAB-CD1234567890}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{E1F2A3B4-C5D6-7890-EFAB-CD1234567890}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{E1F2A3B4-C5D6-7890-EFAB-CD1234567890}.Release|Any CPU.Build.0 = Release|Any CPU
		{F1A2B3C4-D5E6-7890-FABC-DE1234567890}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{F1A2B3C4-D5E6-7890-FABC-DE1234567890}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{F1A2B3C4-D5E6-7890-FABC-DE1234567890}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{F1A2B3C4-D5E6-7890-FABC-DE1234567890}.Release|Any CPU.Build.0 = Release|Any CPU
		{A2B3C4D5-E6F1-7890-ABCD-EF1234567891}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{A2B3C4D5-E6F1-7890-ABCD-EF1234567891}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{A2B3C4D5-E6F1-7890-ABCD-EF1234567891}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{A2B3C4D5-E6F1-7890-ABCD-EF1234567891}.Release|Any CPU.Build.0 = Release|Any CPU
		{B2C3D4E5-F6A1-7890-BCDE-FA1234567891}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{B2C3D4E5-F6A1-7890-BCDE-FA1234567891}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{B2C3D4E5-F6A1-7890-BCDE-FA1234567891}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{B2C3D4E5-F6A1-7890-BCDE-FA1234567891}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
	GlobalSection(NestedProjects) = preSolution
		{C1D2E3F4-A5B6-7890-CDEF-AB1234567890} = {A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
		{D1E2F3A4-B5C6-7890-DEFA-BC1234567890} = {A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
		{E1F2A3B4-C5D6-7890-EFAB-CD1234567890} = {A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
		{F1A2B3C4-D5E6-7890-FABC-DE1234567890} = {A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
		{A2B3C4D5-E6F1-7890-ABCD-EF1234567891} = {B1C2D3E4-F5A6-7890-BCDE-FA1234567890}
		{B2C3D4E5-F6A1-7890-BCDE-FA1234567891} = {B1C2D3E4-F5A6-7890-BCDE-FA1234567890}
	EndGlobalSection
EndGlobal
```

### TaskManagement.Api.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <DockerDefaultTargetOS>Linux</DockerDefaultTargetOS>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="AutoMapper.Extensions.Microsoft.DependencyInjection" Version="12.0.1" />
    <PackageReference Include="FluentValidation.AspNetCore" Version="11.3.0" />
    <PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="8.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
    </PackageReference>
    <PackageReference Include="Serilog.AspNetCore" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\TaskManagement.Application\TaskManagement.Application.csproj" />
    <ProjectReference Include="..\TaskManagement.Infrastructure\TaskManagement.Infrastructure.csproj" />
  </ItemGroup>

</Project>
```

### Program.cs
```csharp
using Microsoft.EntityFrameworkCore;
using Serilog;
using TaskManagement.Infrastructure.Data;

var builder = WebApplication.CreateBuilder(args);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .CreateLogger();

builder.Host.UseSerilog();

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new()
    {
        Title = "Task Management API",
        Version = "v1",
        Description = "RESTful API for task management"
    });
});

// Database
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// Health checks
builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseSerilogRequestLogging();

app.UseHttpsRedirection();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.MapHealthChecks("/health");

try
{
    Log.Information("Starting Task Management API");
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}
```

### appsettings.json
```json
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft": "Warning",
        "Microsoft.Hosting.Lifetime": "Information"
      }
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Database=taskmanagement;Username=postgres;Password=password"
  },
  "Jwt": {
    "SecretKey": "your-secret-key-change-in-production",
    "Issuer": "TaskManagement.Api",
    "Audience": "TaskManagement.Api",
    "ExpirationMinutes": 60
  }
}
```

### ApplicationDbContext.cs
```csharp
using Microsoft.EntityFrameworkCore;
using TaskManagement.Core.Entities;

namespace TaskManagement.Infrastructure.Data;

/// <summary>
/// Application database context for Task Management.
/// </summary>
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<TaskItem> Tasks => Set<TaskItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}
```

### HealthController.cs
```csharp
using Microsoft.AspNetCore.Mvc;

namespace TaskManagement.Api.Controllers;

/// <summary>
/// Health check controller for monitoring application status.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    /// <summary>
    /// Get application health status.
    /// </summary>
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new
        {
            Status = "Healthy",
            Timestamp = DateTime.UtcNow,
            Version = "0.1.0"
        });
    }
}
```

### ExceptionHandlingMiddleware.cs
```csharp
using System.Net;
using System.Text.Json;

namespace TaskManagement.Api.Middleware;

/// <summary>
/// Middleware for centralized exception handling.
/// </summary>
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

    private static async Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = (int)HttpStatusCode.InternalServerError;

        var response = new
        {
            StatusCode = context.Response.StatusCode,
            Message = "Internal Server Error",
            Detailed = exception.Message
        };

        var json = JsonSerializer.Serialize(response);
        await context.Response.WriteAsync(json);
    }
}
```

### Dockerfile
```dockerfile
# Build stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy solution and project files
COPY ["TaskManagement.sln", "."]
COPY ["src/TaskManagement.Api/TaskManagement.Api.csproj", "src/TaskManagement.Api/"]
COPY ["src/TaskManagement.Core/TaskManagement.Core.csproj", "src/TaskManagement.Core/"]
COPY ["src/TaskManagement.Application/TaskManagement.Application.csproj", "src/TaskManagement.Application/"]
COPY ["src/TaskManagement.Infrastructure/TaskManagement.Infrastructure.csproj", "src/TaskManagement.Infrastructure/"]

# Restore dependencies
RUN dotnet restore

# Copy all source code
COPY . .

# Build and publish
WORKDIR "/src/src/TaskManagement.Api"
RUN dotnet build -c Release -o /app/build
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
EXPOSE 80
EXPOSE 443

COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "TaskManagement.Api.dll"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: taskmanagement
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:

      - "5432:5432"
    volumes:

      - postgres_data:/var/lib/postgresql/data
    networks:

      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:

      - "5000:80"
    environment:

      - ASPNETCORE_ENVIRONMENT=Production

      - ConnectionStrings__DefaultConnection=Host=postgres;Database=taskmanagement;Username=postgres;Password=password
    depends_on:
      postgres:
        condition: service_healthy
    networks:

      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

### .gitignore
```
# Build results
[Dd]ebug/
[Dd]ebugPublic/
[Rr]elease/
[Rr]eleases/
x64/
x86/
[Ww][Ii][Nn]32/
[Aa][Rr][Mm]/
[Aa][Rr][Mm]64/
bld/
[Bb]in/
[Oo]bj/
[Ll]og/
[Ll]ogs/

# Visual Studio
.vs/
.vscode/
*.user
*.userosscache
*.suo
*.userprefs
*.sln.docstates

# ReSharper
_ReSharper*/
*.[Rr]e[Ss]harper
*.DotSettings.user

# JetBrains Rider
.idea/
*.sln.iml

# NuGet
*.nupkg
*.snupkg
**/packages/*
!**/packages/build/
project.lock.json
project.fragment.lock.json
artifacts/

# Test Results
[Tt]est[Rr]esult*/
[Bb]uild[Ll]og.*
*.trx
*.coverage
*.coveragexml
TestResults/

# ASP.NET Scaffolding
ScaffoldingReadMe.txt

# Database
*.db
*.db-shm
*.db-wal

# Environment
.env
appsettings.Local.json
appsettings.*.Local.json

# OS
.DS_Store
Thumbs.db
```

### global.json
```json
{
  "sdk": {
    "version": "8.0.0",
    "rollForward": "latestMinor"
  }
}
```

### Directory.Build.props
```xml
<Project>
  <PropertyGroup>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>false</TreatWarningsAsErrors>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
  </PropertyGroup>
</Project>
```

### README.md
```markdown
# Task Management API - v0.1.0

## What's New
- Initial release

- ASP.NET Core 8.0 Web API

- Entity Framework Core with PostgreSQL

- JWT authentication

- OpenAPI/Swagger documentation

## Overview
A production-ready RESTful API for task management built with ASP.NET Core 8.0, Entity Framework Core, and PostgreSQL. Provides comprehensive endpoints for user authentication and task management with full OpenAPI documentation.

## Features
- **Authentication**: JWT-based authentication

- **Task Management**: Full CRUD operations

- **Validation**: FluentValidation for input validation

- **Documentation**: Interactive API documentation with Swagger UI

- **Monitoring**: Health checks and structured logging

- **Database Migrations**: Entity Framework Core migrations

- **Containerization**: Docker and docker-compose configuration

## Technology Stack
- .NET 8.0

- ASP.NET Core 8.0

- Entity Framework Core 8.0

- PostgreSQL

- AutoMapper

- FluentValidation

- Serilog

- Swagger/OpenAPI

## Installation

### Prerequisites
- .NET 8 SDK or higher

- PostgreSQL 12+ (or Docker)

- Docker (optional)

### Setup

#### Using .NET CLI
```bash
git clone <repository-url>
cd TaskManagement

# Restore dependencies
dotnet restore

# Update database
dotnet ef database update --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api

# Run application
dotnet run --project src/TaskManagement.Api
```

#### Using Docker
```bash
git clone <repository-url>
cd TaskManagement/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Configuration

Update `src/TaskManagement.Api/appsettings.Development.json`:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Database=taskmanagement;Username=postgres;Password=password"
  },
  "Jwt": {
    "SecretKey": "your-secret-key-at-least-32-characters-long",
    "Issuer": "TaskManagement.Api",
    "Audience": "TaskManagement.Api",
    "ExpirationMinutes": 60
  }
}
```

## Usage

### API Documentation
- **Swagger UI**: http://localhost:5000/swagger

- **Health Check**: http://localhost:5000/health

### Example Endpoints
```
GET    /health                      - Health check
POST   /api/v1/auth/register        - Register new user
POST   /api/v1/auth/login           - Login user
GET    /api/v1/tasks                - Get all tasks
POST   /api/v1/tasks                - Create new task
GET    /api/v1/tasks/{id}           - Get task by ID
PUT    /api/v1/tasks/{id}           - Update task
DELETE /api/v1/tasks/{id}           - Delete task
```

## Development

### Running Tests
```bash
# All tests
dotnet test

# Specific project
dotnet test tests/TaskManagement.UnitTests

# With coverage
dotnet test /p:CollectCoverage=true /p:CoverageReportFormat=opencover
```

### Database Migrations
```bash
# Add migration
dotnet ef migrations add MigrationName --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api

# Update database
dotnet ef database update --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api

# Remove last migration
dotnet ef migrations remove --project src/TaskManagement.Infrastructure --startup-project src/TaskManagement.Api
```

### Code Quality
```bash
# Format code
dotnet format

# Build in Release mode
dotnet build -c Release

# Publish for deployment
dotnet publish -c Release -o ./publish
```

## Contributing
1. Fork the repository

2. Create a feature branch

3. Make your changes

4. Run tests and ensure coverage

5. Submit a pull request

## License
MIT

## Contact
Your Name - your.email@example.com
```

### CHANGELOG.md
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.1.0] - 2025-10-21

### Added
- Initial ASP.NET Core 8.0 project structure

- Entity Framework Core with PostgreSQL

- JWT authentication implementation

- Task CRUD operations

- OpenAPI/Swagger documentation

- Global exception handling middleware

- Health check endpoints

- Docker configuration

- Comprehensive test suite

- Structured logging with Serilog
```

### DEVLOG.md
```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement user authentication

- [ ] Create task entity and DbContext

- [ ] Add task CRUD endpoints

- [ ] Configure JWT authentication

### Medium Priority
- [ ] Add task filtering and sorting

- [ ] Implement pagination

- [ ] Add task categories

- [ ] Create user profile management

### Low Priority
- [ ] Add task search functionality

- [ ] Implement task sharing

- [ ] Add email notifications

- [ ] Create admin dashboard

## Development History

### Project Architecture
- **Design**: RESTful API with ASP.NET Core

- **Tech Stack**: .NET 8, ASP.NET Core, Entity Framework Core, PostgreSQL

- **Pattern**: Layered architecture (API-Application-Infrastructure-Core)

### Initial Setup - 2025-10-21
- Created standard ASP.NET Core project structure

- Configured Entity Framework Core

- Set up testing framework (xUnit)

- Configured OpenAPI documentation

- Initialized Docker configuration

## Troubleshooting History

(Document issues and solutions here as they arise)
```

## Project Types and Variations

### Web API with Authentication
```
Additional Dependencies:

- Microsoft.AspNetCore.Authentication.JwtBearer

- Microsoft.AspNetCore.Identity.EntityFrameworkCore

- IdentityModel
```

### Clean Architecture with CQRS
```
Additional Dependencies:

- MediatR

- MediatR.Extensions.Microsoft.DependencyInjection

- FluentValidation.DependencyInjectionExtensions
```

### Microservice
```
Additional Dependencies:

- Polly (resilience)

- RabbitMQ.Client (messaging)

- StackExchange.Redis (caching)

- OpenTelemetry (observability)
```

## Success Criteria

After initialization, verify:

- [ ] Solution builds successfully

- [ ] All projects compile

- [ ] Application starts

- [ ] Tests run and pass

- [ ] Swagger UI accessible

- [ ] Health endpoint responds

- [ ] Database migrations work

- [ ] Docker containers start

- [ ] Documentation complete

- [ ] Ready to begin development

## Related Skills

**Use After Initialization**:

- `setup-csharp-system-prompt`: Configure Claude Code standards

- `create-claude-md`: Customize project guidelines

- `generate-test-cases`: Add comprehensive tests

**For Development**:

- `plan-before-code`: Plan features before implementing

- `test-driven-development`: Write tests first

- `cleanup-csharp`: Clean code periodically

## Additional Resources

- [ASP.NET Core Documentation](https://docs.microsoft.com/aspnet/core/)

- [Entity Framework Core Documentation](https://docs.microsoft.com/ef/core/)

- [Clean Architecture Guide](https://github.com/jasontaylordev/CleanArchitecture)

- [.NET CLI Reference](https://docs.microsoft.com/dotnet/core/tools/)

- [xUnit Documentation](https://xunit.net/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - C# Project Standards
**Priority**: MEDIUM - Standard C#/.NET project initialization
