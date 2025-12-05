---
template_id: csharp_mocks_fixtures
template_name: Mocks & Fixtures - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: test_development
phase: mocks_fixtures
phase_number: 4
difficulty: intermediate
estimated_time_hours: 3-5
prerequisites:

  - test_development/test_cases/csharp_test_cases.md
related_templates:

  - test_development/performance_testing/csharp_performance_testing.md
tools:

  - NUnit (4.2.2)

  - xUnit

  - MSTest
tags:

  - test-development

  - c#
---
# C# Mocks & Fixtures

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                       ► │ ● CURRENT
│ Phase 5: Performance Testing                       ► │ [NEXT]
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 3 (Test Cases Development) should be completed first
**Next Step:** Phase 5 (Performance Testing)

---


## Objective
Design and implement effective mocking strategies and fixture management using Moq and NSubstitute to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/mocks_fixtures/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/mocks_fixtures/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Fixture Setup

- [ ] xUnit/NUnit lifecycle hooks configured appropriately

- [ ] Test data builders created for flexible data generation

- [ ] Fixture factories implemented with realistic data

- [ ] Cleanup and disposal logic automated

- [ ] Fixtures documented with clear purposes

### Mocking Strategy

- [ ] External dependencies identified for mocking

- [ ] Mocking approach chosen (mock vs stub vs fake)

- [ ] Mock objects configured with Moq or NSubstitute

- [ ] Verification methods used appropriately

- [ ] Over-mocking avoided

### Test Data Management

- [ ] Test data factories implemented

- [ ] Realistic test data patterns established

- [ ] Data builders for complex objects created

- [ ] Test data isolated per test

- [ ] Data cleanup automated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Mocks & Fixtures Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/mocks_fixtures"
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

Please implement comprehensive mocking and fixture strategies for this C# project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Fixture Architecture Design

### Understanding xUnit Fixtures

xUnit provides constructor/dispose patterns and class/collection fixtures:

**Basic Setup/Teardown**:
```csharp
using Xunit;

public class UserServiceTests : IDisposable
{
    private readonly Database _database;
    private readonly UserService _userService;
    private readonly User _testUser;

    // Constructor - runs before each test
    public UserServiceTests()
    {
        _database = new Database("test_db");
        _userService = new UserService(_database);
        _testUser = new User
        {
            Username = "testuser",
            Email = "test@example.com"
        };
    }

    // Dispose - runs after each test
    public void Dispose()
    {
        _database.ClearTestData();
        _database.Dispose();
    }

    [Fact]
    public void ShouldCreateUser()
    {
        var result = _userService.CreateUser(_testUser);
        Assert.Equal("testuser", result.Username);
    }
}
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Class Fixtures (IClassFixture)** - Shared across test class:
```csharp
public class DatabaseFixture : IDisposable
{
    public IDbConnection Connection { get; }

    public DatabaseFixture()
    {
        // Expensive setup - run once per class
        Connection = new SqlConnection("Server=.;Database=TestDb");
        Connection.Open();
        InitializeSchema();
    }

    private void InitializeSchema()
    {
        using var cmd = Connection.CreateCommand();
        cmd.CommandText = "CREATE TABLE Users (Id INT, Username NVARCHAR(50))";
        cmd.ExecuteNonQuery();
    }

    public void Dispose()
    {
        Connection?.Dispose();
    }
}

public class UserRepositoryTests : IClassFixture<DatabaseFixture>
{
    private readonly DatabaseFixture _fixture;

    public UserRepositoryTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public void ShouldInsertUser()
    {
        var repo = new UserRepository(_fixture.Connection);
        var user = new User { Id = 1, Username = "alice" };

        repo.Insert(user);

        var retrieved = repo.GetById(1);
        Assert.Equal("alice", retrieved.Username);
    }
}
```

**2. Collection Fixtures** - Shared across multiple test classes:
```csharp
// Define the collection
[CollectionDefinition("Database collection")]
public class DatabaseCollection : ICollectionFixture<DatabaseFixture>
{
    // This class has no code, and is never created
}

