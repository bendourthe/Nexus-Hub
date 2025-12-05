---
template_id: csharp_unit_tests
template_name: Unit Tests - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: test_development
phase: unit_tests
phase_number: 2
difficulty: intermediate
estimated_time_hours: 3-6
prerequisites:

  - test_development/test_structure/csharp_test_structure.md
related_templates:

  - test_development/test_cases/csharp_test_cases.md
tools:

  - NUnit (4.2.2)
  - xUnit
  - MSTest
tags:

  - test-development
  - testing
  - c#
---
# C# Unit Tests - Comprehensive Implementation Guide

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                             ► │ ● CURRENT
│ Phase 3: Test Cases Development                    ► │ [NEXT]
│ Phase 4: Mocks & Fixtures                                ► │ 
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 1 (Test Structure Setup) should be completed first
**Next Step:** Phase 3 (Test Cases Development)

---


## Objective

Develop a comprehensive unit testing strategy for C# applications using xUnit and NUnit frameworks, focusing on test isolation, fast execution, and thorough coverage of individual components following FIRST principles and AAA patterns.

---

## Output Directory Structure

```
${OUTPUT_DIR}/
├── templates/           # Reusable test templates
├── assets/             # Diagrams and visualizations
└── exports/            # Final documentation
```

---

## Implementation Checklist

### Test Foundation
- [ ] xUnit and NUnit framework comparison
- [ ] Test project structure established
- [ ] Naming conventions documented
- [ ] Configuration files created

### Test Patterns
- [ ] Method and class tests
- [ ] Async/await test patterns
- [ ] Exception testing patterns
- [ ] Theory and data-driven tests

### Test Quality
- [ ] Test independence verified
- [ ] Mock patterns documented (Moq)
- [ ] Edge cases covered
- [ ] Anti-patterns identified

---

## Prompt Template

~~~markdown
# C# Unit Testing Implementation - Comprehensive Guide

## Context
Generate comprehensive guidance for implementing unit tests in C# applications using xUnit/NUnit frameworks with detailed examples.

## CRITICAL: Output Directory Setup

```bash
mkdir -p ${OUTPUT_DIR}/templates ${OUTPUT_DIR}/assets ${OUTPUT_DIR}/exports
```

---

## Phase 1: Unit Testing Fundamentals

### 1.1 FIRST Principles

**Fast** - Tests execute in milliseconds
- Use `[Fact(Timeout = 1000)]` to enforce speed
- Avoid I/O operations
- Mock external dependencies

**Independent** - No shared state between tests
- Use test class constructors for setup
- Use `IDisposable` for cleanup
- Each test creates its own test data

**Repeatable** - Deterministic results
- Mock `DateTime.Now` with `ISystemClock`
- Control randomness
- Isolate from environment

**Self-validating** - Clear pass/fail
- Use descriptive assertion messages
- Use FluentAssertions for readability
- Avoid manual verification

**Timely** - Written with or before code
- Follow TDD practices
- Maintain high coverage

**AAA Pattern:**
```csharp
[Fact]
public void CalculateDiscount_WithValidRate_ReturnsDiscountedPrice()
{
    // Arrange
    var calculator = new PriceCalculator();
    decimal originalPrice = 100m;
    decimal discountRate = 0.20m;

    // Act
    decimal result = calculator.CalculateDiscount(originalPrice, discountRate);

    // Assert
    Assert.Equal(80m, result);
}
```

### 1.2 Common Anti-Patterns

**Anti-Pattern: Testing Implementation**
```csharp
// BAD
[Fact]
public void Sort_UsesQuickSort()
{
    var sorter = new Sorter();
    sorter.Sort(new[] { 3, 1, 2 });
    Assert.Equal("QuickSort", sorter.AlgorithmUsed);
}

// GOOD
[Fact]
public void Sort_ReturnsAscendingOrder()
{
    var sorter = new Sorter();
    var result = sorter.Sort(new[] { 3, 1, 2 });
    Assert.Equal(new[] { 1, 2, 3 }, result);
}
```

---

## Phase 2: Test Organization

### 2.1 Project Structure

