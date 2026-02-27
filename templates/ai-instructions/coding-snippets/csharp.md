## C# Conventions

**Tooling**:
- **Build**: `dotnet build`
- **Formatting**: `dotnet format` (EditorConfig)
- **Target**: .NET 8+ (LTS preferred)

**Naming**: `PascalCase` for public members/methods/classes, `camelCase` for locals/parameters, `_camelCase` for private fields

**Code Patterns**:
- `using` statements/declarations for all `IDisposable` resources
- `async/await` for I/O-bound operations; never `.Result` or `.Wait()`
- Modern C# features (records, pattern matching, file-scoped namespaces, global usings)
- Auto-implemented properties (`public string Name { get; set; }`)
- LINQ for collections manipulation
- Built-in DI container (Microsoft.Extensions.DependencyInjection)

**Testing**: xUnit (preferred) or NUnit, with Moq or NSubstitute for mocking.

```csharp
public class CalculatorTests
{
    [Fact]
    public void Add_ShouldReturnSum()
    {
        var calculator = new Calculator();
        Assert.Equal(5, calculator.Add(2, 3));
    }
}
```
