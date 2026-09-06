### Step 1: Leverage Modern Java Features

**Records for Immutable Data**:

```java
// Records eliminate boilerplate for data carriers (Java 16+)
public record User(String name, String email, LocalDate joinDate) {

    // Compact constructor for validation
    public User {
        Objects.requireNonNull(name, "name must not be null");
        Objects.requireNonNull(email, "email must not be null");
        if (!email.contains("@")) {
            throw new IllegalArgumentException("invalid email: " + email);
        }
    }

    // Custom accessor
    public String displayName() {
        return name + " <" + email + ">";
    }
}

// Records work naturally with collections and streams
List<User> users = List.of(
    new User("Alice", "alice@example.com", LocalDate.of(2024, 1, 15)),
    new User("Bob", "bob@example.com", LocalDate.of(2024, 3, 22))
);

// Destructure in local variable declarations
var user = new User("Alice", "alice@example.com", LocalDate.now());
String name = user.name();   // accessor, not getName()
String email = user.email();
```

**Sealed Classes and Pattern Matching**:

```java
// Sealed classes restrict which classes can extend them (Java 17+)
public sealed interface Shape permits Circle, Rectangle, Triangle {
    double area();
}

public record Circle(double radius) implements Shape {
    public double area() { return Math.PI * radius * radius; }
}

public record Rectangle(double width, double height) implements Shape {
    public double area() { return width * height; }
}

public record Triangle(double base, double height) implements Shape {
    public double area() { return 0.5 * base * height; }
}

// Pattern matching for instanceof (Java 16+)
public static String describe(Object obj) {
    if (obj instanceof String s && s.length() > 5) {
        return "long string: " + s;
    } else if (obj instanceof Integer i && i > 0) {
        return "positive int: " + i;
    }
    return "unknown: " + obj;
}

// Pattern matching for switch (Java 21+)
public static String formatShape(Shape shape) {
    return switch (shape) {
        case Circle c when c.radius() > 100 -> "large circle, r=" + c.radius();
        case Circle c    -> "circle, r=" + c.radius();
        case Rectangle r -> "rectangle, %sx%s".formatted(r.width(), r.height());
        case Triangle t  -> "triangle, base=" + t.base();
    };
}
```

**Text Blocks and Virtual Threads**:

```java
// Text blocks for multi-line strings (Java 15+)
String json = """
        {
            "name": "%s",
            "email": "%s",
            "active": true
        }
        """.formatted(user.name(), user.email());

String sql = """
        SELECT u.id, u.name, u.email
        FROM users u
        JOIN orders o ON o.user_id = u.id
        WHERE o.status = 'ACTIVE'
        ORDER BY u.name
        """;

// Virtual threads (Java 21+, Project Loom)
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<String>> futures = urls.stream()
        .map(url -> executor.submit(() -> fetchUrl(url)))
        .toList();

    List<String> results = new ArrayList<>();
    for (var future : futures) {
        results.add(future.get());
    }
}

// var for local type inference (Java 10+)
var users = new ArrayList<User>();           // ArrayList<User>
var counts = Map.of("a", 1, "b", 2);        // Map<String, Integer>
var stream = users.stream().filter(u -> u.name().startsWith("A")); // Stream<User>
```