```
Solution/
├── src/
│   └── MyApp/
│       ├── Calculator.cs
│       └── Services/
│           └── UserService.cs
└── tests/
    └── MyApp.Tests/
        ├── CalculatorTests.cs
        └── Services/
            └── UserServiceTests.cs
```

### 2.2 Test Naming

**Class Naming:** `<ClassName>Tests`
- `CalculatorTests`
- `UserServiceTests`

**Method Naming:** `MethodName_StateUnderTest_ExpectedBehavior`
```csharp
[Fact]
public void Add_TwoPositiveNumbers_ReturnsSum() { }

[Fact]
public void Divide_ByZero_ThrowsDivideByZeroException() { }

[Fact]
public void GetUser_WithInvalidId_ReturnsNull() { }
```

### 2.3 xUnit Configuration

**Project File (.csproj):**
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.6.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.3" />
    <PackageReference Include="Moq" Version="4.20.69" />
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
    <PackageReference Include="coverlet.collector" Version="6.0.0" />
  </ItemGroup>
</Project>
```

---

## Phase 3: Testing Different Components

### 3.1 Testing Pure Methods

**Example:**
```csharp
public class Calculator
{
    public decimal CalculateDiscount(decimal price, decimal discountRate)
    {
        if (price < 0)
            throw new ArgumentException("Price cannot be negative", nameof(price));
        if (discountRate < 0 || discountRate > 1)
            throw new ArgumentException("Discount rate must be between 0 and 1", nameof(discountRate));

        return price * (1 - discountRate);
    }
}
```

**Tests:**
```csharp
public class CalculatorTests
{
    private readonly Calculator _calculator;

    public CalculatorTests()
    {
        _calculator = new Calculator();
    }

    [Fact]
    public void CalculateDiscount_WithNoDiscount_ReturnsOriginalPrice()
    {
        // Arrange
        decimal price = 100m;
        decimal discountRate = 0m;

        // Act
        decimal result = _calculator.CalculateDiscount(price, discountRate);

        // Assert
        Assert.Equal(100m, result);
    }

    [Fact]
    public void CalculateDiscount_WithFullDiscount_ReturnsZero()
    {
        var result = _calculator.CalculateDiscount(100m, 1m);
        Assert.Equal(0m, result);
    }

    [Theory]
    [InlineData(100, 0.20, 80)]
    [InlineData(50, 0.10, 45)]
    [InlineData(200, 0.25, 150)]
    public void CalculateDiscount_VariousCombinations_ReturnsCorrectValue(
        decimal price, decimal rate, decimal expected)
    {
        var result = _calculator.CalculateDiscount(price, rate);
        Assert.Equal(expected, result);
    }

    [Fact]
    public void CalculateDiscount_WithNegativePrice_ThrowsArgumentException()
    {
        var exception = Assert.Throws<ArgumentException>(
            () => _calculator.CalculateDiscount(-100m, 0.20m));
        Assert.Contains("Price cannot be negative", exception.Message);
    }

    [Fact]
    public void CalculateDiscount_WithInvalidRate_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() => _calculator.CalculateDiscount(100m, 1.5m));
    }
}
```

### 3.2 Testing Classes with State

**Example:**
```csharp
public class User
{
    public string Name { get; }
    public string Email { get; }
    public int? Age { get; }
    public DateTime CreatedAt { get; }
    public bool IsActive { get; private set; }

    public User(string name, string email, int? age = null)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name cannot be empty", nameof(name));
        if (!IsValidEmail(email))
            throw new ArgumentException("Invalid email format", nameof(email));
        if (age < 0)
            throw new ArgumentException("Age cannot be negative", nameof(age));

        Name = name;
        Email = email;
        Age = age;
        CreatedAt = DateTime.UtcNow;
        IsActive = true;
    }

    public void Deactivate() => IsActive = false;
    public void Activate() => IsActive = true;

    private static bool IsValidEmail(string email) =>
        !string.IsNullOrWhiteSpace(email) && email.Contains("@");
}
```

**Tests:**
```csharp
public class UserTests
{
    [Fact]
    public void Constructor_WithValidInputs_SetsAllProperties()
    {
        // Arrange & Act
        var user = new User("John Doe", "john@example.com", 30);

        // Assert
        Assert.Equal("John Doe", user.Name);
        Assert.Equal("john@example.com", user.Email);
        Assert.Equal(30, user.Age);
        Assert.True(user.IsActive);
        Assert.NotEqual(default, user.CreatedAt);
    }

