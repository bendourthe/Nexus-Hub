# C# Test Structure & Infrastructure

## Objective
Design and implement a robust test infrastructure with optimal framework configuration (xUnit, NUnit, or MSTest), logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices in .NET/C# projects.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── test_structure/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/test_structure/` subdirectory for this testing phase
- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:
- `test_files/` - Actual test implementation files
- `test_data/` - Test fixtures, mock data, sample inputs
- `test_reports/` - Test execution reports, coverage reports, performance results
- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Test Framework Setup
- [ ] Test framework selected (xUnit/NUnit/MSTest)
- [ ] NuGet packages installed and configured
- [ ] Test discovery rules established
- [ ] Parallel execution configured
- [ ] Test settings configured

### Directory Structure
- [ ] Standard .NET test layout implemented
- [ ] Test type separation (unit/integration/e2e) organized
- [ ] Naming conventions documented
- [ ] Resource directories created
- [ ] Test categories configured

### Fixture Infrastructure
- [ ] Test class constructors/Setup methods established
- [ ] IClassFixture/ICollectionFixture configured
- [ ] Fixture scopes defined appropriately
- [ ] Fixture factories implemented
- [ ] Common fixtures centralized

### Test Utilities
- [ ] Custom assertions created
- [ ] Test data builders implemented
- [ ] Helper classes established
- [ ] Object mothers defined
- [ ] Utility documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Test Infrastructure Setup

Please design and implement a comprehensive test infrastructure for this C#/.NET project following this protocol:

## Phase 1: Framework Selection & Configuration

1. **Test Framework Analysis**
   - **Current State**: Document existing test setup if any
   - **Framework Recommendation**:
     - **xUnit** (recommended): Modern, extensible, no static state
     - **NUnit**: Feature-rich, well-established, FluentAssertions
     - **MSTest**: Microsoft official, Visual Studio integrated
   - **Rationale**: Justify framework choice based on project needs

2. **Install Core Testing Dependencies**

   **xUnit** (.csproj):
   ```xml
   <ItemGroup>
       <!-- xUnit framework -->
       <PackageReference Include="xunit" Version="2.6.3" />
       <PackageReference Include="xunit.runner.visualstudio" Version="2.5.5">
           <PrivateAssets>all</PrivateAssets>
           <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
       </PackageReference>

       <!-- Microsoft Test SDK -->
       <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />

       <!-- Mocking -->
       <PackageReference Include="Moq" Version="4.20.70" />
       <PackageReference Include="NSubstitute" Version="5.1.0" />

       <!-- Assertions -->
       <PackageReference Include="FluentAssertions" Version="6.12.0" />

       <!-- Test data -->
       <PackageReference Include="AutoFixture" Version="4.18.0" />
       <PackageReference Include="AutoFixture.Xunit2" Version="4.18.0" />
       <PackageReference Include="Bogus" Version="34.0.2" />

       <!-- Code coverage -->
       <PackageReference Include="coverlet.collector" Version="6.0.0">
           <PrivateAssets>all</PrivateAssets>
           <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
       </PackageReference>
   </ItemGroup>
   ```

   **NUnit** (.csproj):
   ```xml
   <ItemGroup>
       <PackageReference Include="NUnit" Version="4.0.1" />
       <PackageReference Include="NUnit3TestAdapter" Version="4.5.0" />
       <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
       <PackageReference Include="Moq" Version="4.20.70" />
       <PackageReference Include="FluentAssertions" Version="6.12.0" />
       <PackageReference Include="AutoFixture" Version="4.18.0" />
       <PackageReference Include="AutoFixture.NUnit3" Version="4.18.0" />
   </ItemGroup>
   ```

   **MSTest** (.csproj):
   ```xml
   <ItemGroup>
       <PackageReference Include="MSTest.TestFramework" Version="3.2.0" />
       <PackageReference Include="MSTest.TestAdapter" Version="3.2.0" />
       <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
       <PackageReference Include="Moq" Version="4.20.70" />
       <PackageReference Include="FluentAssertions" Version="6.12.0" />
   </ItemGroup>
   ```

