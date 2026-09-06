### Step 7: Test Effectively with JUnit 5

**Parameterized and Nested Tests**:

```java
class UserValidatorTest {

    private final UserValidator validator = new UserValidator();

    @ParameterizedTest(name = "email \"{0}\" should be {1}")
    @CsvSource({
        "alice@example.com, true",
        "bob@test.org, true",
        "invalid, false",
        "'', false",
        "@missing-local.com, false"
    })
    void shouldValidateEmail(String email, boolean expected) {
        assertThat(validator.isValidEmail(email)).isEqualTo(expected);
    }

    @ParameterizedTest
    @MethodSource("userProvider")
    void shouldValidateUser(User user, boolean expected) {
        assertThat(validator.isValid(user)).isEqualTo(expected);
    }

    static Stream<Arguments> userProvider() {
        return Stream.of(
            Arguments.of(new User("Alice", "alice@example.com", LocalDate.now()), true),
            Arguments.of(new User("", "bob@example.com", LocalDate.now()), false),
            Arguments.of(new User("Charlie", "invalid", LocalDate.now()), false)
        );
    }

    @Nested
    class WhenUserIsNew {
        @Test
        void shouldRequireName() {
            var user = new User("", "test@example.com", LocalDate.now());
            assertThat(validator.isValid(user)).isFalse();
        }

        @Test
        void shouldRequireValidEmail() {
            var user = new User("Alice", "not-an-email", LocalDate.now());
            assertThat(validator.isValid(user)).isFalse();
        }
    }

    @Nested
    class WhenUserExists {
        @Test
        void shouldAllowEmailUpdate() {
            var user = new User("Alice", "new@example.com", LocalDate.of(2024, 1, 1));
            assertThat(validator.isValid(user)).isTrue();
        }
    }
}
```

**Mockito and AssertJ**:

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock private OrderRepository orderRepository;
    @Mock private PaymentGateway paymentGateway;
    @Mock private NotificationService notificationService;
    @InjectMocks private OrderService orderService;

    @Test
    void shouldCreateOrderAndChargePayment() {
        // Arrange
        var request = new CreateOrderRequest("user-1", List.of(
            new OrderItem("product-a", 2, new BigDecimal("10.00"))
        ));
        var expectedOrder = new Order("order-1", "user-1", new BigDecimal("20.00"));

        when(orderRepository.save(any(Order.class))).thenReturn(expectedOrder);
        when(paymentGateway.charge(any(BigDecimal.class))).thenReturn(PaymentResult.success());

        // Act
        Order result = orderService.createOrder(request);

        // Assert
        assertThat(result.id()).isEqualTo("order-1");
        assertThat(result.total()).isEqualByComparingTo("20.00");

        verify(paymentGateway).charge(new BigDecimal("20.00"));
        verify(notificationService).sendOrderConfirmation(eq("user-1"), any());
        verifyNoMoreInteractions(paymentGateway);
    }

    @Test
    void shouldThrowWhenPaymentFails() {
        var request = new CreateOrderRequest("user-1", List.of(
            new OrderItem("product-a", 1, new BigDecimal("50.00"))
        ));

        when(orderRepository.save(any())).thenReturn(new Order("order-2", "user-1", new BigDecimal("50.00")));
        when(paymentGateway.charge(any())).thenReturn(PaymentResult.declined("insufficient funds"));

        assertThatThrownBy(() -> orderService.createOrder(request))
            .isInstanceOf(PaymentDeclinedException.class)
            .hasMessageContaining("insufficient funds");

        verify(notificationService, never()).sendOrderConfirmation(any(), any());
    }
}
```

**TestContainers and MockMvc**:

```java
// Integration test with TestContainers (real PostgreSQL)
@SpringBootTest
@Testcontainers
class UserRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldPersistAndRetrieveUser() {
        var user = new UserEntity("Alice", "alice@example.com");
        userRepository.save(user);

        Optional<UserEntity> found = userRepository.findByEmail("alice@example.com");

        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("Alice");
    }
}

// Web layer test with MockMvc (Spring Boot test slice)
@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired private MockMvc mockMvc;
    @MockBean private UserService userService;

    @Test
    void shouldReturnUserById() throws Exception {
        var user = new User("user-1", "Alice", "alice@example.com");
        when(userService.findById("user-1")).thenReturn(Optional.of(user));

        mockMvc.perform(get("/api/v1/users/user-1")
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Alice"))
            .andExpect(jsonPath("$.email").value("alice@example.com"));
    }

    @Test
    void shouldReturn404WhenUserNotFound() throws Exception {
        when(userService.findById("missing")).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/users/missing")
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.code").value("NOT_FOUND"));
    }

    @Test
    void shouldValidateCreateRequest() throws Exception {
        String invalidBody = """
                { "name": "", "email": "not-valid" }
                """;

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidBody))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"));
    }
}
```
