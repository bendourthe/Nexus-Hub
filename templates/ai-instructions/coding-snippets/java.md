## Java Conventions

**Tooling**:
- **Build**: Maven or Gradle
- **Linting**: Checkstyle, SpotBugs
- **Formatting**: Google Java Format
- **Target**: Java 17+ (records, text blocks, switch expressions, `var`)

**Naming**: `camelCase` for methods/variables, `PascalCase` for classes/interfaces, `UPPER_CASE` for constants

**Code Patterns**:
- Try-with-resources for all closeable resources
- `Optional<T>` for return types to avoid nulls
- Stream API for collections processing where readable
- Single responsibility per class
- Unchecked exceptions for recovery failures; checked only for mandatory handling
- JPA/PreparedStatements for SQL (never string concatenation)

**Testing**: JUnit 5 (Jupiter) with Mockito for mocking.

```java
class CalculatorTest {
    @Test
    void shouldAddNumbers() {
        var calculator = new Calculator();
        assertEquals(5, calculator.add(2, 3));
    }
}
```
