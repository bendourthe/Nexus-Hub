### Step 3: Design Type-Safe Generics

**Bounded Type Parameters and Wildcards**:

```java
// Upper bounded type parameter
public static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

// Multiple bounds
public static <T extends Serializable & Comparable<T>> void process(T item) {
    // T must implement both Serializable and Comparable
}

// Wildcards: PECS (Producer Extends, Consumer Super)
// Use extends when you READ from a structure
public static double sum(List<? extends Number> numbers) {
    return numbers.stream()
        .mapToDouble(Number::doubleValue)
        .sum();
}

// Use super when you WRITE to a structure
public static void addIntegers(List<? super Integer> list) {
    list.add(1);
    list.add(2);
    list.add(3);
}

// Unbounded wildcard for read-only generic operations
public static void printAll(List<?> items) {
    for (Object item : items) {
        System.out.println(item);
    }
}
```

**Generic Methods and Type Tokens**:

```java
// Generic method with inferred types
public static <K, V> Map<K, V> mapOf(K key, V value) {
    return Map.of(key, value);
}

// Type-safe heterogeneous container using type tokens
public class TypeSafeRegistry {
    private final Map<Class<?>, Object> map = new ConcurrentHashMap<>();

    public <T> void put(Class<T> type, T instance) {
        map.put(Objects.requireNonNull(type), instance);
    }

    public <T> T get(Class<T> type) {
        return type.cast(map.get(type));
    }
}

// Usage
var registry = new TypeSafeRegistry();
registry.put(String.class, "hello");
registry.put(Integer.class, 42);
String s = registry.get(String.class);  // type-safe, no cast needed

// Generic interface with self-referential bound (Comparable pattern)
public interface Builder<T extends Builder<T>> {
    T withName(String name);
    T withAge(int age);
}

public class PersonBuilder implements Builder<PersonBuilder> {
    private String name;
    private int age;

    @Override
    public PersonBuilder withName(String name) {
        this.name = name;
        return this;
    }

    @Override
    public PersonBuilder withAge(int age) {
        this.age = age;
        return this;
    }

    public Person build() {
        return new Person(name, age);
    }
}
```

**Type Erasure Workarounds**:

```java
// Problem: cannot do "new T()" or "T.class" due to erasure
// Solution 1: Pass Class<T> as a parameter
public static <T> T createInstance(Class<T> type) throws Exception {
    return type.getDeclaredConstructor().newInstance();
}

// Solution 2: Use a Supplier<T> factory
public static <T> List<T> createList(int size, Supplier<T> factory) {
    return IntStream.range(0, size)
        .mapToObj(i -> factory.get())
        .collect(Collectors.toList());
}

List<StringBuilder> builders = createList(5, StringBuilder::new);

// Solution 3: TypeReference pattern (used by Jackson, Spring)
public abstract class TypeReference<T> {
    private final Type type;

    protected TypeReference() {
        Type superclass = getClass().getGenericSuperclass();
        this.type = ((ParameterizedType) superclass).getActualTypeArguments()[0];
    }

    public Type getType() { return type; }
}

// Usage with Jackson
List<User> users = objectMapper.readValue(json,
    new TypeReference<List<User>>() {});
```
