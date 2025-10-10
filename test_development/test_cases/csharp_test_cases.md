# C# Test Case Development

## Objective
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using xUnit, NUnit, or MSTest frameworks.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── test_cases/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:

- Create `tests/{phase}/` directory in repository root if it doesn't exist

- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:

- `test_files/` - Actual test implementation files

- `test_data/` - Test fixtures, mock data, sample inputs

- `test_reports/` - Test execution reports, coverage reports, performance results

- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Test Coverage
- [ ] Happy path scenarios tested
- [ ] Edge cases and boundaries covered
- [ ] Error conditions validated
- [ ] Input validation tested
- [ ] State transitions verified
- [ ] Regression tests added for bugs
- [ ] Async methods properly tested

### Test Quality
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Test names clearly describe what is tested
- [ ] Tests are isolated and independent
- [ ] Tests execute quickly (<1s for unit tests)
- [ ] Assertions are specific and meaningful
- [ ] No test interdependencies
- [ ] Proper use of SetUp/TearDown or constructors

### Test Organization
- [ ] Tests grouped logically by feature/class
- [ ] Related tests organized in test classes
- [ ] Theory/TestCase attributes used for parametrized tests
- [ ] Setup and teardown properly implemented
- [ ] Test documentation provided
- [ ] Mocks and fakes used appropriately

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Test Case Development

Please develop comprehensive test cases for this C# code following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Test Case Planning

1. **Analyze Code to Test**
   - Identify all public methods and classes
   - Document expected behavior
   - List input parameters and types
   - Define expected outputs
   - Note side effects (database, files, external services)
   - Identify exceptions that should be thrown

2. **Identify Test Scenarios**

   **Happy Path**:
   - Normal operation with valid inputs
   - Expected use cases
   - Successful execution flows
   - Valid object state transitions

   **Edge Cases**:
   - Boundary values (int.MaxValue, int.MinValue, 0)
   - Empty collections (empty List, Dictionary, Array)
   - Null values
   - Large data sets
   - Special characters in strings
   - Concurrent access scenarios

   **Error Conditions**:
   - Invalid inputs
   - Missing required parameters
   - ArgumentException scenarios
   - NullReferenceException scenarios
   - Business rule violations
   - External dependency failures

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation (xUnit)

### AAA Pattern (Arrange-Act-Assert)

Follow this structure for clear, maintainable tests:

```csharp
using Xunit;
using Moq;
using FluentAssertions;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace MyApp.Tests.Unit
{
    /// <summary>
    /// Unit tests for UserService class.
    ///
    /// Tests cover user creation, validation, and retrieval operations.
    /// </summary>
    public class UserServiceTests : IDisposable
    {
        private readonly UserService _userService;
        private readonly Mock<IUserRepository> _mockRepository;
        private readonly Mock<IEmailService> _mockEmailService;

        public UserServiceTests()
        {
            _mockRepository = new Mock<IUserRepository>();
            _mockEmailService = new Mock<IEmailService>();
            _userService = new UserService(_mockRepository.Object, _mockEmailService.Object);
        }

        public void Dispose()
        {
            // Clean up resources if needed
        }

        [Fact]
        public void CreateUser_WithValidData_ReturnsUserId()
        {
            // Arrange - Set up test data and mocks
            var user = new User
            {
                Name = "Alice",
                Email = "alice@example.com",
                Age = 30
            };
            var expectedUserId = 123;
            _mockRepository.Setup(r => r.Save(It.IsAny<User>()))
                .Returns(expectedUserId);

            // Act - Execute the method being tested
            var actualUserId = _userService.CreateUser(user);

            // Assert - Verify the result matches expectations
            actualUserId.Should().Be(expectedUserId);
            _mockRepository.Verify(r => r.Save(user), Times.Once);
            _mockEmailService.Verify(e => e.SendWelcomeEmail(user.Email), Times.Once);
        }

        [Fact]
        public void CreateUser_WithInvalidEmail_ThrowsArgumentException()
        {
            // Arrange
            var user = new User
            {
                Name = "Bob",
                Email = "not-an-email",
                Age = 25
            };

            // Act
            Action act = () => _userService.CreateUser(user);

            // Assert - Use FluentAssertions for exception testing
            act.Should().Throw<ArgumentException>()
                .WithMessage("*Invalid email format*");

            _mockRepository.Verify(r => r.Save(It.IsAny<User>()), Times.Never);
        }

        [Fact]
        public void CreateUser_WithoutAge_UsesDefaultAge()
        {
            // Arrange
            var user = new User
            {
                Name = "Charlie",
                Email = "charlie@example.com"
            };
            var expectedDefaultAge = 18;

            // Act
            _userService.CreateUser(user);

            // Assert
            user.Age.Should().Be(expectedDefaultAge);
        }

        [Fact]
        public async Task CreateUserAsync_WithValidData_ReturnsUserId()
        {
            // Arrange
            var user = new User { Name = "Dave", Email = "dave@example.com" };
            _mockRepository.Setup(r => r.SaveAsync(It.IsAny<User>()))
                .ReturnsAsync(456);

            // Act
            var userId = await _userService.CreateUserAsync(user);

            // Assert
            userId.Should().Be(456);
        }
    }
}
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `MethodName_Condition_ExpectedResult`

**Examples**:
```csharp
// Good test names
[Fact]
public void AddUser_WithValidData_ReturnsUserId() { }

