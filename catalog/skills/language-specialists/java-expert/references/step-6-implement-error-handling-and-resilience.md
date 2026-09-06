### Step 6: Implement Error Handling and Resilience

**Custom Exception Hierarchy**:

```java
// Base application exception
public abstract class ApplicationException extends RuntimeException {
    private final String errorCode;

    protected ApplicationException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    protected ApplicationException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() { return errorCode; }
}

// Specific exception types
public class ResourceNotFoundException extends ApplicationException {
    public ResourceNotFoundException(String resourceType, Object id) {
        super("NOT_FOUND", "%s not found with id: %s".formatted(resourceType, id));
    }
}

public class BusinessRuleException extends ApplicationException {
    public BusinessRuleException(String rule, String detail) {
        super("BUSINESS_RULE_VIOLATION", "Rule '%s' violated: %s".formatted(rule, detail));
    }
}

// Global exception handler with @ControllerAdvice
@RestControllerAdvice
public class GlobalExceptionHandler {

    record ErrorResponse(String code, String message, Instant timestamp) {}

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ResourceNotFoundException ex) {
        return new ErrorResponse(ex.getErrorCode(), ex.getMessage(), Instant.now());
    }

    @ExceptionHandler(BusinessRuleException.class)
    @ResponseStatus(HttpStatus.UNPROCESSABLE_ENTITY)
    public ErrorResponse handleBusinessRule(BusinessRuleException ex) {
        return new ErrorResponse(ex.getErrorCode(), ex.getMessage(), Instant.now());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        String details = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return new ErrorResponse("VALIDATION_ERROR", details, Instant.now());
    }
}
```

**Result Pattern and Resilience4j**:

```java
// Result type (Either pattern) for explicit error handling without exceptions
public sealed interface Result<T> permits Result.Success, Result.Failure {

    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}

    static <T> Result<T> success(T value) { return new Success<>(value); }
    static <T> Result<T> failure(String error) { return new Failure<>(error); }

    default <R> Result<R> map(Function<T, R> fn) {
        return switch (this) {
            case Success<T> s -> Result.success(fn.apply(s.value()));
            case Failure<T> f -> Result.failure(f.error());
        };
    }

    default <R> Result<R> flatMap(Function<T, Result<R>> fn) {
        return switch (this) {
            case Success<T> s -> fn.apply(s.value());
            case Failure<T> f -> Result.failure(f.error());
        };
    }

    default T orElse(T fallback) {
        return switch (this) {
            case Success<T> s -> s.value();
            case Failure<T> f -> fallback;
        };
    }
}

// Usage
Result<User> result = validateInput(request)
    .flatMap(this::findUser)
    .map(this::enrichProfile);

// Resilience4j: retry with exponential backoff
RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(500))
    .retryExceptions(IOException.class, TimeoutException.class)
    .ignoreExceptions(BusinessRuleException.class)
    .build();

Retry retry = Retry.of("paymentService", retryConfig);

Supplier<PaymentResult> supplier = Retry.decorateSupplier(retry,
    () -> paymentGateway.charge(amount));
PaymentResult result = supplier.get();

// Resilience4j: circuit breaker
CircuitBreakerConfig cbConfig = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .slidingWindowSize(10)
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("inventoryService", cbConfig);

Supplier<Inventory> decorated = CircuitBreaker.decorateSupplier(circuitBreaker,
    () -> inventoryService.check(productId));
```