// Use the collection
[Collection("Database collection")]
public class UserTests
{
    private readonly DatabaseFixture _fixture;

    public UserTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public void TestUserOperations()
    {
        // Use _fixture.Connection
    }
}

[Collection("Database collection")]
public class OrderTests
{
    private readonly DatabaseFixture _fixture;

    public OrderTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public void TestOrderOperations()
    {
        // Same fixture instance as UserTests
    }
}
```

**3. NUnit Setup/TearDown**:
```csharp
using NUnit.Framework;

[TestFixture]
public class UserServiceTests
{
    private Database _database;
    private UserService _userService;

    [OneTimeSetUp]
    public void OneTimeSetup()
    {
        // Runs once before all tests
        Environment.SetEnvironmentVariable("ENV", "test");
    }

    [SetUp]
    public void SetUp()
    {
        // Runs before each test
        _database = new Database("test_db");
        _userService = new UserService(_database);
    }

    [TearDown]
    public void TearDown()
    {
        // Runs after each test
        _database.ClearTestData();
    }

    [OneTimeTearDown]
    public void OneTimeTearDown()
    {
        // Runs once after all tests
        Database.CloseAllConnections();
    }

    [Test]
    public void ShouldCreateUser()
    {
        var user = new User("testuser", "test@example.com");
        var result = _userService.CreateUser(user);
        Assert.That(result.Username, Is.EqualTo("testuser"));
    }
}
```

### Fixture Factories

Create factories for flexible test data generation:

```csharp
// Tests/Factories/UserFactory.cs
public class UserFactory
{
    private static long _idCounter = 0;
    private readonly List<User> _createdUsers = new();

    public User Create(Action<User> configure = null)
    {
        _idCounter++;
        var user = new User
        {
            Id = _idCounter,
            Username = $"user_{_idCounter}",
            Email = $"user{_idCounter}@test.com",
            Age = 25,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        configure?.Invoke(user);
        _createdUsers.Add(user);
        return user;
    }

    public List<User> CreateBatch(int count, Action<User> configure = null)
    {
        return Enumerable.Range(0, count)
            .Select(_ => Create(configure))
            .ToList();
    }

    public void Reset()
    {
        _idCounter = 0;
        _createdUsers.Clear();
    }
}

// Usage in tests
public class UserOperationsTests
{
    private readonly UserFactory _userFactory;

    public UserOperationsTests()
    {
        _userFactory = new UserFactory();
    }

    [Fact]
    public void ShouldCreateUsersWithDefaults()
    {
        var user1 = _userFactory.Create();
        var user2 = _userFactory.Create();

        Assert.Equal("user_1", user1.Username);
        Assert.Equal("user_2", user2.Username);
    }

    [Fact]
    public void ShouldCreateUsersWithCustomData()
    {
        var user = _userFactory.Create(u =>
        {
            u.Username = "alice";
            u.Email = "alice@example.com";
            u.Age = 30;
        });

        Assert.Equal("alice", user.Username);
        Assert.Equal(30, user.Age);
    }

    [Fact]
    public void ShouldCreateBatchOfUsers()
    {
        var users = _userFactory.CreateBatch(5, u => u.IsActive = false);

        Assert.Equal(5, users.Count);
        Assert.All(users, u => Assert.False(u.IsActive));
    }
}
```

### Builder Pattern for Complex Objects

```csharp
// Tests/Builders/OrderBuilder.cs
public class OrderBuilder
{
    private long? _id;
    private long? _userId;
    private readonly List<OrderItem> _items = new();
    private OrderStatus _status = OrderStatus.Pending;
    private decimal _total = 0;
    private Address _shippingAddress;

    public OrderBuilder WithId(long id)
    {
        _id = id;
        return this;
    }

    public OrderBuilder ForUser(long userId)
    {
        _userId = userId;
        return this;
    }

