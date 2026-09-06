### Step 3: Leverage Generics, Delegates, and Events

**Generic Constraints and Covariance/Contravariance**:

```csharp
// Multiple constraints on a generic type
public class Repository<T> where T : class, IEntity, new()
{
    public T Create()
    {
        var entity = new T(); // Possible because of new() constraint
        entity.CreatedAt = DateTime.UtcNow;
        return entity;
    }

    public async Task<T?> FindAsync(int id, CancellationToken ct = default)
    {
        return await _dbContext.Set<T>().FindAsync(new object[] { id }, ct);
    }
}

// Covariance (out): IEnumerable<Derived> can be used as IEnumerable<Base>
IEnumerable<string> strings = new List<string> { "a", "b" };
IEnumerable<object> objects = strings; // Covariant: out T

// Contravariance (in): Action<Base> can be used as Action<Derived>
Action<object> printObject = obj => Console.WriteLine(obj);
Action<string> printString = printObject; // Contravariant: in T

// Custom covariant interface
public interface IReadOnlyRepository<out T> where T : class
{
    Task<T?> FindAsync(int id);
    Task<IReadOnlyList<T>> GetAllAsync();
}

// Custom contravariant interface
public interface IComparer<in T>
{
    int Compare(T x, T y);
}
```

**Func, Action, and Custom Delegates**:

```csharp
// Func<T, TResult> for transformations
public async Task<TResult> ExecuteWithRetryAsync<TResult>(
    Func<CancellationToken, Task<TResult>> operation,
    int maxRetries = 3,
    CancellationToken ct = default)
{
    for (int attempt = 0; ; attempt++)
    {
        try
        {
            return await operation(ct);
        }
        catch (Exception ex) when (attempt < maxRetries - 1)
        {
            var delay = TimeSpan.FromSeconds(Math.Pow(2, attempt));
            await Task.Delay(delay, ct);
        }
    }
}

// Action<T> for side effects
public void ForEach<T>(IEnumerable<T> items, Action<T> action)
{
    foreach (var item in items)
        action(item);
}

// Predicate<T> for filtering
public List<T> Filter<T>(IEnumerable<T> source, Predicate<T> predicate)
{
    return source.Where(item => predicate(item)).ToList();
}
```

**Event Patterns**:

```csharp
// Standard .NET event pattern
public class OrderProcessor
{
    public event EventHandler<OrderEventArgs>? OrderCompleted;
    public event EventHandler<OrderEventArgs>? OrderFailed;

    protected virtual void OnOrderCompleted(OrderEventArgs e)
    {
        OrderCompleted?.Invoke(this, e);
    }

    public async Task ProcessAsync(Order order, CancellationToken ct = default)
    {
        try
        {
            await ValidateAsync(order, ct);
            await ChargePaymentAsync(order, ct);
            await FulfillAsync(order, ct);

            OnOrderCompleted(new OrderEventArgs(order, OrderStatus.Completed));
        }
        catch (Exception ex)
        {
            OrderFailed?.Invoke(this, new OrderEventArgs(order, OrderStatus.Failed, ex));
            throw;
        }
    }
}

public class OrderEventArgs : EventArgs
{
    public Order Order { get; }
    public OrderStatus Status { get; }
    public Exception? Error { get; }

    public OrderEventArgs(Order order, OrderStatus status, Exception? error = null)
    {
        Order = order;
        Status = status;
        Error = error;
    }
}
```
