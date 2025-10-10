# Java Mocks & Fixtures

## Objective
Design and implement effective mocking strategies and fixture management using Mockito and WireMock to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── mocks_fixtures/
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

### Fixture Setup
- [ ] JUnit lifecycle methods configured (@BeforeEach/@AfterEach/@BeforeAll/@AfterAll)
- [ ] Test data builders created for flexible data generation
- [ ] Fixture factories implemented with realistic data
- [ ] Cleanup and reset logic automated
- [ ] Fixtures documented with clear purposes

### Mocking Strategy
- [ ] External dependencies identified for mocking
- [ ] Mocking approach chosen (mock vs spy vs stub)
- [ ] Mock objects configured with Mockito
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
# Java Mocks & Fixtures Implementation

Please implement comprehensive mocking and fixture strategies for this Java project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Fixture Architecture Design

### Understanding JUnit 5 Lifecycle

JUnit 5 provides annotations for fixture management:

**Basic Setup/Teardown**:
```java
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class UserServiceTest {
    private Database database;
    private UserService userService;
    private User testUser;

    @BeforeAll
    static void setupClass() {
        // Runs once before all tests in this class
        System.setProperty("env", "test");
    }

    @BeforeEach
    void setUp() {
        // Runs before each test
        database = new Database("test_db");
        userService = new UserService(database);
        testUser = new User("testuser", "test@example.com");
    }

    @AfterEach
    void tearDown() {
        // Runs after each test - cleanup
        database.clearTestData();
    }

    @AfterAll
    static void tearDownClass() {
        // Runs once after all tests
        Database.closeAllConnections();
    }

    @Test
    void shouldCreateUser() {
        User result = userService.createUser(testUser);
        assertEquals("testuser", result.getUsername());
    }
}
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Class-Level Fixtures (@BeforeAll/@AfterAll)**:
```java
class DatabaseIntegrationTest {
    private static Connection connection;
    private static TestDatabase testDb;

    @BeforeAll
    static void setupDatabase() throws SQLException {
        // Expensive setup - run once
        connection = DriverManager.getConnection("jdbc:h2:mem:test");
        testDb = new TestDatabase(connection);
        testDb.createSchema();
    }

    @AfterAll
    static void tearDownDatabase() throws SQLException {
        // Cleanup after all tests
        testDb.dropSchema();
        connection.close();
    }

    @Test
    void shouldInsertUser() {
        testDb.insertUser(new User("alice", "alice@test.com"));
        assertEquals(1, testDb.countUsers());
    }

    @Test
    void shouldQueryUsers() {
        List<User> users = testDb.queryUsers();
        assertFalse(users.isEmpty());
    }
}
```

**2. Test-Level Fixtures (@BeforeEach/@AfterEach)**:
```java
class UserRepositoryTest {
    private UserRepository repository;
    private Database mockDatabase;

    @BeforeEach
    void setUp() {
        // Fresh instance for each test
        mockDatabase = mock(Database.class);
        repository = new UserRepository(mockDatabase);
    }

    @AfterEach
    void tearDown() {
        // Reset after each test
        reset(mockDatabase);
    }

    @Test
    void shouldFindUserById() {
        User expected = new User(1L, "alice");
        when(mockDatabase.findById(1L)).thenReturn(Optional.of(expected));

        Optional<User> result = repository.findById(1L);

        assertTrue(result.isPresent());
        assertEquals("alice", result.get().getUsername());
    }
}
```

**3. Nested Test Classes**:
```java
@DisplayName("User API Tests")
class UserApiTest {
    private MockMvc mockMvc;
    private UserService userService;

    @BeforeEach
    void setUp() {
        userService = mock(UserService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(
            new UserController(userService)
        ).build();
    }

    @Nested
    @DisplayName("GET /users")
    class GetUsersTests {
        private List<User> testUsers;

        @BeforeEach
        void setUpUsers() {
            testUsers = Arrays.asList(
                new User(1L, "alice"),
                new User(2L, "bob")
            );
            when(userService.getAllUsers()).thenReturn(testUsers);
        }

        @Test
        void shouldReturnAllUsers() throws Exception {
            mockMvc.perform(get("/users"))
                   .andExpect(status().isOk())
                   .andExpect(jsonPath("$", hasSize(2)));
        }
    }

    @Nested
    @DisplayName("POST /users")
    class CreateUserTests {
        @Test
        void shouldCreateUser() throws Exception {
            User newUser = new User(null, "charlie");
            User saved = new User(1L, "charlie");
            when(userService.createUser(any())).thenReturn(saved);

            mockMvc.perform(post("/users")
                   .contentType(MediaType.APPLICATION_JSON)
                   .content("{\"username\":\"charlie\"}"))
                   .andExpect(status().isCreated());
        }
    }
}
```

### Fixture Factories

Create factories for flexible test data generation:

```java
// test/java/com/example/factories/UserFactory.java
public class UserFactory {
    private static long idCounter = 0;
    private List<User> createdUsers = new ArrayList<>();

