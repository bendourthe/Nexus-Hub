# Java API Documentation

## Objective
Create complete, accurate API documentation for Java-based APIs (REST/gRPC) that enables developers to quickly understand and successfully integrate, including authentication flows, request formats, response structures, and error handling.

## Implementation Checklist

### Endpoint Documentation
- [ ] All endpoints documented with HTTP methods
- [ ] Request/response schemas with Java types
- [ ] Path, query, and body parameters specified
- [ ] Status codes and meanings explained
- [ ] Content types specified

### Authentication
- [ ] Authentication methods documented
- [ ] JWT/OAuth2 configuration explained
- [ ] Security annotations documented
- [ ] Token management explained

### Request/Response
- [ ] DTO classes documented
- [ ] Jackson/Gson annotations explained
- [ ] Validation annotations shown
- [ ] Example JSON payloads provided

### Error Handling
- [ ] Exception hierarchy documented
- [ ] Error response format specified
- [ ] HTTP status code mappings
- [ ] Common error scenarios covered

### Examples
- [ ] Working Java client examples
- [ ] Spring RestTemplate/WebClient examples
- [ ] OkHttp/Apache HttpClient examples
- [ ] Complete integration examples

### Best Practices
- [ ] Rate limiting documented
- [ ] Pagination patterns explained
- [ ] API versioning strategy
- [ ] Performance considerations

## Prompt Template

~~~markdown
# Java API Documentation Request

Generate comprehensive API documentation following this protocol:

## Phase 1: OpenAPI with Springdoc

```yaml
openapi: 3.0.3
info:
  title: Java API
  version: 1.0.0

paths:
  /api/v1/users:
    get:
      tags: [Users]
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 0
        - name: size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PageUsers'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
          format: int64
        email:
          type: string
        name:
          type: string

    PageUsers:
      type: object
      properties:
        content:
          type: array
          items:
            $ref: '#/components/schemas/User'
        page:
          type: integer
        size:
          type: integer
        totalElements:
          type: integer
```

## Phase 2: Spring Boot API Implementation

### Controller
```java
@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "Users", description = "User management APIs")
public class UserController {

    private final UserService userService;

    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    @Operation(summary = "List users", description = "Get paginated list of users")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Success"),
        @ApiResponse(responseCode = "401", description = "Unauthorized")
    })
    public ResponseEntity<Page<UserResponse>> listUsers(
            @Parameter(description = "Page number") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "20") int size) {

        Pageable pageable = PageRequest.of(page, size);
        Page<UserResponse> users = userService.listUsers(pageable);
        return ResponseEntity.ok(users);
    }

    @PostMapping
    @Operation(summary = "Create user")
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {

        UserResponse user = userService.createUser(request);
        URI location = ServletUriComponentsBuilder
            .fromCurrentRequest()
            .path("/{id}")
            .buildAndExpand(user.getId())
            .toUri();

        return ResponseEntity.created(location).body(user);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```

### DTOs with Validation
```java
public class CreateUserRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Email must be valid")
    private String email;

    @NotBlank(message = "Name is required")
    @Size(min = 1, max = 100)
    private String name;

    @NotBlank
    @Size(min = 8, message = "Password must be at least 8 characters")
    private String password;

    // Getters and setters
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserResponse {
    private Long id;
    private String email;
    private String name;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'")
    private LocalDateTime createdAt;
}
```

## Phase 3: Java Client Examples

### RestTemplate Client
```java
@Service
public class UserApiClient {
    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String apiKey;

    public UserApiClient(RestTemplateBuilder builder,
                         @Value("${api.base-url}") String baseUrl,
                         @Value("${api.key}") String apiKey) {
        this.restTemplate = builder
            .setConnectTimeout(Duration.ofSeconds(5))
            .setReadTimeout(Duration.ofSeconds(30))
            .build();
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    public Page<UserResponse> listUsers(int page, int size) {
        String url = UriComponentsBuilder.fromHttpUrl(baseUrl + "/users")
            .queryParam("page", page)
            .queryParam("size", size)
            .toUriString();

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(apiKey);
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        try {
            ResponseEntity<PageImpl<UserResponse>> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                request,
                new ParameterizedTypeReference<PageImpl<UserResponse>>() {}
            );
            return response.getBody();
        } catch (HttpClientErrorException e) {
            handleClientError(e);
            throw e;
        } catch (HttpServerErrorException e) {
            log.error("Server error: {}", e.getMessage());
            throw e;
        }
    }

    public UserResponse createUser(CreateUserRequest userRequest) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(apiKey);
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<CreateUserRequest> request = new HttpEntity<>(userRequest, headers);

        ResponseEntity<UserResponse> response = restTemplate.postForEntity(
            baseUrl + "/users",
            request,
            UserResponse.class
        );

        return response.getBody();
    }

    private void handleClientError(HttpClientErrorException e) {
        if (e.getStatusCode() == HttpStatus.UNAUTHORIZED) {
            throw new AuthenticationException("Invalid API key");
        } else if (e.getStatusCode() == HttpStatus.BAD_REQUEST) {
            // Parse error response
            try {
                ErrorResponse error = objectMapper.readValue(
                    e.getResponseBodyAsString(),
                    ErrorResponse.class
                );
                throw new ValidationException(error.getMessage());
            } catch (IOException ex) {
                throw new RuntimeException("Failed to parse error response", ex);
            }
        }
    }
}
```

