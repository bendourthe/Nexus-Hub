### Step 1: Master Async/Await and Task Patterns

**Task and ValueTask Basics**:

```csharp
// Async method returning Task<T> for I/O-bound work
public async Task<Customer> GetCustomerAsync(int id, CancellationToken ct = default)
{
    var customer = await _dbContext.Customers
        .FirstOrDefaultAsync(c => c.Id == id, ct);

    if (customer is null)
        throw new NotFoundException($"Customer {id} not found");

    return customer;
}

// Use ValueTask<T> when the result is often synchronous (cache hit)
private readonly ConcurrentDictionary<int, Product> _cache = new();

public ValueTask<Product> GetProductAsync(int id, CancellationToken ct = default)
{
    if (_cache.TryGetValue(id, out var cached))
        return ValueTask.FromResult(cached); // No allocation

    return new ValueTask<Product>(LoadAndCacheProductAsync(id, ct));
}

private async Task<Product> LoadAndCacheProductAsync(int id, CancellationToken ct)
{
    var product = await _repository.FindAsync(id, ct);
    _cache.TryAdd(id, product);
    return product;
}
```

**Async Streams with IAsyncEnumerable**:

```csharp
// Produce items lazily over an async stream
public async IAsyncEnumerable<LogEntry> StreamLogsAsync(
    DateTime since,
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var batch in _logSource.ReadBatchesAsync(since, ct))
    {
        foreach (var entry in batch.Entries)
        {
            ct.ThrowIfCancellationRequested();
            yield return entry;
        }
    }
}

// Consume the stream
await foreach (var log in service.StreamLogsAsync(DateTime.UtcNow.AddHours(-1), ct))
{
    Console.WriteLine($"{log.Timestamp}: {log.Message}");
}
```

**ConfigureAwait and SemaphoreSlim**:

```csharp
// Library code should use ConfigureAwait(false) to avoid deadlocks
public async Task<byte[]> DownloadAsync(string url, CancellationToken ct = default)
{
    using var client = new HttpClient();
    var response = await client.GetAsync(url, ct).ConfigureAwait(false);
    response.EnsureSuccessStatusCode();
    return await response.Content.ReadAsByteArrayAsync(ct).ConfigureAwait(false);
}

// Throttle concurrent access with SemaphoreSlim
private readonly SemaphoreSlim _semaphore = new(maxCount: 5);

public async Task<string> ThrottledRequestAsync(string url, CancellationToken ct = default)
{
    await _semaphore.WaitAsync(ct);
    try
    {
        return await _httpClient.GetStringAsync(url, ct);
    }
    finally
    {
        _semaphore.Release();
    }
}

// CancellationToken with timeout composition
public async Task ProcessWithTimeoutAsync(CancellationToken externalCt)
{
    using var cts = CancellationTokenSource.CreateLinkedTokenSource(externalCt);
    cts.CancelAfter(TimeSpan.FromSeconds(30));

    await DoWorkAsync(cts.Token); // Cancelled by either timeout or external signal
}
```
