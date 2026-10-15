### Step 4: Embrace Pattern Matching and Modern C#

**Switch Expressions and Property Patterns**:

```csharp
// Switch expression with pattern matching
public decimal CalculateDiscount(Customer customer) => customer switch
{
    { Tier: CustomerTier.Gold, YearsActive: > 5 } => 0.25m,
    { Tier: CustomerTier.Gold } => 0.20m,
    { Tier: CustomerTier.Silver, YearsActive: > 3 } => 0.15m,
    { Tier: CustomerTier.Silver } => 0.10m,
    { IsNewCustomer: true } => 0.05m,
    _ => 0m
};

// Type patterns with when clauses
public string FormatError(Exception ex) => ex switch
{
    ArgumentNullException ane => $"Missing required argument: {ane.ParamName}",
    ValidationException ve when ve.Errors.Count > 1 => $"Multiple validation errors ({ve.Errors.Count})",
    ValidationException ve => $"Validation failed: {ve.Errors.First().ErrorMessage}",
    HttpRequestException { StatusCode: HttpStatusCode.NotFound } => "Resource not found",
    HttpRequestException hre => $"HTTP error: {hre.StatusCode}",
    _ => $"Unexpected error: {ex.Message}"
};
```

**List Patterns and Records**:

```csharp
// List patterns (C# 11+)
public string DescribeSequence(int[] numbers) => numbers switch
{
    [] => "empty",
    [var single] => $"single element: {single}",
    [var first, .., var last] => $"starts with {first}, ends with {last}",
};

// Records with value equality and immutability
public record Address(string Street, string City, string State, string Zip);

public record Customer(string Name, string Email, Address Address)
{
    // Computed property on a record
    public string DisplayName => $"{Name} ({Email})";
}

// Non-destructive mutation with 'with' expressions
var updated = customer with { Email = "new@example.com" };

// Record structs for value types
public readonly record struct Coordinate(double Latitude, double Longitude);

// Init-only setters for classes that are not records
public class AppConfig
{
    public string ConnectionString { get; init; } = string.Empty;
    public int MaxRetries { get; init; } = 3;
    public TimeSpan Timeout { get; init; } = TimeSpan.FromSeconds(30);
}

var config = new AppConfig
{
    ConnectionString = "Server=localhost;Database=app",
    MaxRetries = 5
};
// config.ConnectionString = "other"; // Compile error: init-only
```

**File-Scoped Namespaces and Global Usings**:

```csharp
// File-scoped namespace (C# 10+): saves one level of indentation
namespace MyApp.Services;

public class OrderService
{
    // Entire file is in this namespace
}

// GlobalUsings.cs: declare common imports once for the whole project
global using System.Collections.Generic;
global using System.Linq;
global using System.Threading;
global using System.Threading.Tasks;
global using Microsoft.Extensions.Logging;
global using MyApp.Domain.Entities;
```
