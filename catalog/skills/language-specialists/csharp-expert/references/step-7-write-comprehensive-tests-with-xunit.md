### Step 7: Write Comprehensive Tests with xUnit

**Fact and Theory Tests**:

```csharp
public class OrderCalculatorTests
{
    // Single test case
    [Fact]
    public void CalculateTotal_WithEmptyItems_ReturnsZero()
    {
        var calculator = new OrderCalculator();
        var result = calculator.CalculateTotal(Array.Empty<OrderItem>());
        Assert.Equal(0m, result);
    }

    // Parameterized tests with InlineData
    [Theory]
    [InlineData(100, 0.10, 90)]
    [InlineData(200, 0.25, 150)]
    [InlineData(50, 0, 50)]
    public void ApplyDiscount_WithVariousInputs_ReturnsExpected(
        decimal price, decimal discount, decimal expected)
    {
        var calculator = new OrderCalculator();
        var result = calculator.ApplyDiscount(price, discount);
        Assert.Equal(expected, result);
    }

    // Complex test data with ClassData
    [Theory]
    [ClassData(typeof(BulkOrderTestData))]
    public void CalculateTotal_WithBulkOrders_AppliesTierPricing(
        List<OrderItem> items, decimal expected)
    {
        var calculator = new OrderCalculator();
        var result = calculator.CalculateTotal(items);
        Assert.Equal(expected, result);
    }
}

public class BulkOrderTestData : IEnumerable<object[]>
{
    public IEnumerator<object[]> GetEnumerator()
    {
        yield return new object[]
        {
            new List<OrderItem> { new("Widget", 10, 5.00m) },
            50.00m
        };
        yield return new object[]
        {
            new List<OrderItem> { new("Widget", 100, 5.00m) },
            450.00m // 10% bulk discount
        };
    }

    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}
```

**Fixtures and Mocking with Moq**:

```csharp
// Shared test fixture for expensive setup (database, config)
public class DatabaseFixture : IAsyncLifetime
{
    public AppDbContext DbContext { get; private set; } = null!;

    public async Task InitializeAsync()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        DbContext = new AppDbContext(options);
        await DbContext.Database.EnsureCreatedAsync();
    }

    public async Task DisposeAsync()
    {
        await DbContext.DisposeAsync();
    }
}

// Use the fixture via IClassFixture<T>
public class OrderServiceTests : IClassFixture<DatabaseFixture>
{
    private readonly DatabaseFixture _fixture;

    public OrderServiceTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public async Task PlaceOrder_WithValidData_ReturnsSuccess()
    {
        // Arrange
        var mockEmailSender = new Mock<IEmailSender>();
        mockEmailSender
            .Setup(x => x.SendAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        var mockLogger = new Mock<ILogger<OrderService>>();

        var service = new OrderService(
            new SqlOrderRepository(_fixture.DbContext),
            mockEmailSender.Object,
            mockLogger.Object);

        var request = new CreateOrderRequest(CustomerId: 1, Items: new[] { new OrderItemDto("Widget", 5) });

        // Act
        var result = await service.PlaceOrderAsync(request, CancellationToken.None);

        // Assert
        Assert.True(result.IsSuccess);
        mockEmailSender.Verify(
            x => x.SendAsync("order-confirmation", It.IsAny<string>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
```

**FluentAssertions and Integration Testing**:

```csharp
// FluentAssertions for readable assertions
using FluentAssertions;

[Fact]
public void Customer_WithGoldTier_ShouldHaveCorrectDiscount()
{
    var customer = new Customer("Alice", CustomerTier.Gold, yearsActive: 6);
    var discount = _calculator.CalculateDiscount(customer);

    discount.Should().Be(0.25m);
    customer.DisplayName.Should().StartWith("Alice");
    customer.Tier.Should().Be(CustomerTier.Gold);
}

[Fact]
public async Task GetOrders_ShouldReturnPagedResults()
{
    var orders = await _service.GetOrdersAsync(page: 1, pageSize: 10);

    orders.Should().NotBeNull();
    orders.Items.Should().HaveCountLessOrEqualTo(10);
    orders.Items.Should().BeInDescendingOrder(o => o.CreatedAt);
    orders.TotalCount.Should().BeGreaterThan(0);
}

// Integration testing with WebApplicationFactory
public class OrdersApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public OrdersApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real database with in-memory for tests
                services.RemoveAll<DbContextOptions<AppDbContext>>();
                services.AddDbContext<AppDbContext>(options =>
                    options.UseInMemoryDatabase("TestDb"));
            });
        }).CreateClient();
    }

    [Fact]
    public async Task GetOrders_ReturnsOkWithOrders()
    {
        var response = await _client.GetAsync("/api/orders");

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content.ReadFromJsonAsync<PagedResult<OrderDto>>();
        content.Should().NotBeNull();
        content!.Items.Should().NotBeEmpty();
    }

    [Fact]
    public async Task CreateOrder_WithInvalidData_ReturnsBadRequest()
    {
        var request = new CreateOrderRequest(CustomerId: 0, Items: Array.Empty<OrderItemDto>());
        var response = await _client.PostAsJsonAsync("/api/orders", request);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
    }
}
```