    public OrderBuilder AddItem(long productId, int quantity, decimal price)
    {
        _items.Add(new OrderItem
        {
            ProductId = productId,
            Quantity = quantity,
            Price = price
        });
        _total += quantity * price;
        return this;
    }

    public OrderBuilder WithStatus(OrderStatus status)
    {
        _status = status;
        return this;
    }

    public OrderBuilder WithShippingAddress(Address address)
    {
        _shippingAddress = address;
        return this;
    }

    public Order Build()
    {
        return new Order
        {
            Id = _id,
            UserId = _userId,
            Items = new List<OrderItem>(_items),
            Status = _status,
            Total = _total,
            ShippingAddress = _shippingAddress
        };
    }
}

// Usage
[Fact]
public void ShouldProcessOrder()
{
    var address = new Address("123 Main St", "Boston", "MA");
    var order = new OrderBuilder()
        .WithId(1)
        .ForUser(100)
        .AddItem(1, 2, 10.00m)
        .AddItem(2, 1, 15.00m)
        .WithStatus(OrderStatus.Confirmed)
        .WithShippingAddress(address)
        .Build();

    Assert.Equal(35.00m, order.Total);
    Assert.Equal(2, order.Items.Count);
}
```

## Phase 2: Mocking Strategies with Moq

### Understanding Moq

Moq is the most popular .NET mocking framework:

```bash
dotnet add package Moq
```

**Creating Mocks**:
```csharp
using Moq;

public class UserServiceTests
{
    private readonly Mock<IUserRepository> _mockRepository;
    private readonly Mock<IEmailService> _mockEmailService;
    private readonly UserService _userService;

    public UserServiceTests()
    {
        _mockRepository = new Mock<IUserRepository>();
        _mockEmailService = new Mock<IEmailService>();
        _userService = new UserService(
            _mockRepository.Object,
            _mockEmailService.Object
        );
    }

