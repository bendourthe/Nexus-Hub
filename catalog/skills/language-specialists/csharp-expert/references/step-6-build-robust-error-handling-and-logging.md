### Step 6: Build Robust Error Handling and Logging

**Custom Exception Hierarchy**:

```csharp
// Base exception for the application domain
public abstract class AppException : Exception
{
    public string Code { get; }

    protected AppException(string code, string message, Exception? inner = null)
        : base(message, inner)
    {
        Code = code;
    }
}

public class NotFoundException : AppException
{
    public NotFoundException(string entity, object id)
        : base("NOT_FOUND", $"{entity} with id '{id}' was not found") { }
}

public class ConflictException : AppException
{
    public ConflictException(string message)
        : base("CONFLICT", message) { }
}

public class ValidationException : AppException
{
    public IReadOnlyList<ValidationError> Errors { get; }

    public ValidationException(IEnumerable<ValidationError> errors)
        : base("VALIDATION_FAILED", "One or more validation errors occurred")
    {
        Errors = errors.ToList().AsReadOnly();
    }
}
```

**Result Pattern (avoiding exceptions for expected failures)**:

```csharp
// Generic Result type
public class Result<T>
{
    public T? Value { get; }
    public string? Error { get; }
    public bool IsSuccess => Error is null;

    private Result(T value) { Value = value; }
    private Result(string error) { Error = error; }

    public static Result<T> Success(T value) => new(value);
    public static Result<T> Failure(string error) => new(error);

    public TOut Match<TOut>(Func<T, TOut> onSuccess, Func<string, TOut> onFailure)
        => IsSuccess ? onSuccess(Value!) : onFailure(Error!);
}

// Usage in a service
public async Task<Result<Order>> PlaceOrderAsync(CreateOrderRequest request, CancellationToken ct)
{
    if (request.Items.Count == 0)
        return Result<Order>.Failure("Order must contain at least one item");

    var customer = await _customerRepo.FindAsync(request.CustomerId, ct);
    if (customer is null)
        return Result<Order>.Failure($"Customer {request.CustomerId} not found");

    var order = new Order(customer, request.Items);
    await _orderRepo.SaveAsync(order, ct);

    return Result<Order>.Success(order);
}

// Consume the result
var result = await _orderService.PlaceOrderAsync(request, ct);
return result.Match(
    onSuccess: order => Ok(order),
    onFailure: error => BadRequest(new { error }));
```

**Structured Logging with ILogger and Serilog**:

```csharp
// ILogger with structured logging (semantic parameters, not string interpolation)
public class OrderService
{
    private readonly ILogger<OrderService> _logger;

    public OrderService(ILogger<OrderService> logger)
    {
        _logger = logger;
    }

    public async Task ProcessAsync(Order order, CancellationToken ct)
    {
        _logger.LogInformation("Processing order {OrderId} for customer {CustomerId}",
            order.Id, order.CustomerId);

        try
        {
            await ExecuteAsync(order, ct);
            _logger.LogInformation("Order {OrderId} processed successfully in {ElapsedMs}ms",
                order.Id, stopwatch.ElapsedMilliseconds);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to process order {OrderId}", order.Id);
            throw;
        }
    }
}

// Serilog configuration in Program.cs
builder.Host.UseSerilog((context, config) => config
    .ReadFrom.Configuration(context.Configuration)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .WriteTo.Console(outputTemplate:
        "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} {Properties:j}{NewLine}{Exception}")
    .WriteTo.Seq("http://localhost:5341"));

// Global exception handling middleware
public class GlobalExceptionMiddleware : IMiddleware
{
    private readonly ILogger<GlobalExceptionMiddleware> _logger;

    public GlobalExceptionMiddleware(ILogger<GlobalExceptionMiddleware> logger)
    {
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        try
        {
            await next(context);
        }
        catch (AppException ex)
        {
            _logger.LogWarning(ex, "Application error: {ErrorCode}", ex.Code);
            context.Response.StatusCode = ex switch
            {
                NotFoundException => StatusCodes.Status404NotFound,
                ConflictException => StatusCodes.Status409Conflict,
                ValidationException => StatusCodes.Status422UnprocessableEntity,
                _ => StatusCodes.Status400BadRequest
            };
            await context.Response.WriteAsJsonAsync(new { error = ex.Code, message = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception");
            context.Response.StatusCode = StatusCodes.Status500InternalServerError;
            await context.Response.WriteAsJsonAsync(new { error = "INTERNAL_ERROR" });
        }
    }
}
```