[Fact]
public void AddUser_WithDuplicateEmail_ThrowsValidationException() { }

[Fact]
public void GetUser_WithNonexistentId_ReturnsNull() { }

[Fact]
public void UpdateUser_WithInvalidAge_ThrowsArgumentException() { }

// Poor test names (avoid these)
[Fact]
public void TestAddUser() { }              // Too generic

[Fact]
public void Test1() { }                    // Non-descriptive

[Fact]
public void TestError() { }                // Unclear what error

[Fact]
public void TestEdgeCase() { }             // Vague
```

### Testing Different Scenarios

**1. Testing Return Values**:
```csharp
public class CalculatorTests
{
    private readonly Calculator _calculator;

    public CalculatorTests()
    {
        _calculator = new Calculator();
    }

    [Fact]
    public void CalculateTotal_WithNumbers_ReturnsSum()
    {
        // Arrange
        var items = new[] { 10.0, 20.0, 30.0 };

        // Act
        var result = _calculator.CalculateTotal(items);

        // Assert
        result.Should().Be(60.0);
    }

    [Fact]
    public void CalculateTotal_WithEmptyArray_ReturnsZero()
    {
        // Arrange
        var items = Array.Empty<double>();

        // Act
        var result = _calculator.CalculateTotal(items);

        // Assert
        result.Should().Be(0.0);
    }

    [Fact]
    public void CalculateTotal_WithNegativeValues_ReturnsCorrectSum()
    {
        // Arrange
        var items = new[] { 10.0, -5.0, 15.0 };

        // Act
        var result = _calculator.CalculateTotal(items);

        // Assert
        result.Should().Be(20.0);
    }
}
```

**2. Testing Exceptions**:
```csharp
public class MathOperationsTests
{
    [Fact]
    public void Divide_ByZero_ThrowsDivideByZeroException()
    {
        // Arrange
        var math = new MathOperations();

        // Act
        Action act = () => math.Divide(10, 0);

        // Assert
        act.Should().Throw<DivideByZeroException>();
    }

    [Fact]
    public void ParseDate_WithInvalidFormat_ThrowsArgumentExceptionWithMessage()
    {
        // Arrange
        var parser = new DateParser();

        // Act
        Action act = () => parser.Parse("not-a-date");

        // Assert
        act.Should().Throw<ArgumentException>()
            .WithMessage("*Invalid date format*");
    }

    [Fact]
    public void ProcessData_WithNullInput_ThrowsArgumentNullException()
    {
        // Arrange
        var processor = new DataProcessor();

        // Act
        Action act = () => processor.Process(null);

        // Assert
        act.Should().Throw<ArgumentNullException>()
            .And.ParamName.Should().Be("data");
    }
}
```

**3. Testing Async Operations**:
```csharp
public class AsyncOperationsTests
{
    [Fact]
    public async Task FetchUserAsync_WithValidId_ReturnsUser()
    {
        // Arrange
        var mockRepository = new Mock<IUserRepository>();
        var expectedUser = new User { Id = 1, Name = "Alice" };
        mockRepository.Setup(r => r.GetByIdAsync(1))
            .ReturnsAsync(expectedUser);
        var service = new UserService(mockRepository.Object);

        // Act
        var user = await service.FetchUserAsync(1);

        // Assert
        user.Should().BeEquivalentTo(expectedUser);
    }