    [Fact]
    public void Constructor_WithoutAge_SetsAgeToNull()
    {
        var user = new User("Jane", "jane@example.com");
        Assert.Null(user.Age);
    }

    [Theory]
    [InlineData("")]
    [InlineData(null)]
    [InlineData("   ")]
    public void Constructor_WithInvalidName_ThrowsArgumentException(string name)
    {
        Assert.Throws<ArgumentException>(() => new User(name, "test@example.com"));
    }

    [Theory]
    [InlineData("invalid")]
    [InlineData("@example.com")]
    [InlineData("user@")]
    public void Constructor_WithInvalidEmail_ThrowsArgumentException(string email)
    {
        Assert.Throws<ArgumentException>(() => new User("John", email));
    }

    [Fact]
    public void Deactivate_SetsIsActiveToFalse()
    {
        var user = new User("John", "john@example.com");
        user.Deactivate();
        Assert.False(user.IsActive);
    }

    [Fact]
    public void Activate_AfterDeactivation_SetsIsActiveToTrue()
    {
        var user = new User("John", "john@example.com");
        user.Deactivate();
        user.Activate();
        Assert.True(user.IsActive);
    }
}
```

### 3.3 Testing Async Methods

**Example:**
```csharp
public class DataService
{
    public async Task<string> FetchDataAsync(string url)
    {
        if (string.IsNullOrWhiteSpace(url))
            throw new ArgumentException("URL cannot be empty", nameof(url));

        await Task.Delay(100); // Simulate async operation

        if (url.Contains("timeout"))
            throw new TimeoutException("Request timed out");

        return $"Data from {url}";
    }

    public async Task<List<string>> FetchMultipleAsync(List<string> urls)
    {
        var tasks = urls.Select(url => FetchDataAsync(url));
        return (await Task.WhenAll(tasks)).ToList();
    }
}
```

**Tests:**
```csharp
public class DataServiceTests
{
    private readonly DataService _service;

    public DataServiceTests()
    {
        _service = new DataService();
    }

    [Fact]
    public async Task FetchDataAsync_WithValidUrl_ReturnsData()
    {
        // Act
        var result = await _service.FetchDataAsync("https://example.com");

        // Assert
        Assert.Contains("https://example.com", result);
    }

    [Fact]
    public async Task FetchDataAsync_WithEmptyUrl_ThrowsArgumentException()
    {
        await Assert.ThrowsAsync<ArgumentException>(
            () => _service.FetchDataAsync(""));
    }

    [Fact]
    public async Task FetchDataAsync_WithTimeoutUrl_ThrowsTimeoutException()
    {
        await Assert.ThrowsAsync<TimeoutException>(
            () => _service.FetchDataAsync("https://timeout.com"));
    }

    [Fact]
    public async Task FetchMultipleAsync_WithMultipleUrls_ReturnsAllResults()
    {
        // Arrange
        var urls = new List<string> { "https://a.com", "https://b.com" };

        // Act
        var results = await _service.FetchMultipleAsync(urls);

        // Assert
        Assert.Equal(2, results.Count);
        Assert.All(results, r => Assert.NotEmpty(r));
    }
}
```

### 3.4 Testing with Moq

**Example:**
```csharp
public interface IUserRepository
{
    User GetById(int id);
    void Save(User user);
}

public class UserService
{
    private readonly IUserRepository _repository;

    public UserService(IUserRepository repository)
    {
        _repository = repository;
    }

    public User GetUser(int id)
    {
        if (id <= 0)
            throw new ArgumentException("ID must be positive", nameof(id));

        return _repository.GetById(id);
    }