    public User create() {
        return create(new HashMap<>());
    }

    public User create(Map<String, Object> overrides) {
        idCounter++;
        User user = new User();
        user.setId((Long) overrides.getOrDefault("id", idCounter));
        user.setUsername((String) overrides.getOrDefault("username", "user_" + idCounter));
        user.setEmail((String) overrides.getOrDefault("email", "user" + idCounter + "@test.com"));
        user.setAge((Integer) overrides.getOrDefault("age", 25));
        user.setActive((Boolean) overrides.getOrDefault("active", true));
        user.setCreatedAt((LocalDateTime) overrides.getOrDefault("createdAt", LocalDateTime.now()));

        createdUsers.add(user);
        return user;
    }

    public List<User> createBatch(int count) {
        return createBatch(count, new HashMap<>());
    }

    public List<User> createBatch(int count, Map<String, Object> overrides) {
        List<User> users = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            users.add(create(overrides));
        }
        return users;
    }

    public void reset() {
        idCounter = 0;
        createdUsers.clear();
    }
}

// Usage in tests
class UserOperationsTest {
    private UserFactory userFactory;

    @BeforeEach
    void setUp() {
        userFactory = new UserFactory();
    }

    @Test
    void shouldCreateUsersWithDefaults() {
        User user1 = userFactory.create();
        User user2 = userFactory.create();

        assertEquals("user_1", user1.getUsername());
        assertEquals("user_2", user2.getUsername());
    }

    @Test
    void shouldCreateUsersWithCustomData() {
        Map<String, Object> data = Map.of(
            "username", "alice",
            "email", "alice@example.com",
            "age", 30
        );
        User user = userFactory.create(data);

        assertEquals("alice", user.getUsername());
        assertEquals(30, user.getAge());
    }

    @Test
    void shouldCreateBatchOfUsers() {
        List<User> users = userFactory.createBatch(5);

        assertEquals(5, users.size());
        assertTrue(users.stream().allMatch(User::isActive));
    }
}
```

### Builder Pattern for Complex Objects

```java
// test/java/com/example/builders/OrderBuilder.java
public class OrderBuilder {
    private Long id;
    private Long userId;
    private List<OrderItem> items = new ArrayList<>();
    private OrderStatus status = OrderStatus.PENDING;
    private BigDecimal total = BigDecimal.ZERO;
    private Address shippingAddress;

    public OrderBuilder withId(Long id) {
        this.id = id;
        return this;
    }

    public OrderBuilder forUser(Long userId) {
        this.userId = userId;
        return this;
    }

    public OrderBuilder addItem(Long productId, int quantity, BigDecimal price) {
        OrderItem item = new OrderItem(productId, quantity, price);
        this.items.add(item);
        this.total = this.total.add(price.multiply(BigDecimal.valueOf(quantity)));
        return this;
    }

    public OrderBuilder withStatus(OrderStatus status) {
        this.status = status;
        return this;
    }

    public OrderBuilder withShippingAddress(Address address) {
        this.shippingAddress = address;
        return this;
    }

    public Order build() {
        Order order = new Order();
        order.setId(id);
        order.setUserId(userId);
        order.setItems(new ArrayList<>(items));
        order.setStatus(status);
        order.setTotal(total);
        order.setShippingAddress(shippingAddress);
        return order;
    }
}

// Usage
@Test
void shouldProcessOrder() {
    Address address = new Address("123 Main St", "Boston", "MA");
    Order order = new OrderBuilder()
        .withId(1L)
        .forUser(100L)
        .addItem(1L, 2, new BigDecimal("10.00"))
        .addItem(2L, 1, new BigDecimal("15.00"))
        .withStatus(OrderStatus.CONFIRMED)
        .withShippingAddress(address)
        .build();

    assertEquals(new BigDecimal("35.00"), order.getTotal());
    assertEquals(2, order.getItems().size());
}
```

## Phase 2: Mocking Strategies with Mockito

### Understanding Mockito

Mockito is the most popular Java mocking framework:

```xml
<!-- Maven dependency -->
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-core</artifactId>
    <version>5.8.0</version>
    <scope>test</scope>