    [Fact]
    public async Task FetchUserAsync_WhenRepositoryThrows_ThrowsException()
    {
        // Arrange
        var mockRepository = new Mock<IUserRepository>();
        mockRepository.Setup(r => r.GetByIdAsync(It.IsAny<int>()))
            .ThrowsAsync(new DatabaseException("Connection failed"));
        var service = new UserService(mockRepository.Object);

        // Act
        Func<Task> act = async () => await service.FetchUserAsync(1);

        // Assert
        await act.Should().ThrowAsync<DatabaseException>()
            .WithMessage("Connection failed");
    }
}
```

**4. Testing Side Effects and Mocks**:
```csharp
public class OrderServiceTests
{
    private readonly Mock<IOrderRepository> _mockRepository;
    private readonly Mock<IInventoryService> _mockInventory;
    private readonly Mock<IEmailService> _mockEmail;
    private readonly OrderService _orderService;

    public OrderServiceTests()
    {
        _mockRepository = new Mock<IOrderRepository>();
        _mockInventory = new Mock<IInventoryService>();
        _mockEmail = new Mock<IEmailService>();
        _orderService = new OrderService(
            _mockRepository.Object,
            _mockInventory.Object,
            _mockEmail.Object
        );
    }

    [Fact]
    public void CreateOrder_WithValidData_SavesAndUpdatesInventory()
    {
        // Arrange
        var order = new Order();
        order.AddItem(new OrderItem(1, 5));

        // Act
        _orderService.CreateOrder(order);

        // Assert
        _mockRepository.Verify(r => r.Save(order), Times.Once);
        _mockInventory.Verify(i => i.DecrementStock(1, 5), Times.Once);
    }

    [Fact]
    public void CreateOrder_Success_SendsConfirmationEmail()
    {
        // Arrange
        var order = new Order { CustomerEmail = "customer@example.com" };

        // Act
        _orderService.CreateOrder(order);

        // Assert
        _mockEmail.Verify(
            e => e.SendOrderConfirmation(
                "customer@example.com",
                It.IsAny<Order>()
            ),
            Times.Once
        );
    }
}
```

**5. Testing State Changes**:
```csharp
public class UserAccountTests
{
    [Fact]
    public void Login_WithValidCredentials_UpdatesStatusToActive()
    {
        // Arrange
        var user = new User("alice", "password")
        {
            Status = UserStatus.Inactive
        };

        // Act
        user.Login("password");

        // Assert
        user.Status.Should().Be(UserStatus.Active);
        user.LastLoginTime.Should().NotBeNull();
    }

    [Fact]
    public void CancelOrder_Success_RestoresInventory()
    {
        // Arrange
        var inventory = new Inventory();
        inventory.AddStock(1, 100);
        var order = new Order();
        order.AddItem(new OrderItem(1, 5));
        inventory.ReserveStock(1, 5);

        // Act
        order.Cancel();
        inventory.ReleaseReservation(1, 5);

        // Assert
        inventory.GetAvailableStock(1).Should().Be(100);
    }
}
```

### Parametrized Tests (Using Theory)

Test multiple scenarios efficiently:

```csharp
public class ValidationTests
{
    [Theory]
    [InlineData(0, "zero")]
    [InlineData(1, "one")]
    [InlineData(5, "five")]
    [InlineData(10, "ten")]
    public void NumberToWord_WithInput_ReturnsExpectedWord(int input, string expected)
    {
        // Act
        var result = NumberConverter.ToWord(input);

        // Assert
        result.Should().Be(expected);
    }

    [Theory]
    [InlineData("")]
    [InlineData("not-an-email")]
    [InlineData("@example.com")]
    [InlineData("user@")]
    [InlineData("user @example.com")]
    public void ValidateEmail_WithInvalidFormats_ThrowsException(string email)
    {
        // Arrange
        var validator = new EmailValidator();

        // Act
        Action act = () => validator.Validate(email);

        // Assert
        act.Should().Throw<ArgumentException>();
    }