    [Fact]
    public void ShouldCreateUser()
    {
        var user = new User("alice", "alice@test.com");
        _mockRepository.Setup(r => r.Save(user)).Returns(user);
        _mockEmailService.Setup(e => e.SendWelcome(user)).Returns(true);

        var result = _userService.CreateUser(user);

        Assert.NotNull(result);
        _mockRepository.Verify(r => r.Save(user), Times.Once);
        _mockEmailService.Verify(e => e.SendWelcome(user), Times.Once);
    }
}
```

### When to Mock vs Use Real Objects

**Use Mocks For**:

- External APIs and services

- Database operations in unit tests

- File system operations

- Network requests

- Slow dependencies

- Non-deterministic behavior

**Use Real Objects For**:

- POCOs and DTOs

- Value objects

- Pure functions

- Integration tests

- Critical business logic

```csharp
// GOOD - Mock external service
[Fact]
public async Task ShouldFetchUserData()
{
    var mockApi = new Mock<IExternalApi>();
    mockApi.Setup(a => a.GetUserAsync(1))
           .ReturnsAsync(new User(1, "alice"));

    var service = new UserService(mockApi.Object);
    var result = await service.FetchFromApiAsync(1);

    Assert.Equal("alice", result.Username);
}

// GOOD - Use real object for simple logic
[Fact]
public void ShouldCalculateTotal()
{
    var items = new[] { 10m, 20m, 30m };
    Assert.Equal(60m, Calculator.Sum(items));
}

// BAD - Over-mocking simple logic
[Fact]
public void ShouldCalculateTotal()
{
    var mockCalc = new Mock<ICalculator>();
    mockCalc.Setup(c => c.Sum(It.IsAny<decimal[]>())).Returns(60m);
    // Testing the mock, not real code
}
```

### Moq Setup and Returns

**Return Values**:
```csharp
// Simple return value
_mockRepository.Setup(r => r.FindById(1)).Returns(user);

// Async return
_mockRepository.Setup(r => r.FindByIdAsync(1))
               .ReturnsAsync(user);

// Different returns per call
_mockApi.SetupSequence(a => a.FetchStatus())
        .Returns(Status.Pending)
        .Returns(Status.Complete);

// Throw exception
_mockDatabase.Setup(d => d.Connect())
             .Throws(new InvalidOperationException("Connection failed"));

// Returns with custom logic
_mockRepository.Setup(r => r.FindById(It.IsAny<long>()))
               .Returns((long id) => id == 1 ? user : null);
```

**Argument Matchers**:
```csharp
// Any argument
_mockRepository.Setup(r => r.Save(It.IsAny<User>())).Returns(user);

// Specific argument
_mockRepository.Setup(r => r.FindById(It.Is<long>(id => id == 1)))
               .Returns(user);

// Condition matcher
_mockRepository.Setup(r => r.Save(It.Is<User>(u => u.Age > 18)))
               .Returns(user);

// Range matcher
_mockRepository.Setup(r => r.FindById(It.IsInRange(1L, 100L, Range.Inclusive)))
               .Returns(user);
```

### Moq Verification

```csharp
var user = new User("alice");

// Verify method was called
_mockRepository.Verify(r => r.Save(user));

// Verify with call count
_mockRepository.Verify(r => r.Save(It.IsAny<User>()), Times.Once);
_mockRepository.Verify(r => r.FindAll(), Times.AtLeastOnce);
_mockRepository.Verify(r => r.FindById(It.IsAny<long>()), Times.AtMost(3));
_mockRepository.Verify(r => r.Delete(It.IsAny<User>()), Times.Never);

// Verify async method
_mockRepository.Verify(r => r.SaveAsync(user), Times.Once);

// Verify getter/setter
_mockRepository.VerifyGet(r => r.ConnectionString, Times.Once);
_mockRepository.VerifySet(r => r.ConnectionString = It.IsAny<string>());

// Verify no other calls
_mockRepository.VerifyNoOtherCalls();
```

### Property and Event Mocking

```csharp
// Mock property
var mockConfig = new Mock<IConfiguration>();
mockConfig.SetupGet(c => c.ConnectionString)
          .Returns("Server=localhost");

// Mock property with setter
mockConfig.SetupProperty(c => c.Timeout, 30);
mockConfig.Object.Timeout = 60;
Assert.Equal(60, mockConfig.Object.Timeout);

// Mock event
var mockPublisher = new Mock<IEventPublisher>();
mockPublisher.Setup(p => p.Publish(It.IsAny<Event>()))
             .Raises(p => p.EventPublished += null, new EventArgs());

var eventRaised = false;
mockPublisher.Object.EventPublished += (s, e) => eventRaised = true;
mockPublisher.Object.Publish(new Event());
Assert.True(eventRaised);
```

## Phase 3: Mocking with NSubstitute

### Understanding NSubstitute

NSubstitute provides a more fluent mocking syntax:

```bash
dotnet add package NSubstitute
```

**Creating Substitutes**:
```csharp
using NSubstitute;

public class UserServiceTests
{
    private readonly IUserRepository _repository;
    private readonly IEmailService _emailService;
    private readonly UserService _userService;

    public UserServiceTests()
    {
        _repository = Substitute.For<IUserRepository>();
        _emailService = Substitute.For<IEmailService>();
        _userService = new UserService(_repository, _emailService);
    }

