### Step 5: Apply Spring Boot Patterns

**Dependency Injection and Configuration**:

```java
// Constructor injection (preferred over field injection)
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;
    private final NotificationService notificationService;

    // Single constructor: @Autowired is optional
    public OrderService(OrderRepository orderRepository,
                        PaymentGateway paymentGateway,
                        NotificationService notificationService) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
        this.notificationService = notificationService;
    }
}

// @Configuration class for third-party beans
@Configuration
public class HttpClientConfig {

    @Bean
    public HttpClient httpClient(@Value("${http.timeout:30}") int timeoutSeconds) {
        return HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(timeoutSeconds))
            .followRedirects(HttpClient.Redirect.NORMAL)
            .build();
    }

    @Bean
    @Profile("production")
    public HttpClient productionHttpClient() {
        return HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .sslContext(productionSslContext())
            .build();
    }
}

// Type-safe configuration properties
@ConfigurationProperties(prefix = "app.notification")
public record NotificationProperties(
    boolean enabled,
    String senderEmail,
    int maxRetries,
    Duration retryDelay
) {}

// application.yml
// app:
//   notification:
//     enabled: true
//     sender-email: noreply@example.com
//     max-retries: 3
//     retry-delay: 5s
```

**REST Controllers and Exception Handlers**:

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    public List<UserDto> listUsers(@RequestParam(defaultValue = "0") int page,
                                   @RequestParam(defaultValue = "20") int size) {
        return userService.findAll(PageRequest.of(page, size))
            .map(UserDto::from)
            .getContent();
    }

    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable Long id) {
        return userService.findById(id)
            .map(UserDto::from)
            .orElseThrow(() -> new ResourceNotFoundException("User", id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserDto createUser(@Valid @RequestBody CreateUserRequest request) {
        User user = userService.create(request);
        return UserDto.from(user);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}

// Spring Security basic configuration (Java 21+ / Spring Security 6.x)
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .build();
    }
}
```