### WebClient (Reactive)
```java
@Service
public class ReactiveUserApiClient {
    private final WebClient webClient;

    public ReactiveUserApiClient(WebClient.Builder builder,
                                 @Value("${api.base-url}") String baseUrl,
                                 @Value("${api.key}") String apiKey) {
        this.webClient = builder
            .baseUrl(baseUrl)
            .defaultHeader("Authorization", "Bearer " + apiKey)
            .build();
    }

    public Mono<Page<UserResponse>> listUsers(int page, int size) {
        return webClient.get()
            .uri(uriBuilder -> uriBuilder
                .path("/users")
                .queryParam("page", page)
                .queryParam("size", size)
                .build())
            .retrieve()
            .onStatus(HttpStatus::is4xxClientError, response ->
                response.bodyToMono(ErrorResponse.class)
                    .flatMap(error -> Mono.error(
                        new ApiException(error.getMessage())
                    ))
            )
            .bodyToMono(new ParameterizedTypeReference<PageImpl<UserResponse>>() {});
    }

    public Mono<UserResponse> createUser(CreateUserRequest request) {
        return webClient.post()
            .uri("/users")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .retrieve()
            .bodyToMono(UserResponse.class)
            .retryWhen(Retry.backoff(3, Duration.ofSeconds(1))
                .filter(throwable -> throwable instanceof WebClientRequestException));
    }
}
```

### OkHttp Client
```java
public class OkHttpUserClient {
    private final OkHttpClient client;
    private final String baseUrl;
    private final String apiKey;
    private final ObjectMapper objectMapper;

    public OkHttpUserClient(String baseUrl, String apiKey) {
        this.client = new OkHttpClient.Builder()
            .connectTimeout(5, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(new RetryInterceptor(3))
            .build();
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule());
    }

    public Page<UserResponse> listUsers(int page, int size) throws IOException {
        HttpUrl url = HttpUrl.parse(baseUrl + "/users")
            .newBuilder()
            .addQueryParameter("page", String.valueOf(page))
            .addQueryParameter("size", String.valueOf(size))
            .build();

        Request request = new Request.Builder()
            .url(url)
            .addHeader("Authorization", "Bearer " + apiKey)
            .get()
            .build();

        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected response: " + response);
            }

            String responseBody = response.body().string();
            JavaType type = objectMapper.getTypeFactory()
                .constructParametricType(PageImpl.class, UserResponse.class);
            return objectMapper.readValue(responseBody, type);
        }
    }

    public UserResponse createUser(CreateUserRequest userRequest) throws IOException {
        String json = objectMapper.writeValueAsString(userRequest);
        RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));

        Request request = new Request.Builder()
            .url(baseUrl + "/users")
            .addHeader("Authorization", "Bearer " + apiKey)
            .post(body)
            .build();

        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected response: " + response);
            }
            return objectMapper.readValue(response.body().string(), UserResponse.class);
        }
    }
}
```

## Phase 4: Security Configuration

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.decoder(jwtDecoder()))
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            );

        return http.build();
    }

    @Bean
    public JwtDecoder jwtDecoder() {
        return NimbusJwtDecoder.withPublicKey(publicKey).build();
    }
}
```

## Phase 5: Testing

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void createUser_ValidRequest_ReturnsCreated() throws Exception {
        CreateUserRequest request = new CreateUserRequest(
            "test@example.com",
            "Test User",
            "password123"
        );

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.email").value("test@example.com"))
            .andExpect(header().exists("Location"));
    }

    @Test
    void listUsers_ReturnsPagedResults() throws Exception {
        mockMvc.perform(get("/api/v1/users")
                .param("page", "0")
                .param("size", "10"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").isArray())
            .andExpect(jsonPath("$.page").exists());
    }
}
```
```

---

## Best Practices

1. **Use Spring Boot Starters**: Leverage spring-boot-starter-web for REST APIs
2. **Validation**: Use Jakarta Bean Validation (@Valid, @NotNull, etc.)
3. **DTOs**: Separate DTOs from entities, use MapStruct for mapping
4. **Exception Handling**: Use @ControllerAdvice for global error handling
5. **Pagination**: Use Spring Data's Page/Pageable
6. **Documentation**: Use Springdoc OpenAPI for automatic doc generation
7. **Testing**: Write integration tests with MockMvc
8. **Security**: Implement OAuth2/JWT with Spring Security

---
~~~

## Output Format Specifications

The API documentation should:
- Follow OpenAPI 3.0 standards
- Include Spring Boot-specific annotations
- Provide multiple Java client examples
- Document validation and error handling
- Show security configuration
- Include testing examples
- Target Java/Spring developers