    [Fact]
    public void ShouldCreateUser()
    {
        var user = new User("alice", "alice@test.com");
        _repository.Save(user).Returns(user);
        _emailService.SendWelcome(user).Returns(true);

        var result = _userService.CreateUser(user);

        Assert.NotNull(result);
        _repository.Received(1).Save(user);
        _emailService.Received(1).SendWelcome(user);
    }
}
```

**NSubstitute Features**:
```csharp
// Return values
_repository.FindById(1).Returns(user);

// Multiple return values
_api.FetchStatus().Returns(Status.Pending, Status.Complete);

// Async returns
_repository.FindByIdAsync(1).Returns(Task.FromResult(user));

// Throws exception
_database.Connect().Returns(x => throw new Exception("Failed"));

// Argument matching
_repository.FindById(Arg.Any<long>()).Returns(user);
_repository.Save(Arg.Is<User>(u => u.Age > 18)).Returns(user);

// Verification
_repository.Received().Save(user);
_repository.Received(2).FindAll();
_repository.DidNotReceive().Delete(Arg.Any<User>());

// Clear received calls
_repository.ClearReceivedCalls();
```

## Phase 4: Mocking External Dependencies

### Mocking HTTP with HttpClient

```csharp
public class HttpClientTests
{
    [Fact]
    public async Task ShouldMockHttpClient()
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>()
            )
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent("{\"id\":1,\"name\":\"alice\"}")
            });

        var httpClient = new HttpClient(mockHandler.Object);
        var apiClient = new ApiClient(httpClient);

        var user = await apiClient.GetUserAsync(1);

        Assert.Equal("alice", user.Name);
    }
}
```

### Mocking Entity Framework

```csharp
public class UserRepositoryTests
{
    [Fact]
    public void ShouldQueryUsers()
    {
        var users = new List<User>
        {
            new User { Id = 1, Username = "alice" },
            new User { Id = 2, Username = "bob" }
        }.AsQueryable();

        var mockSet = new Mock<DbSet<User>>();
        mockSet.As<IQueryable<User>>().Setup(m => m.Provider).Returns(users.Provider);
        mockSet.As<IQueryable<User>>().Setup(m => m.Expression).Returns(users.Expression);
        mockSet.As<IQueryable<User>>().Setup(m => m.ElementType).Returns(users.ElementType);
        mockSet.As<IQueryable<User>>().Setup(m => m.GetEnumerator()).Returns(users.GetEnumerator());

        var mockContext = new Mock<AppDbContext>();
        mockContext.Setup(c => c.Users).Returns(mockSet.Object);

        var repository = new UserRepository(mockContext.Object);
        var result = repository.GetAll();

        Assert.Equal(2, result.Count);
    }
}
```

### Mocking File System

```csharp
public class FileServiceTests
{
    [Fact]
    public void ShouldReadFile()
    {
        var mockFileSystem = new Mock<IFileSystem>();
        mockFileSystem.Setup(fs => fs.ReadAllText("config.txt"))
                      .Returns("setting=value");

        var service = new FileService(mockFileSystem.Object);
        var config = service.ReadConfig("config.txt");

        Assert.Equal("value", config["setting"]);
    }

    [Fact]
    public void ShouldWriteFile()
    {
        var mockFileSystem = new Mock<IFileSystem>();

        var service = new FileService(mockFileSystem.Object);
        service.WriteLog("test.log", "test message");

        mockFileSystem.Verify(
            fs => fs.WriteAllText("test.log", "test message"),
            Times.Once
        );
    }
}
```

### Mocking DateTime

```csharp
public interface IDateTimeProvider
{
    DateTime Now { get; }
    DateTime UtcNow { get; }
}

public class TimestampServiceTests
{
    [Fact]
    public void ShouldMockDateTime()
    {
        var mockDateTime = new Mock<IDateTimeProvider>();
        var fixedDate = new DateTime(2024, 1, 15, 12, 0, 0);
        mockDateTime.Setup(d => d.UtcNow).Returns(fixedDate);

        var service = new TimestampService(mockDateTime.Object);
        var timestamp = service.GetCurrentTimestamp();

        Assert.Equal("2024-01-15T12:00:00", timestamp);
    }
}
```

## Phase 5: Test Data with Bogus

### Using Bogus Library

```bash
dotnet add package Bogus
```

```csharp
using Bogus;

public class UserFactoryWithBogus
{
    private readonly Faker<User> _faker;