    public void ActivateUser(int id)
    {
        var user = _repository.GetById(id);
        if (user != null)
        {
            user.Activate();
            _repository.Save(user);
        }
    }
}
```

**Tests:**
```csharp
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _mockRepository;
    private readonly UserService _service;

    public UserServiceTests()
    {
        _mockRepository = new Mock<IUserRepository>();
        _service = new UserService(_mockRepository.Object);
    }

    [Fact]
    public void GetUser_WithValidId_CallsRepository()
    {
        // Arrange
        var user = new User("John", "john@example.com");
        _mockRepository.Setup(r => r.GetById(1)).Returns(user);

        // Act
        var result = _service.GetUser(1);

        // Assert
        Assert.Equal(user, result);
        _mockRepository.Verify(r => r.GetById(1), Times.Once);
    }

    [Fact]
    public void GetUser_WithInvalidId_ThrowsArgumentException()
    {
        Assert.Throws<ArgumentException>(() => _service.GetUser(0));
        _mockRepository.Verify(r => r.GetById(It.IsAny<int>()), Times.Never);
    }

    [Fact]
    public void ActivateUser_WithExistingUser_ActivatesAndSaves()
    {
        // Arrange
        var user = new User("John", "john@example.com");
        user.Deactivate();
        _mockRepository.Setup(r => r.GetById(1)).Returns(user);

        // Act
        _service.ActivateUser(1);

        // Assert
        Assert.True(user.IsActive);
        _mockRepository.Verify(r => r.GetById(1), Times.Once);
        _mockRepository.Verify(r => r.Save(user), Times.Once);
    }

    [Fact]
    public void ActivateUser_WithNonExistentUser_DoesNotSave()
    {
        // Arrange
        _mockRepository.Setup(r => r.GetById(999)).Returns((User)null);

        // Act
        _service.ActivateUser(999);

        // Assert
        _mockRepository.Verify(r => r.Save(It.IsAny<User>()), Times.Never);
    }
}
```

### 3.5 Testing Collections and LINQ

**Example:**
```csharp
public static class CollectionUtils
{
    public static List<int> FilterEven(List<int> numbers)
    {
        return numbers?.Where(n => n % 2 == 0).ToList() ?? new List<int>();
    }

    public static Dictionary<int, int> GroupByLength(List<string> strings)
    {
        return strings?
            .GroupBy(s => s.Length)
            .ToDictionary(g => g.Key, g => g.Count())
            ?? new Dictionary<int, int>();
    }

    public static List<T> RemoveDuplicates<T>(List<T> list)
    {
        return list?.Distinct().ToList() ?? new List<T>();
    }
}
```

**Tests:**
```csharp
public class CollectionUtilsTests
{
    [Fact]
    public void FilterEven_WithMixedNumbers_ReturnsOnlyEven()
    {
        var input = new List<int> { 1, 2, 3, 4, 5, 6 };
        var result = CollectionUtils.FilterEven(input);
        Assert.Equal(new List<int> { 2, 4, 6 }, result);
    }

    [Fact]
    public void FilterEven_WithNull_ReturnsEmptyList()
    {
        var result = CollectionUtils.FilterEven(null);
        Assert.Empty(result);
    }

    [Theory]
    [MemberData(nameof(GroupByLengthData))]
    public void GroupByLength_GroupsCorrectly(List<string> input, Dictionary<int, int> expected)
    {
        var result = CollectionUtils.GroupByLength(input);
        Assert.Equal(expected, result);
    }

    public static IEnumerable<object[]> GroupByLengthData =>
        new List<object[]>
        {
            new object[] {
                new List<string> { "a", "bb", "ccc", "dd" },
                new Dictionary<int, int> { { 1, 1 }, { 2, 2 }, { 3, 1 } }
            },
            new object[] {
                new List<string>(),
                new Dictionary<int, int>()
            }
        };

    [Fact]
    public void RemoveDuplicates_RemovesDuplicateValues()
    {
        var input = new List<int> { 1, 2, 2, 3, 3, 3, 4 };
        var result = CollectionUtils.RemoveDuplicates(input);
        Assert.Equal(new List<int> { 1, 2, 3, 4 }, result);
    }
}
```

---

## Phase 4: Advanced Patterns

### 4.1 FluentAssertions

```csharp
using FluentAssertions;

[Fact]
public void User_ShouldHaveCorrectProperties()
{
    var user = new User("John", "john@example.com", 30);

    user.Name.Should().Be("John");
    user.Email.Should().Contain("@");
    user.Age.Should().BeGreaterThan(18);
    user.IsActive.Should().BeTrue();
}