3. **Configuration File Setup**

   **xUnit Configuration** (xunit.runner.json):
   ```json
   {
     "$schema": "https://xunit.net/schema/current/xunit.runner.schema.json",
     "methodDisplay": "method",
     "methodDisplayOptions": "all",
     "diagnosticMessages": true,
     "internalDiagnosticMessages": false,
     "maxParallelThreads": 4,
     "parallelizeAssembly": true,
     "parallelizeTestCollections": true,
     "preEnumerateTheories": false,
     "shadowCopy": false
   }
   ```

   **NUnit Configuration** (.runsettings):
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <RunSettings>
     <NUnit>
       <NumberOfTestWorkers>4</NumberOfTestWorkers>
       <DefaultTimeout>10000</DefaultTimeout>
       <InternalTraceLevel>Off</InternalTraceLevel>
     </NUnit>
     <RunConfiguration>
       <MaxCpuCount>4</MaxCpuCount>
       <ResultsDirectory>./TestResults</ResultsDirectory>
       <TargetPlatform>x64</TargetPlatform>
     </RunConfiguration>
     <DataCollectionRunSettings>
       <DataCollectors>
         <DataCollector friendlyName="Code Coverage" />
       </DataCollectors>
     </DataCollectionRunSettings>
   </RunSettings>
   ```

   **Directory.Build.props** (Solution-level):
   ```xml
   <Project>
     <PropertyGroup>
       <LangVersion>latest</LangVersion>
       <Nullable>enable</Nullable>
       <ImplicitUsings>enable</ImplicitUsings>
       <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
     </PropertyGroup>

     <ItemGroup>
       <Using Include="System"/>
       <Using Include="System.Collections.Generic"/>
       <Using Include="System.Linq"/>
       <Using Include="System.Threading.Tasks"/>
       <Using Include="Xunit"/>
       <Using Include="FluentAssertions"/>
       <Using Include="Moq"/>
     </ItemGroup>
   </Project>
   ```

## Phase 2: Directory Structure Design

**Standard .NET Solution Layout**:
```
Solution/
├── src/
│   └── MyApp/
│       ├── Domain/
│       │   ├── User.cs
│       │   └── Product.cs
│       ├── Services/
│       │   ├── UserService.cs
│       │   └── ProductService.cs
│       ├── Repositories/
│       │   ├── IUserRepository.cs
│       │   └── UserRepository.cs
│       └── MyApp.csproj
│
├── tests/
│   ├── MyApp.UnitTests/
│   │   ├── Services/
│   │   │   ├── UserServiceTests.cs
│   │   │   └── ProductServiceTests.cs
│   │   ├── Domain/
│   │   │   └── UserTests.cs
│   │   ├── Fixtures/
│   │   │   ├── UserFixture.cs
│   │   │   └── ProductFixture.cs
│   │   ├── Builders/
│   │   │   ├── UserBuilder.cs
│   │   │   └── ProductBuilder.cs
│   │   ├── Helpers/
│   │   │   ├── TestDataGenerator.cs
│   │   │   └── CustomAssertions.cs
│   │   └── MyApp.UnitTests.csproj
│   │
│   ├── MyApp.IntegrationTests/
│   │   ├── Repositories/
│   │   │   └── UserRepositoryTests.cs
│   │   ├── Api/
│   │   │   └── UserControllerTests.cs
│   │   ├── Infrastructure/
│   │   │   ├── DatabaseFixture.cs
│   │   │   └── WebApplicationFactoryFixture.cs
│   │   └── MyApp.IntegrationTests.csproj
│   │
│   ├── MyApp.E2ETests/
│   │   ├── Workflows/
│   │   │   └── UserWorkflowTests.cs
│   │   └── MyApp.E2ETests.csproj
│   │
│   └── MyApp.TestUtilities/
│       ├── Fixtures/
│       ├── Builders/
│       ├── Extensions/
│       └── MyApp.TestUtilities.csproj
│
├── MyApp.sln
├── Directory.Build.props
├── .editorconfig
└── .runsettings
```

## Phase 3: Fixture Infrastructure

1. **xUnit Fixtures**

   **Class Fixture** (Shared setup for all tests in a class):
   ```csharp
   /// <summary>
   /// Fixture providing database context for tests.
   /// Created once for all tests in the class.
   /// </summary>
   public class DatabaseFixture : IDisposable
   {
       public TestDbContext DbContext { get; private set; }

       public DatabaseFixture()
       {
           var options = new DbContextOptionsBuilder<TestDbContext>()
               .UseInMemoryDatabase(databaseName: "TestDatabase")
               .Options;

           DbContext = new TestDbContext(options);
           SeedTestData();
       }

       private void SeedTestData()
       {
           // Add seed data
           DbContext.Users.AddRange(
               new User { Id = 1, Username = "testuser1" },
               new User { Id = 2, Username = "testuser2" }
           );
           DbContext.SaveChanges();
       }

       public void Dispose()
       {
           DbContext?.Dispose();
       }
   }

   /// <summary>
   /// Test class using class fixture.
   /// </summary>
   public class UserServiceTests : IClassFixture<DatabaseFixture>
   {
       private readonly DatabaseFixture _fixture;

       public UserServiceTests(DatabaseFixture fixture)
       {
           _fixture = fixture;
       }

       [Fact]
       public void GetUser_ShouldReturnUser_WhenUserExists()
       {
           // Arrange
           var service = new UserService(_fixture.DbContext);

           // Act
           var user = service.GetUser(1);

           // Assert
           user.Should().NotBeNull();
           user.Username.Should().Be("testuser1");
       }
   }
   ```

   **Collection Fixture** (Shared across multiple test classes):
   ```csharp
   /// <summary>
   /// Collection fixture shared across multiple test classes.
   /// </summary>
   public class WebApplicationFixture : IDisposable
   {
       public HttpClient Client { get; private set; }
       private readonly WebApplicationFactory<Program> _factory;

       public WebApplicationFixture()
       {
           _factory = new WebApplicationFactory<Program>();
           Client = _factory.CreateClient();
       }

       public void Dispose()
       {
           Client?.Dispose();
           _factory?.Dispose();
       }
   }

   [CollectionDefinition("WebApp Collection")]
   public class WebAppCollection : ICollectionFixture<WebApplicationFixture>
   {
       // This class is never instantiated, it's just a marker
   }

   /// <summary>
   /// Test class using collection fixture.
   /// </summary>
   [Collection("WebApp Collection")]
   public class UserApiTests
   {
       private readonly WebApplicationFixture _fixture;

       public UserApiTests(WebApplicationFixture fixture)
       {
           _fixture = fixture;
       }

       [Fact]
       public async Task GetUsers_ShouldReturnOk()
       {
           var response = await _fixture.Client.GetAsync("/api/users");
           response.StatusCode.Should().Be(HttpStatusCode.OK);
       }
   }
   ```

2. **NUnit Fixtures**

   ```csharp
   /// <summary>
   /// NUnit fixture with SetUp and TearDown.
   /// </summary>
   [TestFixture]
   public class UserServiceTests
   {
       private UserService _userService;
       private Mock<IUserRepository> _mockRepository;

       [OneTimeSetUp]
       public void OneTimeSetUp()
       {
           // Runs once before all tests
           Console.WriteLine("Starting test suite");
       }

       [SetUp]
       public void SetUp()
       {
           // Runs before each test
           _mockRepository = new Mock<IUserRepository>();
           _userService = new UserService(_mockRepository.Object);
       }

       [TearDown]
       public void TearDown()
       {
           // Runs after each test
           _userService = null;
       }

       [OneTimeTearDown]
       public void OneTimeTearDown()
       {
           // Runs once after all tests
           Console.WriteLine("Test suite completed");
       }

       [Test]
       public void CreateUser_ShouldCallRepository()
       {
           // Arrange
           var user = new User { Username = "testuser" };

           // Act
           _userService.CreateUser(user);

           // Assert
           _mockRepository.Verify(r => r.Add(It.IsAny<User>()), Times.Once);
       }
   }
   ```

3. **Test Data Builders**

   ```csharp
   /// <summary>
   /// Builder pattern for test data creation.
   /// </summary>
   public class UserBuilder
   {
       private int _id = 1;
       private string _username = "testuser";
       private string _email = "test@example.com";
       private bool _isActive = true;
       private List<string> _roles = new();

       public static UserBuilder CreateDefault() => new UserBuilder();

       public UserBuilder WithId(int id)
       {
           _id = id;
           return this;
       }

       public UserBuilder WithUsername(string username)
       {
           _username = username;
           return this;
       }

       public UserBuilder WithEmail(string email)
       {
           _email = email;
           return this;
       }

       public UserBuilder Inactive()
       {
           _isActive = false;
           return this;
       }

       public UserBuilder WithRole(string role)
       {
           _roles.Add(role);
           return this;
       }

       public User Build()
       {
           return new User
           {
               Id = _id,
               Username = _username,
               Email = _email,
               IsActive = _isActive,
               Roles = _roles
           };
       }
   }

   // Usage:
   // var admin = UserBuilder.CreateDefault()
   //     .WithUsername("admin")
   //     .WithRole("Administrator")
   //     .Build();
   ```

4. **Object Mother Pattern**

   ```csharp
   /// <summary>
   /// Object Mother pattern for common test objects.
   /// </summary>
   public static class UserMother
   {
       public static User CreateDefaultUser() =>
           new User
           {
               Id = 1,
               Username = "testuser",
               Email = "test@example.com",
               IsActive = true
           };

       public static User CreateAdminUser() =>
           new User
           {
               Id = 2,
               Username = "admin",
               Email = "admin@example.com",
               IsActive = true,
               Roles = new List<string> { "Administrator" }
           };

       public static User CreateInactiveUser() =>
           new User
           {
               Id = 3,
               Username = "inactive",
               Email = "inactive@example.com",
               IsActive = false
           };

       public static List<User> CreateUserList(int count) =>
           Enumerable.Range(1, count)
               .Select(i => new User
               {
                   Id = i,
                   Username = $"user{i}",
                   Email = $"user{i}@example.com",
                   IsActive = true
               })
               .ToList();
   }
   ```

## Phase 4: Test Utilities & Helpers

1. **Custom Assertions with FluentAssertions**

   ```csharp
   /// <summary>
   /// Custom assertion extensions.
   /// </summary>
   public static class UserAssertions
   {
       public static UserAssertionsWrapper Should(this User user)
       {
           return new UserAssertionsWrapper(user);
       }
   }

   public class UserAssertionsWrapper
   {
       private readonly User _user;

       public UserAssertionsWrapper(User user)
       {
           _user = user;
       }

       public AndConstraint<UserAssertionsWrapper> HaveValidEmail(
           string because = "", params object[] becauseArgs)
       {
           var emailRegex = @"^[^@\s]+@[^@\s]+\.[^@\s]+$";
           Regex.IsMatch(_user.Email, emailRegex)
               .Should().BeTrue(because, becauseArgs);

           return new AndConstraint<UserAssertionsWrapper>(this);
       }

       public AndConstraint<UserAssertionsWrapper> BeActive(
           string because = "", params object[] becauseArgs)
       {
           _user.IsActive.Should().BeTrue(because, becauseArgs);
           return new AndConstraint<UserAssertionsWrapper>(this);
       }

       public AndConstraint<UserAssertionsWrapper> HaveRole(
           string role, string because = "", params object[] becauseArgs)
       {
           _user.Roles.Should().Contain(role, because, becauseArgs);
           return new AndConstraint<UserAssertionsWrapper>(this);
       }
   }

   // Usage:
   // user.Should().HaveValidEmail().And.BeActive().And.HaveRole("Admin");
   ```

2. **Test Data Generator with AutoFixture**

   ```csharp
   /// <summary>
   /// AutoFixture customizations for test data generation.
   /// </summary>
   public class UserCustomization : ICustomization
   {
       public void Customize(IFixture fixture)
       {
           fixture.Customize<User>(composer => composer
               .With(u => u.Username, () => fixture.Create<string>())
               .With(u => u.Email, () => $"{fixture.Create<string>()}@example.com")
               .With(u => u.IsActive, true)
               .Without(u => u.Id));
       }
   }

   // Usage in tests:
   [Theory, AutoData]
   public void CreateUser_ShouldGenerateId(User user)
   {
       // AutoFixture automatically generates user with test data
       _userService.Create(user);
       user.Id.Should().BeGreaterThan(0);
   }
   ```

3. **Test Data with Bogus**

   ```csharp
   /// <summary>
   /// Bogus data generator for realistic test data.
   /// </summary>
   public class TestDataGenerator
   {
       private readonly Faker<User> _userFaker;

       public TestDataGenerator()
       {
           _userFaker = new Faker<User>()
               .RuleFor(u => u.Id, f => f.Random.Int(1, 1000))
               .RuleFor(u => u.Username, f => f.Internet.UserName())
               .RuleFor(u => u.Email, f => f.Internet.Email())
               .RuleFor(u => u.FirstName, f => f.Name.FirstName())
               .RuleFor(u => u.LastName, f => f.Name.LastName())
               .RuleFor(u => u.IsActive, f => f.Random.Bool(0.8f))
               .RuleFor(u => u.CreatedAt, f => f.Date.Past());
       }

       public User GenerateUser() => _userFaker.Generate();

       public List<User> GenerateUsers(int count) => _userFaker.Generate(count);
   }
   ```

## Phase 5: Test Discovery & Execution

1. **Test Categorization**

   **xUnit Traits**:
   ```csharp
   [Trait("Category", "Unit")]
   [Fact]
   public void UnitTest() { }

   [Trait("Category", "Integration")]
   [Fact]
   public void IntegrationTest() { }
   ```

   **NUnit Categories**:
   ```csharp
   [Test, Category("Unit")]
   public void UnitTest() { }

   [Test, Category("Integration")]
   public void IntegrationTest() { }
   ```

2. **Execution Commands**

   ```bash
   # Run all tests
   dotnet test

   # Run specific test project
   dotnet test tests/MyApp.UnitTests/

   # Run tests with filter
   dotnet test --filter "Category=Unit"
   dotnet test --filter "FullyQualifiedName~UserService"

   # Run with logger
   dotnet test --logger "trx;LogFileName=test-results.trx"

   # Run with coverage
   dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=opencover

   # Parallel execution
   dotnet test --parallel

   # Verbose output
   dotnet test --logger "console;verbosity=detailed"
   ```

## Output Format

### Infrastructure Summary
- **Test Framework**: [xUnit/NUnit/MSTest with justification]
- **Total Test Projects**: [count]
- **Test Organization**: [structure description]
- **Fixture Types**: [list of fixture types]
- **Utility Projects**: [shared test utilities]

### Directory Structure
```
[Complete solution tree with all test projects and key files]
```

### Configuration Files Created
- **.csproj files**: Dependencies and settings
- **xunit.runner.json** or **.runsettings**: Test configuration
- **Directory.Build.props**: Solution-wide settings

### Fixture Infrastructure
**Class Fixtures**:
- [fixture_name]: [description and purpose]

**Collection Fixtures**:
- [fixture_name]: [description and shared scope]

**Builders**:
- [builder_name]: [fluent API methods]

### Test Utilities
**Custom Assertions**:
- [assertion_name]: [purpose and usage]

**Data Generators**:
- [generator_name]: [AutoFixture/Bogus configuration]

**Helper Extensions**:
- [extension_name]: [utility methods]

### Test Execution Commands
```bash
# Run all tests
dotnet test

# Run specific category
dotnet test --filter "Category=Unit"

# Run with coverage
dotnet test /p:CollectCoverage=true

# Run in Visual Studio
Test Explorer -> Run All
```

### Best Practices Implemented
- Clear separation of test types (Unit/Integration/E2E)
- Reusable fixtures and builders
- Custom assertions for domain objects
- Realistic test data generation
- Parallel execution configured
- Code coverage integrated
- Proper test isolation

### Next Steps
- [ ] Implement actual test cases using infrastructure
- [ ] Configure CI/CD integration
- [ ] Set up code coverage reporting
- [ ] Add integration test databases
- [ ] Document team testing guidelines
~~~

## Output Format

The AI assistant should deliver:

1. **Test infrastructure design** with complete solution structure
2. **Configuration files** (.csproj, xunit.runner.json, .runsettings)
3. **Fixture implementations** for different scopes
4. **Test data builders and generators**
5. **Custom assertions** for domain objects
6. **Test utility library** with shared helpers
7. **Documentation** of conventions and patterns
8. **Execution commands** for various scenarios