    public UserFactoryWithBogus()
    {
        _faker = new Faker<User>()
            .RuleFor(u => u.Id, f => f.IndexFaker)
            .RuleFor(u => u.Username, f => f.Internet.UserName())
            .RuleFor(u => u.Email, f => f.Internet.Email())
            .RuleFor(u => u.FirstName, f => f.Name.FirstName())
            .RuleFor(u => u.LastName, f => f.Name.LastName())
            .RuleFor(u => u.Age, f => f.Random.Number(18, 80))
            .RuleFor(u => u.IsActive, f => f.Random.Bool());
    }

    public User Generate() => _faker.Generate();

    public List<User> Generate(int count) => _faker.Generate(count);
}

// Usage
[Fact]
public void ShouldCreateRandomUsers()
{
    var factory = new UserFactoryWithBogus();
    var users = factory.Generate(10);

    Assert.Equal(10, users.Count);
    Assert.All(users, u => Assert.InRange(u.Age, 18, 80));
}
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Class-Level Fixtures** (IClassFixture):

- [fixture_name]: [purpose, setup, teardown]

**Test-Level Setup** (Constructor/Dispose):

- [fixture_name]: [purpose, when to use]

**Fixture Factories**:

- [factory_name]: [creates what, customization options]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Tool (Moq/NSubstitute) | Reason |
|------------|------------------|------------------------|--------|
| [API/Service] | [mock/stub] | [tool] | [justification] |

**Mock Configurations**:
```csharp
// Example mock setup
private readonly Mock<IApiClient> _mockApiClient;

public TestClass()
{
    _mockApiClient = new Mock<IApiClient>();
    _mockApiClient.Setup(a => a.Get(It.IsAny<string>()))
                  .ReturnsAsync(new Response { Status = 200 });
}
```

### Test Data Factories
**Factory Classes**:

- UserFactory: [customization options]

- OrderFactory: [customization options]

**Builder Classes**:

- [builder_name]: [purpose, fluent interface methods]

### Usage Examples
```csharp
// Example test using fixtures and mocks
public class UserRegistrationTests
{
    private readonly Mock<IEmailService> _mockEmailService;
    private readonly UserService _userService;
    private readonly UserFactory _userFactory;

    public UserRegistrationTests()
    {
        _mockEmailService = new Mock<IEmailService>();
        _userService = new UserService(_mockEmailService.Object);
        _userFactory = new UserFactory();
    }

    [Fact]
    public void ShouldRegisterUser()
    {
        var userData = _userFactory.Create(u => u.Username = "alice");
        _mockEmailService.Setup(e => e.SendWelcome(It.IsAny<User>()))
                        .Returns(true);

        var result = _userService.RegisterUser(userData);

        Assert.NotNull(result.Id);
        _mockEmailService.Verify(e => e.SendWelcome(userData), Times.Once);
    }
}
```

### Best Practices Implemented

- [ ] Fixtures use appropriate scopes (class/collection)

- [ ] Mocks are used for external dependencies only

- [ ] Test data factories provide flexible data creation

- [ ] Mock verification ensures correct behavior

- [ ] Disposal patterns followed for cleanup

- [ ] Interface-based mocking used

### Common Pitfalls Avoided

- Over-mocking simple DTOs

- Not disposing fixtures properly

- Complex mock setups that obscure test intent

- Mocking concrete classes instead of interfaces

- Testing mock behavior instead of real code

### Next Steps

- [ ] Implement remaining fixtures for integration tests

- [ ] Add factories for all domain models

- [ ] Document fixture usage for team

- [ ] Set up shared mock configurations

- [ ] Review mock coverage and necessity

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Comprehensive fixture setup** using xUnit/NUnit patterns

2. **Mock configurations** for external dependencies

3. **Test data factories** for domain objects

4. **Builder patterns** for complex test data

5. **Usage documentation** with examples

6. **Best practices guide** for Moq and NSubstitute

7. **Fixture and mock catalog** for easy reference
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
