### Step 2: Set Up Database Integration Tests with Testcontainers

**Python (pytest + testcontainers):**
```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def postgres():
    """Start a PostgreSQL container for the test module."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture
def db_session(postgres):
    """Create a fresh database session with transaction rollback."""
    engine = create_engine(postgres.get_connection_url())
    # Run migrations
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_email TEXT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class TestOrderRepository:
    """Database integration tests using a real PostgreSQL container."""

    def test_create_order(self, db_session):
        repo = OrderRepository(db_session)
        order = repo.create(
            customer_email="alice@example.com",
            total_amount=99.99,
        )
        assert order.id is not None
        assert order.status == "pending"

    def test_find_orders_by_customer(self, db_session):
        repo = OrderRepository(db_session)
        repo.create(customer_email="bob@example.com", total_amount=50.00)
        repo.create(customer_email="bob@example.com", total_amount=75.00)
        repo.create(customer_email="carol@example.com", total_amount=100.00)

        bob_orders = repo.find_by_customer("bob@example.com")
        assert len(bob_orders) == 2

    def test_update_order_status(self, db_session):
        repo = OrderRepository(db_session)
        order = repo.create(
            customer_email="dave@example.com",
            total_amount=200.00,
        )
        updated = repo.update_status(order.id, "shipped")
        assert updated.status == "shipped"

    def test_transaction_rollback_on_error(self, db_session):
        repo = OrderRepository(db_session)
        repo.create(customer_email="eve@example.com", total_amount=50.00)

        with pytest.raises(ValueError):
            repo.update_status(99999, "shipped")  # Non-existent order

        # Original order should still exist despite the error
        orders = repo.find_by_customer("eve@example.com")
        assert len(orders) == 1
```

**JavaScript (Jest + testcontainers):**
```javascript
const { GenericContainer } = require("testcontainers");
const { Client } = require("pg");

let container;
let client;

beforeAll(async () => {
  container = await new GenericContainer("postgres:16-alpine")
    .withEnvironment({
      POSTGRES_USER: "test",
      POSTGRES_PASSWORD: "test",
      POSTGRES_DB: "testdb",
    })
    .withExposedPorts(5432)
    .start();

  client = new Client({
    host: container.getHost(),
    port: container.getMappedPort(5432),
    user: "test",
    password: "test",
    database: "testdb",
  });
  await client.connect();

  await client.query(`
    CREATE TABLE orders (
      id SERIAL PRIMARY KEY,
      customer_email TEXT NOT NULL,
      total_amount DECIMAL(10, 2) NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TIMESTAMP DEFAULT NOW()
    )
  `);
}, 60000);

afterAll(async () => {
  await client.end();
  await container.stop();
});

afterEach(async () => {
  await client.query("DELETE FROM orders");
});

describe("OrderRepository with PostgreSQL", () => {
  test("creates an order", async () => {
    const result = await client.query(
      "INSERT INTO orders (customer_email, total_amount) VALUES ($1, $2) RETURNING *",
      ["alice@example.com", 99.99]
    );
    expect(result.rows[0].customer_email).toBe("alice@example.com");
    expect(result.rows[0].status).toBe("pending");
  });

  test("finds orders by customer email", async () => {
    await client.query(
      "INSERT INTO orders (customer_email, total_amount) VALUES ($1, $2), ($1, $3)",
      ["bob@example.com", 50.0, 75.0]
    );
    const result = await client.query(
      "SELECT * FROM orders WHERE customer_email = $1",
      ["bob@example.com"]
    );
    expect(result.rows).toHaveLength(2);
  });
});
```

**Java (JUnit 5 + Testcontainers):**
```java
import org.junit.jupiter.api.*;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import javax.sql.DataSource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
class OrderRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");

    private JdbcTemplate jdbc;
    private OrderRepository repo;

    @BeforeEach
    void setUp() {
        var ds = new DriverManagerDataSource();
        ds.setUrl(postgres.getJdbcUrl());
        ds.setUsername(postgres.getUsername());
        ds.setPassword(postgres.getPassword());
        jdbc = new JdbcTemplate(ds);

        jdbc.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_email TEXT NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """);
        repo = new OrderRepository(jdbc);
    }

    @AfterEach
    void tearDown() {
        jdbc.execute("DELETE FROM orders");
    }

    @Test
    void createOrderPersistsToDatabase() {
        var order = repo.create("alice@example.com", java.math.BigDecimal.valueOf(99.99));
        assertNotNull(order.getId());
        assertEquals("pending", order.getStatus());
    }

    @Test
    void findOrdersByCustomerReturnsMatchingRows() {
        repo.create("bob@example.com", java.math.BigDecimal.valueOf(50));
        repo.create("bob@example.com", java.math.BigDecimal.valueOf(75));
        repo.create("carol@example.com", java.math.BigDecimal.valueOf(100));

        var bobOrders = repo.findByCustomer("bob@example.com");
        assertEquals(2, bobOrders.size());
    }
}
```
