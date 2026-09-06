### Step 5: Apply Dependency Injection and SOLID Principles

**IServiceCollection Registration**:

```csharp
// Program.cs (minimal API style)
var builder = WebApplication.CreateBuilder(args);

// Register services with appropriate lifetimes
builder.Services.AddSingleton<ICacheService, RedisCacheService>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<IOrderRepository, SqlOrderRepository>();
builder.Services.AddTransient<IEmailSender, SmtpEmailSender>();

// Register all implementations of an interface via assembly scanning
builder.Services.Scan(scan => scan
    .FromAssemblyOf<ICommandHandler>()
    .AddClasses(classes => classes.AssignableTo(typeof(ICommandHandler<>)))
    .AsImplementedInterfaces()
    .WithScopedLifetime());

// Keyed services (C# 12 / .NET 8)
builder.Services.AddKeyedSingleton<INotifier, EmailNotifier>("email");
builder.Services.AddKeyedSingleton<INotifier, SmsNotifier>("sms");
```

**Options Pattern**:

```csharp
// Strongly typed configuration with validation
public class SmtpOptions
{
    public const string SectionName = "Smtp";

    [Required]
    public string Host { get; init; } = string.Empty;
    public int Port { get; init; } = 587;
    [Required]
    public string Username { get; init; } = string.Empty;
    [Required]
    public string Password { get; init; } = string.Empty;
}

// Registration with validation
builder.Services
    .AddOptions<SmtpOptions>()
    .BindConfiguration(SmtpOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart(); // Fail fast at startup if configuration is invalid

// Inject via IOptions<T>
public class EmailSender : IEmailSender
{
    private readonly SmtpOptions _options;

    public EmailSender(IOptions<SmtpOptions> options)
    {
        _options = options.Value;
    }
}
```

**Decorator Pattern with DI**:

```csharp
// Interface segregation: small, focused interfaces
public interface IOrderRepository
{
    Task<Order?> FindAsync(int id, CancellationToken ct = default);
    Task<IReadOnlyList<Order>> GetByCustomerAsync(int customerId, CancellationToken ct = default);
    Task SaveAsync(Order order, CancellationToken ct = default);
}

// Core implementation
public class SqlOrderRepository : IOrderRepository
{
    public async Task<Order?> FindAsync(int id, CancellationToken ct = default)
        => await _dbContext.Orders.FindAsync(new object[] { id }, ct);

    // Other methods...
}

// Decorator: adds caching without modifying the original class
public class CachedOrderRepository : IOrderRepository
{
    private readonly IOrderRepository _inner;
    private readonly ICacheService _cache;

    public CachedOrderRepository(IOrderRepository inner, ICacheService cache)
    {
        _inner = inner;
        _cache = cache;
    }

    public async Task<Order?> FindAsync(int id, CancellationToken ct = default)
    {
        var cacheKey = $"order:{id}";
        var cached = await _cache.GetAsync<Order>(cacheKey, ct);
        if (cached is not null) return cached;

        var order = await _inner.FindAsync(id, ct);
        if (order is not null)
            await _cache.SetAsync(cacheKey, order, TimeSpan.FromMinutes(10), ct);

        return order;
    }

    // Delegate other methods to _inner...
}

// Register the decorator chain
builder.Services.AddScoped<SqlOrderRepository>();
builder.Services.AddScoped<IOrderRepository>(sp =>
    new CachedOrderRepository(
        sp.GetRequiredService<SqlOrderRepository>(),
        sp.GetRequiredService<ICacheService>()));
```