</dependency>
```

**Creating Mocks**:
```java
import static org.mockito.Mockito.*;

class UserServiceTest {
    private UserRepository mockRepository;
    private EmailService mockEmailService;
    private UserService userService;

    @BeforeEach
    void setUp() {
        // Create mocks
        mockRepository = mock(UserRepository.class);
        mockEmailService = mock(EmailService.class);
        userService = new UserService(mockRepository, mockEmailService);
    }

    @Test
    void shouldCreateUser() {
        User user = new User("alice", "alice@test.com");
        when(mockRepository.save(user)).thenReturn(user);
        when(mockEmailService.sendWelcome(user)).thenReturn(true);

        User result = userService.createUser(user);

        assertNotNull(result);
        verify(mockRepository).save(user);
        verify(mockEmailService).sendWelcome(user);
    }
}
```

**Using Annotations**:
```java
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.junit.jupiter.api.extension.ExtendWith;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository mockRepository;

    @Mock
    private EmailService mockEmailService;

    @InjectMocks  // Automatically injects mocks
    private UserService userService;

    @Test
    void shouldCreateUser() {
        User user = new User("alice", "alice@test.com");
        when(mockRepository.save(any(User.class))).thenReturn(user);

        User result = userService.createUser(user);

        assertNotNull(result);
        verify(mockRepository).save(any(User.class));
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
- Pure functions
- Simple POJOs
- Value objects
- Integration tests
- Critical business logic

```java
// GOOD - Mock external service
@Test
void shouldFetchUserData() {
    ExternalApi mockApi = mock(ExternalApi.class);
    when(mockApi.getUser(1L)).thenReturn(new User(1L, "alice"));

    User result = userService.fetchFromApi(1L);
    assertEquals("alice", result.getUsername());
}

// GOOD - Use real object for simple logic
@Test
void shouldCalculateTotal() {
    List<BigDecimal> items = Arrays.asList(
        new BigDecimal("10"),
        new BigDecimal("20"),
        new BigDecimal("30")
    );
    assertEquals(new BigDecimal("60"), Calculator.sum(items));
}

// BAD - Over-mocking simple logic
@Test
void shouldCalculateTotal() {
    Calculator mockCalc = mock(Calculator.class);
    when(mockCalc.sum(any())).thenReturn(new BigDecimal("60"));
    // Testing the mock, not real code
}
```

### Mockito Stubbing

**Return Values**:
```java
// Simple return value
when(mockRepository.findById(1L)).thenReturn(Optional.of(user));

// Different returns per call
when(mockApi.fetchStatus())
    .thenReturn(Status.PENDING)
    .thenReturn(Status.COMPLETE);

// Throw exception
when(mockDatabase.connect()).thenThrow(new SQLException("Connection failed"));

// Answer with custom logic
when(mockRepository.findById(anyLong())).thenAnswer(invocation -> {
    Long id = invocation.getArgument(0);
    return id == 1L ? Optional.of(new User(1L, "alice")) : Optional.empty();
});
```

**Argument Matchers**:
```java
// Any argument
when(mockRepository.save(any(User.class))).thenReturn(user);

// Specific argument
when(mockRepository.findById(eq(1L))).thenReturn(Optional.of(user));

// Argument captor
ArgumentCaptor<User> userCaptor = ArgumentCaptor.forClass(User.class);
verify(mockRepository).save(userCaptor.capture());
User captured = userCaptor.getValue();
assertEquals("alice", captured.getUsername());

// Custom matcher
when(mockRepository.save(argThat(u -> u.getAge() > 18))).thenReturn(user);
```

### Mockito Verification

```java
User user = new User("alice");

// Verify method was called
verify(mockRepository).save(user);

// Verify call count
verify(mockRepository, times(2)).save(any(User.class));
verify(mockRepository, atLeastOnce()).findAll();
verify(mockRepository, atMost(3)).findById(anyLong());
verify(mockRepository, never()).delete(any(User.class));

// Verify order of calls
InOrder inOrder = inOrder(mockRepository, mockEmailService);
inOrder.verify(mockRepository).save(user);
inOrder.verify(mockEmailService).sendWelcome(user);

// Verify no more interactions
verifyNoMoreInteractions(mockRepository);

// Verify no interactions at all
verifyNoInteractions(mockEmailService);
```

### Spying on Real Objects

```java
// Spy wraps a real object
List<String> realList = new ArrayList<>();
List<String> spyList = spy(realList);

// Real method is called
spyList.add("item1");
assertEquals(1, spyList.size());

// Can stub specific methods
when(spyList.size()).thenReturn(100);
assertEquals(100, spyList.size());

// Verify interactions
verify(spyList).add("item1");
```

**Spying on Dependencies**:
```java
@Spy
private UserRepository userRepository = new UserRepositoryImpl();

@InjectMocks
private UserService userService;

@Test
void shouldSpyOnRepository() {
    // Real method is called, but we can verify
    User user = new User("alice");
    userService.createUser(user);

    verify(userRepository).save(user);
}
```

## Phase 3: Mocking External Dependencies

### Mocking HTTP with WireMock

```xml
<dependency>
    <groupId>com.github.tomakehurst</groupId>
    <artifactId>wiremock-jre8</artifactId>
    <version>2.35.0</version>
    <scope>test</scope>
</dependency>
```

```java
import com.github.tomakehurst.wiremock.WireMockServer;
import static com.github.tomakehurst.wiremock.client.WireMock.*;

class ExternalApiTest {
    private WireMockServer wireMockServer;
    private ApiClient apiClient;

    @BeforeEach
    void setUp() {
        wireMockServer = new WireMockServer(8089);
        wireMockServer.start();
        configureFor("localhost", 8089);
        apiClient = new ApiClient("http://localhost:8089");
    }

    @AfterEach
    void tearDown() {
        wireMockServer.stop();
    }

    @Test
    void shouldMockHttpGet() {
        // Stub HTTP endpoint
        stubFor(get(urlEqualTo("/api/users/1"))
            .willReturn(aResponse()
                .withStatus(200)
                .withHeader("Content-Type", "application/json")
                .withBody("{\"id\":1,\"name\":\"alice\"}")));

        User user = apiClient.getUser(1L);

        assertEquals("alice", user.getName());
        verify(getRequestedFor(urlEqualTo("/api/users/1")));
    }

    @Test
    void shouldMockHttpPost() {
        stubFor(post(urlEqualTo("/api/users"))
            .withRequestBody(containing("alice"))
            .willReturn(aResponse()
                .withStatus(201)
                .withBody("{\"id\":1,\"name\":\"alice\"}")));

        User newUser = new User(null, "alice");
        User created = apiClient.createUser(newUser);

        assertEquals(1L, created.getId());
    }

    @Test
    void shouldSimulateNetworkError() {
        stubFor(get(urlEqualTo("/api/users/1"))
            .willReturn(aResponse()
                .withStatus(500)
                .withFixedDelay(3000)));

        assertThrows(ApiException.class, () -> apiClient.getUser(1L));
    }
}
```

### Mocking Databases with H2

```xml
<dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <version>2.2.224</version>
    <scope>test</scope>
</dependency>
```

```java
class UserRepositoryIntegrationTest {
    private static Connection connection;
    private UserRepository repository;

    @BeforeAll
    static void setupDatabase() throws SQLException {
        // In-memory H2 database
        connection = DriverManager.getConnection(
            "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1"
        );

        // Create schema
        connection.createStatement().execute(
            "CREATE TABLE users (" +
            "id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
            "username VARCHAR(255), " +
            "email VARCHAR(255))"
        );
    }

    @BeforeEach
    void setUp() {
        repository = new UserRepository(connection);
    }

    @AfterEach
    void cleanUp() throws SQLException {
        connection.createStatement().execute("DELETE FROM users");
    }

    @AfterAll
    static void tearDown() throws SQLException {
        connection.close();
    }

    @Test
    void shouldSaveAndRetrieveUser() {
        User user = new User(null, "alice", "alice@test.com");
        User saved = repository.save(user);

        Optional<User> found = repository.findById(saved.getId());

        assertTrue(found.isPresent());
        assertEquals("alice", found.get().getUsername());
    }
}
```

### Mocking File System

```java
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import java.nio.file.Files;

class FileServiceTest {
    @TempDir
    Path tempDir;

    @Test
    void shouldReadFile() throws IOException {
        // Create temporary test file
        Path testFile = tempDir.resolve("config.txt");
        Files.writeString(testFile, "setting=value");

        FileService service = new FileService();
        Map<String, String> config = service.readConfig(testFile);

        assertEquals("value", config.get("setting"));
    }

    @Test
    void shouldWriteFile() throws IOException {
        Path outputFile = tempDir.resolve("output.txt");

        FileService service = new FileService();
        service.writeLog(outputFile, "test message");

        String content = Files.readString(outputFile);
        assertTrue(content.contains("test message"));
    }
}
```

### Mocking Time

```java
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;

class TimestampServiceTest {
    @Test
    void shouldMockTime() {
        Clock fixedClock = Clock.fixed(
            Instant.parse("2024-01-15T12:00:00Z"),
            ZoneId.of("UTC")
        );

        TimestampService service = new TimestampService(fixedClock);
        String timestamp = service.getCurrentTimestamp();

        assertEquals("2024-01-15T12:00:00Z", timestamp);
    }
}
```

## Phase 4: Test Data Factories with Libraries

### Using Java Faker

```xml
<dependency>
    <groupId>com.github.javafaker</groupId>
    <artifactId>javafaker</artifactId>
    <version>1.0.2</version>
    <scope>test</scope>
</dependency>
```

```java
import com.github.javafaker.Faker;

class UserFactoryWithFaker {
    private static final Faker faker = new Faker();

    public static User createRandomUser() {
        return User.builder()
            .username(faker.name().username())
            .email(faker.internet().emailAddress())
            .firstName(faker.name().firstName())
            .lastName(faker.name().lastName())
            .age(faker.number().numberBetween(18, 80))
            .build();
    }

    public static List<User> createRandomUsers(int count) {
        return IntStream.range(0, count)
            .mapToObj(i -> createRandomUser())
            .collect(Collectors.toList());
    }
}
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Class-Level Setup** (@BeforeAll/@AfterAll):
- [fixture_name]: [purpose, setup, teardown]

**Test-Level Setup** (@BeforeEach/@AfterEach):
- [fixture_name]: [purpose, when to use]

**Fixture Factories**:
- [factory_name]: [creates what, customization options]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Tool (Mockito/WireMock) | Reason |
|------------|------------------|-------------------------|--------|
| [API/Service] | [mock/spy/stub] | [tool] | [justification] |

**Mock Configurations**:
```java
// Example mock setup
@Mock
private ApiClient mockApiClient;

@BeforeEach
void setUp() {
    when(mockApiClient.get(anyString())).thenReturn(new Response(200, "OK"));
}
```

### Test Data Factories
**Factory Classes**:
- UserFactory: [customization options]
- OrderFactory: [customization options]

**Builder Classes**:
- [builder_name]: [purpose, fluent interface methods]

### Usage Examples
```java
// Example test using fixtures and mocks
@ExtendWith(MockitoExtension.class)
class UserRegistrationTest {
    @Mock
    private EmailService mockEmailService;

    @InjectMocks
    private UserService userService;

    private UserFactory userFactory;

    @BeforeEach
    void setUp() {
        userFactory = new UserFactory();
    }

    @Test
    void shouldRegisterUser() {
        User userData = userFactory.create(Map.of("username", "alice"));
        when(mockEmailService.sendWelcome(any())).thenReturn(true);

        User result = userService.registerUser(userData);

        assertNotNull(result.getId());
        verify(mockEmailService).sendWelcome(userData);
    }
}
```

### Best Practices Implemented
- [ ] Fixtures use appropriate lifecycle annotations
- [ ] Mocks are used for external dependencies only
- [ ] Test data factories provide flexible data creation
- [ ] Mock verification ensures correct behavior
- [ ] Argument matchers used appropriately
- [ ] Cleanup ensures isolation between tests

### Common Pitfalls Avoided
- Over-mocking simple POJOs
- Not using @ExtendWith(MockitoExtension.class)
- Stubbing in @AfterEach instead of @BeforeEach
- Complex mock setups that obscure test intent
- Testing mock behavior instead of real code

### Next Steps
- [ ] Implement remaining fixtures for integration tests
- [ ] Add factories for all domain models
- [ ] Document fixture usage for team
- [ ] Set up WireMock for HTTP integration tests
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

1. **Comprehensive fixture setup** using JUnit 5 annotations
2. **Mock configurations** for external dependencies
3. **Test data factories** for domain objects
4. **Builder patterns** for complex test data
5. **Usage documentation** with examples
6. **Best practices guide** for Mockito and WireMock
7. **Fixture and mock catalog** for easy reference