[Fact]
public void Collection_ShouldContainExpectedItems()
{
    var numbers = new List<int> { 1, 2, 3, 4, 5 };

    numbers.Should().NotBeEmpty()
           .And.HaveCount(5)
           .And.Contain(3)
           .And.NotContain(6)
           .And.BeInAscendingOrder();
}

[Fact]
public void Exception_ShouldBeThrownWithCorrectMessage()
{
    Action act = () => throw new ArgumentException("Invalid argument");

    act.Should().Throw<ArgumentException>()
       .WithMessage("Invalid argument");
}
```

### 4.2 Testing Disposable Resources

```csharp
public class DisposableResourceTests : IDisposable
{
    private readonly DatabaseConnection _connection;

    public DisposableResourceTests()
    {
        _connection = new DatabaseConnection();
    }

    [Fact]
    public void UseConnection_PerformsOperation()
    {
        // Test using _connection
        Assert.True(_connection.IsOpen);
    }

    public void Dispose()
    {
        _connection?.Dispose();
    }
}
```

### 4.3 Testing Static Methods

```csharp
public static class DateUtils
{
    public static bool IsWeekend(DateTime date)
    {
        return date.DayOfWeek == DayOfWeek.Saturday ||
               date.DayOfWeek == DayOfWeek.Sunday;
    }
}

public class DateUtilsTests
{
    [Theory]
    [InlineData("2024-01-06", true)]  // Saturday
    [InlineData("2024-01-07", true)]  // Sunday
    [InlineData("2024-01-08", false)] // Monday
    public void IsWeekend_ReturnsCorrectValue(string dateString, bool expected)
    {
        var date = DateTime.Parse(dateString);
        Assert.Equal(expected, DateUtils.IsWeekend(date));
    }
}
```

---

## Phase 5: Test Quality

### 5.1 Code Coverage

**Run with coverage:**
```bash
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=opencover
dotnet tool install -g dotnet-reportgenerator-globaltool
reportgenerator -reports:coverage.opencover.xml -targetdir:coverage
```

### 5.2 Test Maintenance Checklist

- [ ] All tests pass independently
- [ ] Tests run in any order
- [ ] Descriptive test names
- [ ] Fast execution (<100ms per test)
- [ ] No code duplication in tests
- [ ] Clear AAA pattern
- [ ] Appropriate use of mocks
- [ ] Edge cases covered
- [ ] >80% code coverage for critical paths

---

## Output Deliverables

Generate these files:

### 1. Implementation Guide (20-30 pages)
`${OUTPUT_DIR}/exports/unit_test_implementation_guide.md`

### 2. Test Examples Collection (50+ tests)
`${OUTPUT_DIR}/exports/unit_test_examples.md`

### 3. Templates
`${OUTPUT_DIR}/templates/`:

- `UnitTestTemplate.cs`
- `MockTestTemplate.cs`
- `AsyncTestTemplate.cs`
- `test.csproj`
- `xunit.runner.json`

### 4. Configuration Files
- `.csproj` with all dependencies
- `xunit.runner.json`
- `.runsettings` for test execution

### 5. Visual Assets
`${OUTPUT_DIR}/assets/`:

- FIRST principles diagram
- AAA pattern visualization
- Test pyramid
- Project structure diagram

### 6. Guides
- Anti-patterns guide
- Quality checklist
- Moq usage guide
- FluentAssertions guide

---

## Verification Checklist

- [ ] All deliverables created
- [ ] 20-30 page implementation guide
- [ ] 50+ test examples
- [ ] xUnit and NUnit examples
- [ ] Moq patterns documented
- [ ] FluentAssertions covered
- [ ] Async testing covered
- [ ] Configuration files complete

---
~~~

End of prompt template.

---

## Additional Notes

- Install: `dotnet add package xunit`
- Run tests: `dotnet test`
- Coverage: `dotnet test /p:CollectCoverage=true`
- Watch mode: `dotnet watch test`
- Filter: `dotnet test --filter "FullyQualifiedName~Calculator"`

---

**Status:** Template ready for use. Copy the prompt section into your AI assistant to generate comprehensive C# unit testing guidance.
