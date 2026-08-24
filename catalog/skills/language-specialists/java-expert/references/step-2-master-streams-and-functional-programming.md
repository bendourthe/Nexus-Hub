### Step 2: Master Streams and Functional Programming

**Stream API Fundamentals**:

```java
// Transforming and filtering
List<String> activeEmails = users.stream()
    .filter(u -> u.joinDate().isAfter(LocalDate.of(2024, 1, 1)))
    .map(User::email)
    .sorted()
    .toList();   // Java 16+; use .collect(Collectors.toList()) for older versions

// FlatMap for nested structures
record Order(String id, List<LineItem> items) {}
record LineItem(String product, int quantity, BigDecimal price) {}

List<LineItem> allItems = orders.stream()
    .flatMap(order -> order.items().stream())
    .filter(item -> item.quantity() > 0)
    .toList();

// Reduce for aggregation
BigDecimal total = allItems.stream()
    .map(item -> item.price().multiply(BigDecimal.valueOf(item.quantity())))
    .reduce(BigDecimal.ZERO, BigDecimal::add);

// Grouping and partitioning with Collectors
Map<String, List<LineItem>> byProduct = allItems.stream()
    .collect(Collectors.groupingBy(LineItem::product));

Map<Boolean, List<LineItem>> partitioned = allItems.stream()
    .collect(Collectors.partitioningBy(item -> item.quantity() > 10));

// Downstream collectors
Map<String, Long> countByProduct = allItems.stream()
    .collect(Collectors.groupingBy(LineItem::product, Collectors.counting()));

Map<String, BigDecimal> revenueByProduct = allItems.stream()
    .collect(Collectors.groupingBy(
        LineItem::product,
        Collectors.reducing(
            BigDecimal.ZERO,
            item -> item.price().multiply(BigDecimal.valueOf(item.quantity())),
            BigDecimal::add
        )
    ));
```

**Optional and Method References**:

```java
// Optional as return type (never as field or parameter)
public Optional<User> findByEmail(String email) {
    return users.stream()
        .filter(u -> u.email().equalsIgnoreCase(email))
        .findFirst();
}

// Chaining Optional operations
String displayName = findByEmail("alice@example.com")
    .map(User::displayName)
    .orElse("Unknown User");

// Optional with flatMap for nested optionals
Optional<String> city = findByEmail("alice@example.com")
    .flatMap(this::findAddress)
    .map(Address::city);

// orElseThrow for mandatory values
User user = findByEmail(email)
    .orElseThrow(() -> new UserNotFoundException("no user with email: " + email));

// Method references in four forms
users.stream().map(User::name);                    // instance method via type
users.stream().forEach(System.out::println);       // instance method via object
users.stream().map(String::valueOf);               // static method
users.stream().map(UserDto::new);                  // constructor reference
```

**Custom Collectors and Parallel Streams**:

```java
// Custom collector: join strings with prefix, delimiter, suffix
Collector<CharSequence, ?, String> csvCollector =
    Collectors.joining(", ", "[", "]");

String csv = users.stream()
    .map(User::name)
    .collect(csvCollector);  // "[Alice, Bob, Charlie]"

// Custom collector: collecting to an immutable map
Collector<User, ?, Map<String, User>> toUserMap =
    Collectors.toUnmodifiableMap(User::email, Function.identity());

// Parallel streams (use only for CPU-bound work on large datasets)
long count = IntStream.range(0, 10_000_000)
    .parallel()
    .filter(n -> isPrime(n))
    .count();

// Avoid parallel streams when:
// - The data set is small (overhead outweighs benefit)
// - Operations have side effects or shared mutable state
// - The source is not efficiently splittable (e.g., LinkedList, Stream.iterate)
```