    [Theory]
    [InlineData(17, false)]
    [InlineData(18, true)]
    [InlineData(21, true)]
    [InlineData(100, true)]
    public void IsAdult_WithVariousAges_ReturnsExpectedResult(int age, bool expected)
    {
        // Act
        var result = AgeChecker.IsAdult(age);

        // Assert
        result.Should().Be(expected);
    }

    [Theory]
    [MemberData(nameof(GetUserTestData))]
    public void CreateUser_WithComplexData_WorksCorrectly(User user, bool shouldSucceed)
    {
        // Arrange
        var service = new UserService();

        if (shouldSucceed)
        {
            // Act
            var result = service.CreateUser(user);

            // Assert
            result.Should().BeGreaterThan(0);
        }
        else
        {
            // Act
            Action act = () => service.CreateUser(user);

            // Assert
            act.Should().Throw<ArgumentException>();
        }
    }

    public static IEnumerable<object[]> GetUserTestData()
    {
        yield return new object[] { new User("Alice", "alice@example.com"), true };
        yield return new object[] { new User("", "bob@example.com"), false };
        yield return new object[] { new User("Charlie", "invalid-email"), false };
    }
}
```

### Testing Edge Cases and Boundaries

```csharp
public class BoundaryTests
{
    public class BoundaryConditions
    {
        private readonly ValueProcessor _processor;

        public BoundaryConditions()
        {
            _processor = new ValueProcessor();
        }

        [Fact]
        public void ProcessValue_WithMinimum_ReturnsExpectedResult()
        {
            // Act
            var result = _processor.ProcessValue(0);

            // Assert
            result.Should().Be(expectedMin);
        }

        [Fact]
        public void ProcessValue_WithMaximum_ReturnsExpectedResult()
        {
            // Act
            var result = _processor.ProcessValue(100);

            // Assert
            result.Should().Be(expectedMax);
        }

        [Fact]
        public void ProcessValue_BelowMinimum_ThrowsArgumentOutOfRangeException()
        {
            // Act
            Action act = () => _processor.ProcessValue(-1);

            // Assert
            act.Should().Throw<ArgumentOutOfRangeException>();
        }

        [Fact]
        public void ProcessValue_AboveMaximum_ThrowsArgumentOutOfRangeException()
        {
            // Act
            Action act = () => _processor.ProcessValue(101);

            // Assert
            act.Should().Throw<ArgumentOutOfRangeException>();
        }
    }

    public class CollectionEdgeCases
    {
        private readonly CollectionProcessor _processor;

        public CollectionEdgeCases()
        {
            _processor = new CollectionProcessor();
        }

        [Fact]
        public void ProcessCollection_WithEmptyList_ReturnsEmptyList()
        {
            // Arrange
            var emptyList = new List<int>();

            // Act
            var result = _processor.ProcessCollection(emptyList);

            // Assert
            result.Should().BeEmpty();
        }

        [Fact]
        public void ProcessCollection_WithSingleElement_ProcessesCorrectly()
        {
            // Arrange
            var singleItemList = new List<int> { 1 };

            // Act
            var result = _processor.ProcessCollection(singleItemList);

            // Assert
            result.Should().HaveCount(1);
        }

        [Fact]
        public void ProcessCollection_WithLargeList_CompletesInReasonableTime()
        {
            // Arrange
            var largeList = Enumerable.Range(0, 10000).ToList();

            // Act
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            var result = _processor.ProcessCollection(largeList);
            stopwatch.Stop();

            // Assert
            result.Should().HaveCount(10000);
            stopwatch.ElapsedMilliseconds.Should().BeLessThan(1000);
        }

