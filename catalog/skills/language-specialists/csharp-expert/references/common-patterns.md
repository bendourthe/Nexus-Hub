## Common Patterns

### Pattern 1: Mediator with CQRS

```csharp
// Command and handler using MediatR
public record CreateOrderCommand(int CustomerId, List<OrderItemDto> Items) : IRequest<Result<int>>;

public class CreateOrderHandler : IRequestHandler<CreateOrderCommand, Result<int>>
{
    private readonly IOrderRepository _orders;
    private readonly ILogger<CreateOrderHandler> _logger;

    public CreateOrderHandler(IOrderRepository orders, ILogger<CreateOrderHandler> logger)
    {
        _orders = orders;
        _logger = logger;
    }

    public async Task<Result<int>> Handle(CreateOrderCommand command, CancellationToken ct)
    {
        var order = Order.Create(command.CustomerId, command.Items);
        await _orders.SaveAsync(order, ct);

        _logger.LogInformation("Order {OrderId} created for customer {CustomerId}",
            order.Id, command.CustomerId);

        return Result<int>.Success(order.Id);
    }
}

// Query and handler (read side)
public record GetOrderQuery(int OrderId) : IRequest<OrderDto?>;

public class GetOrderHandler : IRequestHandler<GetOrderQuery, OrderDto?>
{
    private readonly IReadOnlyRepository<Order> _orders;

    public GetOrderHandler(IReadOnlyRepository<Order> orders) => _orders = orders;

    public async Task<OrderDto?> Handle(GetOrderQuery query, CancellationToken ct)
    {
        var order = await _orders.FindAsync(query.OrderId, ct);
        return order is null ? null : OrderDto.FromDomain(order);
    }
}

// Minimal API endpoint using MediatR
app.MapPost("/api/orders", async (CreateOrderCommand command, IMediator mediator, CancellationToken ct) =>
{
    var result = await mediator.Send(command, ct);
    return result.Match(
        onSuccess: id => Results.Created($"/api/orders/{id}", new { id }),
        onFailure: error => Results.BadRequest(new { error }));
});
```

### Pattern 2: Pipeline Behavior (cross-cutting concerns)

```csharp
// Validation pipeline behavior that runs before every handler
public class ValidationBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;

    public ValidationBehavior(IEnumerable<IValidator<TRequest>> validators)
    {
        _validators = validators;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var context = new ValidationContext<TRequest>(request);
        var failures = (await Task.WhenAll(
                _validators.Select(v => v.ValidateAsync(context, ct))))
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count > 0)
            throw new ValidationException(failures.Select(f =>
                new ValidationError(f.PropertyName, f.ErrorMessage)));

        return await next();
    }
}

// Register the pipeline
builder.Services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
```
