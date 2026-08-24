### Step 2: Achieve LINQ Mastery

**Query Syntax vs Method Syntax**:

```csharp
// Query syntax (reads like SQL, good for joins and grouping)
var expensiveOrders = from o in orders
                      where o.Total > 1000m
                      orderby o.CreatedAt descending
                      select new { o.Id, o.Total, o.Customer.Name };

// Equivalent method syntax (more flexible, composable)
var expensiveOrders = orders
    .Where(o => o.Total > 1000m)
    .OrderByDescending(o => o.CreatedAt)
    .Select(o => new { o.Id, o.Total, o.Customer.Name });

// Join with method syntax
var orderDetails = customers
    .Join(orders,
        c => c.Id,
        o => o.CustomerId,
        (c, o) => new { Customer = c.Name, o.Total, o.CreatedAt })
    .Where(x => x.Total > 500m)
    .ToList();

// GroupBy with aggregation
var salesByRegion = orders
    .GroupBy(o => o.Region)
    .Select(g => new
    {
        Region = g.Key,
        TotalSales = g.Sum(o => o.Total),
        OrderCount = g.Count(),
        AverageOrder = g.Average(o => o.Total)
    })
    .OrderByDescending(x => x.TotalSales);
```

**Deferred Execution and Custom Extension Methods**:

```csharp
// Deferred execution: the query is not evaluated until enumerated
IEnumerable<Order> query = orders.Where(o => o.Total > 100m);
// Nothing has executed yet; adding more items to orders will be reflected

var results = query.ToList(); // NOW it executes

// Custom extension method for reusable LINQ operators
public static class EnumerableExtensions
{
    public static IEnumerable<T> WhereNotNull<T>(this IEnumerable<T?> source) where T : class
    {
        return source.Where(item => item is not null)!;
    }

    public static IEnumerable<IEnumerable<T>> Batch<T>(this IEnumerable<T> source, int size)
    {
        var batch = new List<T>(size);
        foreach (var item in source)
        {
            batch.Add(item);
            if (batch.Count == size)
            {
                yield return batch;
                batch = new List<T>(size);
            }
        }
        if (batch.Count > 0)
            yield return batch;
    }
}

// Usage
var validNames = users.Select(u => u.Email).WhereNotNull().ToList();
var batches = records.Batch(100);
```

**Expression Trees**:

```csharp
// Build dynamic filters with Expression trees
public static class PredicateBuilder
{
    public static Expression<Func<T, bool>> And<T>(
        this Expression<Func<T, bool>> left,
        Expression<Func<T, bool>> right)
    {
        var parameter = Expression.Parameter(typeof(T));
        var body = Expression.AndAlso(
            Expression.Invoke(left, parameter),
            Expression.Invoke(right, parameter));
        return Expression.Lambda<Func<T, bool>>(body, parameter);
    }
}

// Dynamic query building for search filters
Expression<Func<Product, bool>> predicate = p => true;

if (!string.IsNullOrEmpty(filter.Name))
    predicate = predicate.And(p => p.Name.Contains(filter.Name));
if (filter.MinPrice.HasValue)
    predicate = predicate.And(p => p.Price >= filter.MinPrice.Value);

var results = await _dbContext.Products.Where(predicate).ToListAsync(ct);
```