        [Fact]
        public void ProcessValue_WithNull_ThrowsArgumentNullException()
        {
            // Act
            Action act = () => _processor.ProcessValue(null);

            // Assert
            act.Should().Throw<ArgumentNullException>();
        }
    }
}
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```csharp
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace MyApp.Tests.Integration
{
    /// <summary>
    /// Integration tests for user registration workflow.
    ///
    /// Tests the complete user registration process including
    /// validation, database storage, and email notification.
    /// </summary>
    public class UserRegistrationIntegrationTests : IDisposable
    {
        private readonly ApplicationDbContext _dbContext;
        private readonly UserService _userService;
        private readonly TestEmailService _emailService;

        public UserRegistrationIntegrationTests()
        {
            var options = new DbContextOptionsBuilder<ApplicationDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .Options;

            _dbContext = new ApplicationDbContext(options);
            _emailService = new TestEmailService();
            var repository = new UserRepository(_dbContext);
            _userService = new UserService(repository, _emailService);
        }

        public void Dispose()
        {
            _dbContext.Database.EnsureDeleted();
            _dbContext.Dispose();
        }

        [Fact]
        public void RegisterUser_WithValidData_CreatesEntryAndSendsEmail()
        {
            // Arrange
            var request = new UserRegistrationRequest
            {
                Username = "newuser",
                Email = "newuser@example.com",
                Password = "SecurePass123!"
            };

            // Act
            var userId = _userService.RegisterUser(request);

            // Assert - Verify database entry
            var user = _dbContext.Users.Find(userId);
            user.Should().NotBeNull();
            user.Username.Should().Be("newuser");
            user.Email.Should().Be("newuser@example.com");
            user.Password.Should().NotBe("SecurePass123!"); // Should be hashed

            // Assert - Verify email sent
            _emailService.SentEmails.Should().HaveCount(1);
            var welcomeEmail = _emailService.SentEmails[0];
            welcomeEmail.To.Should().Be("newuser@example.com");
            welcomeEmail.Subject.Should().Contain("Welcome");
        }

        [Fact]
        public void RegisterUser_WithDuplicateUsername_ThrowsException()
        {
            // Arrange - Create existing user
            var firstRequest = new UserRegistrationRequest
            {
                Username = "alice",
                Email = "alice@example.com",
                Password = "Pass123!"
            };
            _userService.RegisterUser(firstRequest);

            // Try to create duplicate
            var duplicateRequest = new UserRegistrationRequest
            {
                Username = "alice",
                Email = "different@example.com",
                Password = "Pass123!"
            };

            // Act
            Action act = () => _userService.RegisterUser(duplicateRequest);

            // Assert
            act.Should().Throw<DuplicateUsernameException>();
        }
    }
}
```

### ASP.NET Core API Integration Tests

```csharp
using Microsoft.AspNetCore.Mvc.Testing;
using System.Net.Http.Json;
using Xunit;

public class UserApiIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UserApiIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CreateUser_WithValidData_Returns201()
    {
        // Arrange
        var userData = new
        {
            Username = "testuser",
            Email = "test@example.com",
            Password = "SecurePass123!"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/users", userData);

        // Assert
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.Created);
        var createdUser = await response.Content.ReadFromJsonAsync<UserDto>();
        createdUser.Should().NotBeNull();
        createdUser.Username.Should().Be("testuser");
    }

    [Fact]
    public async Task GetUser_WithExistingId_ReturnsUserData()
    {
        // Arrange - Create user first
        var userId = await CreateTestUserAsync("alice", "alice@example.com");

        // Act
        var response = await _client.GetAsync($"/api/users/{userId}");

        // Assert
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.OK);
        var user = await response.Content.ReadFromJsonAsync<UserDto>();
        user.Id.Should().Be(userId);
        user.Username.Should().Be("alice");
    }
}
```

## Phase 4: End-to-End Test Implementation

E2E tests validate complete workflows:

```csharp
/// <summary>
/// End-to-end tests for e-commerce checkout flow.
///
/// Tests the complete user journey from adding items to cart
/// through payment and order confirmation.
/// </summary>
public class CheckoutWorkflowE2ETests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public CheckoutWorkflowE2ETests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CompletePurchase_FromCartToConfirmation_Success()
    {
        // Login
        var loginResponse = await _client.PostAsJsonAsync("/api/auth/login", new
        {
            Username = "testuser",
            Password = "password123"
        });
        var authToken = await loginResponse.Content.ReadAsStringAsync();
        _client.DefaultRequestHeaders.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", authToken);

        // Add product to cart
        var addToCartResponse = await _client.PostAsJsonAsync("/api/cart/items", new
        {
            ProductId = 1,
            Quantity = 1
        });
        addToCartResponse.StatusCode.Should().Be(System.Net.HttpStatusCode.OK);

        // Create order
        var orderResponse = await _client.PostAsync("/api/orders", null);
        orderResponse.StatusCode.Should().Be(System.Net.HttpStatusCode.Created);

        var order = await orderResponse.Content.ReadFromJsonAsync<OrderDto>();
        order.Should().NotBeNull();
        order.Status.Should().Be("Pending");
        order.Items.Should().HaveCount(1);
    }
}
```

## Phase 5: Test Best Practices

### 1. Test Independence

```csharp
// GOOD - Tests are independent
public class UserServiceTests : IDisposable
{
    private readonly ApplicationDbContext _dbContext;
    private readonly UserService _userService;

    public UserServiceTests()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        _dbContext = new ApplicationDbContext(options);
        _userService = new UserService(_dbContext);
    }

    public void Dispose()
    {
        _dbContext.Database.EnsureDeleted();
        _dbContext.Dispose();
    }

    [Fact]
    public void CreateUser_Success()
    {
        var user = _userService.CreateUser("alice", "alice@example.com");
        user.Id.Should().BeGreaterThan(0);
    }
}

// BAD - Tests depend on each other
public class UserServiceTests
{
    private int _userId; // Shared state!

    [Fact]
    public void Test1_CreateUser()
    {
        var user = _userService.CreateUser("alice", "alice@example.com");
        _userId = user.Id; // Setting shared state
    }

    [Fact]
    public void Test2_DeleteUser()
    {
        _userService.DeleteUser(_userId); // Depends on Test1
    }
}
```

### 2. Clear Assertions

```csharp
// GOOD - Specific, clear assertions
[Fact]
public void CreateUser_WithValidData_ReturnsUserWithCorrectProperties()
{
    // Act
    var user = _userService.CreateUser("alice", "alice@example.com", 30);

    // Assert
    user.Username.Should().Be("alice");
    user.Email.Should().Be("alice@example.com");
    user.Age.Should().Be(30);
    user.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
    user.IsActive.Should().BeTrue();
}

// BAD - Vague or missing assertions
[Fact]
public void CreateUser_Success()
{
    var user = _userService.CreateUser("alice", "alice@example.com", 30);
    user.Should().NotBeNull(); // Too vague
    user.Username.Should().NotBeNullOrEmpty(); // Checks existence, not value
}
```

## Output Format

Please provide comprehensive test cases with the following structure:

### Test Coverage Summary
- **Total Test Cases**: [count]
- **Unit Tests**: [count]
- **Integration Tests**: [count]
- **E2E Tests**: [count]
- **Test Types**:
  - Happy path: [count]
  - Edge cases: [count]
  - Error conditions: [count]

### Test Case Implementation

For each class/module:

**Class**: `[ClassName]`
**Test File**: `tests/[ClassName]Tests.cs`

**Test Cases**:
1. `MethodName_WithValidData_ReturnsExpectedResult`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [result]
   - **Type**: [unit/integration/e2e]

2. `MethodName_WithInvalidInput_ThrowsException`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [exception type]
   - **Type**: [unit/integration/e2e]

### Test Execution Results
```bash
# Run tests
dotnet test

# Run with coverage
dotnet test /p:CollectCoverage=true

# Expected output
Total tests: 25
     Passed: 25
     Failed: 0
```

### Coverage Gaps Identified
- [ ] [Method]: Missing tests for [scenario]
- [ ] [Method]: Need edge case tests for [condition]
- [ ] [Method]: Exception handling not tested

### Test Quality Metrics
- **Average test execution time**: [milliseconds]
- **Tests following AAA pattern**: [percentage]
- **Tests with clear names**: [percentage]
- **Independent tests**: [percentage]

### Next Steps
- [ ] Implement remaining test cases for coverage gaps
- [ ] Add performance tests for critical methods
- [ ] Set up test containers for integration tests
- [ ] Configure CI/CD pipeline
- [ ] Review and refactor slow tests

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

1. **Test case matrix** documenting all scenarios
2. **Complete test implementations** with clear AAA structure
3. **Parametrized tests** for multiple scenarios
4. **Integration and E2E tests** for workflows
5. **Test coverage report** showing gaps
6. **Execution instructions** for running tests
7. **Quality metrics** and improvement suggestions
