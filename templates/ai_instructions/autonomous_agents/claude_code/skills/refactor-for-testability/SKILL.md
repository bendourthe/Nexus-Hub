---
template_id: SKILL
template_name: Refactor-For-Testability - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: refactor-for-testability
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:

  - skills
  - testing
  - generic
---
# refactor-for-testability

---
category: migration-refactoring
priority: MEDIUM
languages: [python, javascript, typescript, java, csharp, go]
requires_user_input: true
estimated_duration: 2-8 hours
---

## Overview

Refactor existing code to improve testability by introducing dependency injection, interfaces, and design patterns that facilitate unit testing and test isolation.

## When to Use This Skill

- Code is difficult to unit test
- High coupling between components
- Heavy use of global state or singletons
- Hard-coded dependencies on external systems
- Inability to test components in isolation
- Low test coverage due to structural issues
- Preparing legacy code for test-driven development

## Prerequisites

- Existing test suite or testing framework setup
- Understanding of dependency injection principles
- Familiarity with mocking/stubbing concepts
- Version control with clean working directory
- Refactoring tools for your language

## Step-by-Step Instructions

### Phase 1: Assessment

#### Step 1: Identify Testability Issues

**Common testability problems:**

```python
# Problem 1: Hard-coded dependencies
class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Hard-coded dependency
        self.cache = RedisCache()  # Hard-coded dependency
        self.logger = Logger()     # Hard-coded dependency

    def get_user(self, user_id):
        # Hard to test - requires real database
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")

# Problem 2: Global state
current_user = None  # Global variable

def process_order(order):
    # Depends on global state
    if current_user is None:
        raise ValueError("No user logged in")
    return f"Order {order} for {current_user}"

# Problem 3: Hidden dependencies
class EmailService:
    def send_email(self, to, subject, body):
        # Hidden dependency on SMTP server
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.send_message(to, subject, body)
        # Hard to test without real SMTP

# Problem 4: Static methods and class methods
class DatabaseHelper:
    @staticmethod
    def get_connection():
        # Static method - hard to mock
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="password"
        )

# Problem 5: Tight coupling
class OrderProcessor:
    def process(self, order):
        # Tightly coupled to specific implementations
        payment = PayPalPayment()
        notification = SMSNotification()

        payment.charge(order.amount)
        notification.send(order.customer, "Order processed")
```

**Create testability assessment:**

```python
"""
Testability Assessment Report

Project: [name]
Date: [date]

Issues Found:

1. Hard-coded Dependencies
   - UserService → MySQLDatabase
   - EmailService → SMTP
   - PaymentService → PayPal API
   Impact: Cannot test without real services
   Priority: HIGH

2. Global State
   - current_user global variable
   - configuration singletons
   Impact: Tests interfere with each other
   Priority: HIGH

3. Static Methods
   - DatabaseHelper.get_connection()
   - ConfigManager.get_config()
   Impact: Difficult to mock
   Priority: MEDIUM

4. Tight Coupling
   - OrderProcessor → PayPalPayment
   - NotificationService → SMSProvider
   Impact: Cannot test implementations independently
   Priority: HIGH

Recommended Actions:
1. Introduce dependency injection
2. Create interfaces/protocols
3. Extract methods for testability
4. Remove global state
5. Add seams for testing
"""
```

### Phase 2: Introduce Dependency Injection

#### Step 2: Extract Dependencies to Constructor

**Python example:**

```python
# BEFORE: Hard-coded dependencies
class UserService:
    def __init__(self):
        self.db = MySQLDatabase()
        self.cache = RedisCache()

    def get_user(self, user_id):
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        user = self.db.query(f"SELECT * FROM users WHERE id={user_id}")
        self.cache.set(f"user:{user_id}", user)
        return user

# AFTER: Dependency injection
class UserService:
    def __init__(self, database, cache):
        self.db = database
        self.cache = cache

    def get_user(self, user_id):
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        user = self.db.query(f"SELECT * FROM users WHERE id={user_id}")
        self.cache.set(f"user:{user_id}", user)
        return user

# Now easily testable with mocks
def test_get_user_with_cache():
    mock_db = Mock()
    mock_cache = Mock()
    mock_cache.get.return_value = {"id": 1, "name": "Alice"}

    service = UserService(mock_db, mock_cache)
    user = service.get_user(1)

    assert user["name"] == "Alice"
    mock_db.query.assert_not_called()  # Database wasn't called
```

**JavaScript/TypeScript example:**

```javascript
// BEFORE: Hard-coded dependencies
class OrderService {
    constructor() {
        this.paymentProcessor = new PayPalPayment();
        this.emailSender = new SMTPEmailSender();
    }

    processOrder(order) {
        this.paymentProcessor.charge(order.amount);
        this.emailSender.send(order.customer.email, "Order confirmed");
    }
}

// AFTER: Dependency injection
class OrderService {
    constructor(paymentProcessor, emailSender) {
        this.paymentProcessor = paymentProcessor;
        this.emailSender = emailSender;
    }

    processOrder(order) {
        this.paymentProcessor.charge(order.amount);
        this.emailSender.send(order.customer.email, "Order confirmed");
    }
}

// Test with mocks
describe('OrderService', () => {
    it('processes order successfully', () => {
        const mockPayment = { charge: jest.fn() };
        const mockEmail = { send: jest.fn() };

        const service = new OrderService(mockPayment, mockEmail);
        service.processOrder({ amount: 100, customer: { email: 'test@example.com' } });

        expect(mockPayment.charge).toHaveBeenCalledWith(100);
        expect(mockEmail.send).toHaveBeenCalledWith('test@example.com', 'Order confirmed');
    });
});
```

**Java example:**

```java
// BEFORE: Hard-coded dependencies
public class UserService {
    private DatabaseConnection db;
    private CacheService cache;

    public UserService() {
        this.db = new MySQLConnection();
        this.cache = new RedisCache();
    }

    public User getUser(int userId) {
        User cached = cache.get("user:" + userId);
        if (cached != null) return cached;

        User user = db.query("SELECT * FROM users WHERE id=" + userId);
        cache.set("user:" + userId, user);
        return user;
    }
}

// AFTER: Dependency injection with interfaces
public interface Database {
    User query(String sql);
}

public interface Cache {
    User get(String key);
    void set(String key, User value);
}

public class UserService {
    private final Database db;
    private final Cache cache;

    public UserService(Database db, Cache cache) {
        this.db = db;
        this.cache = cache;
    }

    public User getUser(int userId) {
        User cached = cache.get("user:" + userId);
        if (cached != null) return cached;

        User user = db.query("SELECT * FROM users WHERE id=" + userId);
        cache.set("user:" + userId, user);
        return user;
    }
}

// Test with mocks
@Test
public void testGetUserWithCache() {
    Database mockDb = mock(Database.class);
    Cache mockCache = mock(Cache.class);
    User expectedUser = new User(1, "Alice");

    when(mockCache.get("user:1")).thenReturn(expectedUser);

    UserService service = new UserService(mockDb, mockCache);
    User user = service.getUser(1);

    assertEquals("Alice", user.getName());
    verify(mockDb, never()).query(anyString());
}
```

#### Step 3: Create Interfaces/Protocols

**Python with Protocol (Python 3.8+):**

```python
from typing import Protocol, Optional
from datetime import datetime

# Define protocols (interfaces)
class Database(Protocol):
    """Protocol for database operations."""
    def query(self, sql: str) -> list:
        ...

    def execute(self, sql: str) -> int:
        ...

class Cache(Protocol):
    """Protocol for cache operations."""
    def get(self, key: str) -> Optional[dict]:
        ...

    def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        ...

class Logger(Protocol):
    """Protocol for logging operations."""
    def info(self, message: str) -> None:
        ...

    def error(self, message: str, exc: Exception = None) -> None:
        ...

# Refactored service using protocols
class UserService:
    def __init__(self, db: Database, cache: Cache, logger: Logger):
        self.db = db
        self.cache = cache
        self.logger = logger

    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID with caching."""
        cache_key = f"user:{user_id}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Cache hit for user {user_id}")
            return cached

        # Query database
        self.logger.info(f"Cache miss for user {user_id}, querying database")
        users = self.db.query(f"SELECT * FROM users WHERE id={user_id}")

        if not users:
            return None

        user = users[0]
        self.cache.set(cache_key, user)
        return user

# Test implementations
class MockDatabase:
    def __init__(self, data):
        self.data = data
        self.queries = []

    def query(self, sql: str) -> list:
        self.queries.append(sql)
        return self.data

    def execute(self, sql: str) -> int:
        return 1

class MockCache:
    def __init__(self):
        self.storage = {}

    def get(self, key: str) -> Optional[dict]:
        return self.storage.get(key)

    def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        self.storage[key] = value

class MockLogger:
    def __init__(self):
        self.logs = []

    def info(self, message: str) -> None:
        self.logs.append(('INFO', message))

    def error(self, message: str, exc: Exception = None) -> None:
        self.logs.append(('ERROR', message, exc))

# Test
def test_user_service():
    mock_db = MockDatabase([{"id": 1, "name": "Alice"}])
    mock_cache = MockCache()
    mock_logger = MockLogger()

    service = UserService(mock_db, mock_cache, mock_logger)

    # First call - should hit database
    user1 = service.get_user(1)
    assert user1["name"] == "Alice"
    assert len(mock_db.queries) == 1

    # Second call - should hit cache
    user2 = service.get_user(1)
    assert user2["name"] == "Alice"
    assert len(mock_db.queries) == 1  # No additional query

    # Check logs
    assert len(mock_logger.logs) == 2
    assert "Cache miss" in mock_logger.logs[0][1]
    assert "Cache hit" in mock_logger.logs[1][1]
```

**TypeScript with interfaces:**

```typescript
// Define interfaces
interface PaymentProcessor {
    charge(amount: number, currency: string): Promise<PaymentResult>;
    refund(transactionId: string, amount: number): Promise<RefundResult>;
}

interface NotificationService {
    sendEmail(to: string, subject: string, body: string): Promise<void>;
    sendSMS(phoneNumber: string, message: string): Promise<void>;
}

interface OrderRepository {
    save(order: Order): Promise<Order>;
    findById(id: string): Promise<Order | null>;
    update(order: Order): Promise<Order>;
}

// Refactored service
class OrderService {
    constructor(
        private paymentProcessor: PaymentProcessor,
        private notificationService: NotificationService,
        private orderRepository: OrderRepository
    ) {}

    async processOrder(order: Order): Promise<Order> {
        // Save order
        const savedOrder = await this.orderRepository.save(order);

        // Process payment
        const payment = await this.paymentProcessor.charge(
            order.amount,
            order.currency
        );

        // Send confirmation
        await this.notificationService.sendEmail(
            order.customer.email,
            'Order Confirmation',
            `Your order ${savedOrder.id} has been confirmed`
        );

        return savedOrder;
    }
}

// Mock implementations for testing
class MockPaymentProcessor implements PaymentProcessor {
    async charge(amount: number, currency: string): Promise<PaymentResult> {
        return { success: true, transactionId: 'mock-123' };
    }

    async refund(transactionId: string, amount: number): Promise<RefundResult> {
        return { success: true, refundId: 'refund-123' };
    }
}

class MockNotificationService implements NotificationService {
    emails: Array<{ to: string; subject: string; body: string }> = [];

    async sendEmail(to: string, subject: string, body: string): Promise<void> {
        this.emails.push({ to, subject, body });
    }

    async sendSMS(phoneNumber: string, message: string): Promise<void> {
        // Mock implementation
    }
}

// Test
describe('OrderService', () => {
    it('processes order successfully', async () => {
        const mockPayment = new MockPaymentProcessor();
        const mockNotification = new MockNotificationService();
        const mockRepository = new MockOrderRepository();

        const service = new OrderService(mockPayment, mockNotification, mockRepository);

        const order = { amount: 100, currency: 'USD', customer: { email: 'test@example.com' } };
        const result = await service.processOrder(order);

        expect(result.id).toBeDefined();
        expect(mockNotification.emails).toHaveLength(1);
        expect(mockNotification.emails[0].to).toBe('test@example.com');
    });
});
```

### Phase 3: Remove Global State

#### Step 4: Replace Global Variables with Dependency Injection

```python
# BEFORE: Global state
current_user = None
config = {
    'database': 'mysql://localhost/mydb',
    'cache_ttl': 3600
}

def get_user_orders(user_id):
    # Depends on global current_user and config
    if current_user is None:
        raise ValueError("No user logged in")

    if current_user['id'] != user_id and not current_user['is_admin']:
        raise PermissionError("Cannot access other user's orders")

    db = connect(config['database'])
    return db.query(f"SELECT * FROM orders WHERE user_id={user_id}")

# AFTER: Remove global state
class UserContext:
    """Holds user context for request."""
    def __init__(self, user_id: int, is_admin: bool = False):
        self.user_id = user_id
        self.is_admin = is_admin

class OrderService:
    def __init__(self, database: Database):
        self.database = database

    def get_user_orders(self, context: UserContext, user_id: int) -> list:
        """Get orders for user."""
        # Check permissions using injected context
        if context.user_id != user_id and not context.is_admin:
            raise PermissionError("Cannot access other user's orders")

        return self.database.query(f"SELECT * FROM orders WHERE user_id={user_id}")

# Now testable
def test_get_user_orders_permission_denied():
    mock_db = Mock()
    service = OrderService(mock_db)
    user_context = UserContext(user_id=1, is_admin=False)

    with pytest.raises(PermissionError):
        service.get_user_orders(user_context, user_id=2)

    mock_db.query.assert_not_called()

def test_get_user_orders_admin_access():
    mock_db = Mock()
    mock_db.query.return_value = [{"id": 1, "amount": 100}]

    service = OrderService(mock_db)
    admin_context = UserContext(user_id=1, is_admin=True)

    orders = service.get_user_orders(admin_context, user_id=2)
    assert len(orders) == 1
    mock_db.query.assert_called_once()
```

#### Step 5: Replace Singletons with Dependency Injection

```python
# BEFORE: Singleton pattern
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connect()
        return cls._instance

    def connect(self):
        # Connect to database
        pass

    def query(self, sql):
        # Execute query
        pass

# Usage makes testing difficult
def get_users():
    db = DatabaseConnection()  # Always gets same instance
    return db.query("SELECT * FROM users")

# AFTER: Remove singleton, use dependency injection
class DatabaseConnection:
    def __init__(self, host: str, port: int, database: str):
        self.host = host
        self.port = port
        self.database = database
        self.connect()

    def connect(self):
        # Connect to database
        pass

    def query(self, sql: str):
        # Execute query
        pass

class UserRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def get_users(self) -> list:
        return self.db.query("SELECT * FROM users")

# Now easily testable
def test_get_users():
    mock_db = Mock()
    mock_db.query.return_value = [{"id": 1, "name": "Alice"}]

    repo = UserRepository(mock_db)
    users = repo.get_users()

    assert len(users) == 1
    assert users[0]["name"] == "Alice"
```

### Phase 4: Extract Methods and Create Seams

#### Step 6: Extract External Dependencies

```python
# BEFORE: Hard to test due to external dependencies
import requests
from datetime import datetime

class WeatherService:
    def get_temperature(self, city: str) -> float:
        # Hard-coded HTTP request - difficult to test
        response = requests.get(
            f"https://api.weather.com/current?city={city}"
        )
        data = response.json()
        return data['temperature']

    def should_send_alert(self, city: str) -> bool:
        # Multiple responsibilities, hard to test
        temp = self.get_temperature(city)
        current_hour = datetime.now().hour

        # Alert if temperature is extreme and during business hours
        return (temp < 0 or temp > 35) and 9 <= current_hour <= 17

# AFTER: Extract dependencies, create seams
class WeatherAPI:
    """Wrapper for external weather API."""
    def get_current_weather(self, city: str) -> dict:
        response = requests.get(
            f"https://api.weather.com/current?city={city}"
        )
        return response.json()

class TimeProvider:
    """Wrapper for time operations."""
    def get_current_hour(self) -> int:
        return datetime.now().hour

class WeatherService:
    def __init__(self, api: WeatherAPI, time_provider: TimeProvider):
        self.api = api
        self.time_provider = time_provider

    def get_temperature(self, city: str) -> float:
        """Get current temperature for city."""
        data = self.api.get_current_weather(city)
        return data['temperature']

    def should_send_alert(self, city: str) -> bool:
        """Determine if weather alert should be sent."""
        temp = self.get_temperature(city)
        current_hour = self.time_provider.get_current_hour()

        return self._is_extreme_temperature(temp) and self._is_business_hours(current_hour)

    def _is_extreme_temperature(self, temp: float) -> bool:
        """Check if temperature is extreme."""
        return temp < 0 or temp > 35

    def _is_business_hours(self, hour: int) -> bool:
        """Check if current time is business hours."""
        return 9 <= hour <= 17

# Now fully testable
class MockWeatherAPI:
    def __init__(self, temperature: float):
        self.temperature = temperature

    def get_current_weather(self, city: str) -> dict:
        return {'temperature': self.temperature}

class MockTimeProvider:
    def __init__(self, hour: int):
        self.hour = hour

    def get_current_hour(self) -> int:
        return self.hour

def test_should_send_alert_extreme_temp_business_hours():
    mock_api = MockWeatherAPI(temperature=-5)
    mock_time = MockTimeProvider(hour=10)

    service = WeatherService(mock_api, mock_time)
    assert service.should_send_alert("Boston") is True

def test_should_not_send_alert_normal_temp():
    mock_api = MockWeatherAPI(temperature=20)
    mock_time = MockTimeProvider(hour=10)

    service = WeatherService(mock_api, mock_time)
    assert service.should_send_alert("Boston") is False

def test_should_not_send_alert_outside_business_hours():
    mock_api = MockWeatherAPI(temperature=-5)
    mock_time = MockTimeProvider(hour=20)

    service = WeatherService(mock_api, mock_time)
    assert service.should_send_alert("Boston") is False
```

#### Step 7: Break Up Large Methods

```python
# BEFORE: Large method with multiple responsibilities
def process_order(order_data):
    # Validate order
    if not order_data.get('customer_id'):
        raise ValueError("Missing customer_id")
    if not order_data.get('items'):
        raise ValueError("Missing items")
    for item in order_data['items']:
        if item['quantity'] <= 0:
            raise ValueError("Invalid quantity")

    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in order_data['items'])
    tax = subtotal * 0.08
    shipping = 10 if subtotal < 100 else 0
    total = subtotal + tax + shipping

    # Process payment
    payment_data = {
        'amount': total,
        'customer_id': order_data['customer_id']
    }
    response = requests.post('https://payment.api/charge', json=payment_data)
    if response.status_code != 200:
        raise Exception("Payment failed")

    # Save to database
    db = MySQLDatabase()
    order_id = db.insert('orders', {
        'customer_id': order_data['customer_id'],
        'total': total,
        'status': 'paid'
    })

    # Send confirmation email
    smtp = smtplib.SMTP('smtp.gmail.com')
    smtp.send_email(
        order_data['customer_email'],
        f"Order {order_id} confirmed",
        f"Total: ${total}"
    )

    return order_id

# AFTER: Broken into testable methods with DI
class OrderValidator:
    def validate(self, order_data: dict) -> None:
        """Validate order data."""
        if not order_data.get('customer_id'):
            raise ValueError("Missing customer_id")
        if not order_data.get('items'):
            raise ValueError("Missing items")
        for item in order_data['items']:
            if item['quantity'] <= 0:
                raise ValueError(f"Invalid quantity for item {item['id']}")

class OrderCalculator:
    def __init__(self, tax_rate: float = 0.08, free_shipping_threshold: float = 100):
        self.tax_rate = tax_rate
        self.free_shipping_threshold = free_shipping_threshold

    def calculate_totals(self, items: list) -> dict:
        """Calculate order totals."""
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        tax = subtotal * self.tax_rate
        shipping = 0 if subtotal >= self.free_shipping_threshold else 10
        total = subtotal + tax + shipping

        return {
            'subtotal': subtotal,
            'tax': tax,
            'shipping': shipping,
            'total': total
        }

class OrderProcessor:
    def __init__(
        self,
        validator: OrderValidator,
        calculator: OrderCalculator,
        payment_service: PaymentService,
        order_repository: OrderRepository,
        notification_service: NotificationService
    ):
        self.validator = validator
        self.calculator = calculator
        self.payment_service = payment_service
        self.order_repository = order_repository
        self.notification_service = notification_service

    def process_order(self, order_data: dict) -> int:
        """Process order through all steps."""
        # Step 1: Validate
        self.validator.validate(order_data)

        # Step 2: Calculate
        totals = self.calculator.calculate_totals(order_data['items'])

        # Step 3: Process payment
        payment_result = self.payment_service.charge(
            order_data['customer_id'],
            totals['total']
        )

        # Step 4: Save order
        order_id = self.order_repository.save({
            'customer_id': order_data['customer_id'],
            'total': totals['total'],
            'status': 'paid',
            'payment_id': payment_result['transaction_id']
        })

        # Step 5: Send confirmation
        self.notification_service.send_order_confirmation(
            order_data['customer_email'],
            order_id,
            totals['total']
        )

        return order_id

# Now each component is independently testable
def test_order_validator():
    validator = OrderValidator()

    # Test valid order
    valid_order = {
        'customer_id': 123,
        'items': [{'id': 1, 'quantity': 2, 'price': 10}]
    }
    validator.validate(valid_order)  # Should not raise

    # Test invalid order
    invalid_order = {'customer_id': 123, 'items': []}
    with pytest.raises(ValueError, match="Missing items"):
        validator.validate(invalid_order)

def test_order_calculator():
    calculator = OrderCalculator(tax_rate=0.08, free_shipping_threshold=100)

    items = [
        {'price': 50, 'quantity': 1},
        {'price': 30, 'quantity': 2}
    ]

    totals = calculator.calculate_totals(items)

    assert totals['subtotal'] == 110
    assert totals['tax'] == 8.8
    assert totals['shipping'] == 0  # Above free shipping threshold
    assert totals['total'] == 118.8

def test_order_processor():
    mock_validator = Mock()
    mock_calculator = Mock()
    mock_calculator.calculate_totals.return_value = {
        'subtotal': 100,
        'tax': 8,
        'shipping': 0,
        'total': 108
    }
    mock_payment = Mock()
    mock_payment.charge.return_value = {'transaction_id': 'tx-123'}
    mock_repository = Mock()
    mock_repository.save.return_value = 456
    mock_notification = Mock()

    processor = OrderProcessor(
        mock_validator,
        mock_calculator,
        mock_payment,
        mock_repository,
        mock_notification
    )

    order_data = {
        'customer_id': 123,
        'customer_email': 'test@example.com',
        'items': [{'price': 100, 'quantity': 1}]
    }

    order_id = processor.process_order(order_data)

    assert order_id == 456
    mock_validator.validate.assert_called_once()
    mock_payment.charge.assert_called_once_with(123, 108)
    mock_notification.send_order_confirmation.assert_called_once()
```

### Phase 5: Add Factory Methods and Builders

#### Step 8: Create Test Fixtures and Factories

```python
# Test data factories
class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create(
        user_id: int = 1,
        name: str = "Test User",
        email: str = "test@example.com",
        is_admin: bool = False,
        **kwargs
    ):
        """Create a test user with defaults."""
        user = {
            'id': user_id,
            'name': name,
            'email': email,
            'is_admin': is_admin
        }
        user.update(kwargs)
        return user

class OrderFactory:
    """Factory for creating test orders."""

    @staticmethod
    def create(
        order_id: int = 1,
        customer_id: int = 1,
        items: list = None,
        status: str = "pending",
        **kwargs
    ):
        """Create a test order with defaults."""
        if items is None:
            items = [
                {'id': 1, 'name': 'Product 1', 'price': 10, 'quantity': 1}
            ]

        order = {
            'id': order_id,
            'customer_id': customer_id,
            'items': items,
            'status': status
        }
        order.update(kwargs)
        return order

# Use in tests
def test_order_processing():
    # Easy to create test data
    user = UserFactory.create(user_id=1, name="Alice")
    order = OrderFactory.create(
        customer_id=user['id'],
        items=[
            {'id': 1, 'price': 50, 'quantity': 2},
            {'id': 2, 'price': 30, 'quantity': 1}
        ]
    )

    # Test logic
    processor = OrderProcessor(...)
    result = processor.process_order(order)
    assert result is not None

# Builder pattern for complex objects
class OrderBuilder:
    """Builder for creating test orders."""

    def __init__(self):
        self.order = {
            'id': 1,
            'customer_id': 1,
            'items': [],
            'status': 'pending'
        }

    def with_id(self, order_id: int):
        self.order['id'] = order_id
        return self

    def with_customer(self, customer_id: int):
        self.order['customer_id'] = customer_id
        return self

    def with_item(self, item_id: int, price: float, quantity: int):
        self.order['items'].append({
            'id': item_id,
            'price': price,
            'quantity': quantity
        })
        return self

    def with_status(self, status: str):
        self.order['status'] = status
        return self

    def build(self):
        return self.order.copy()

# Use builder in tests
def test_large_order():
    order = (OrderBuilder()
        .with_customer(123)
        .with_item(1, 50, 10)
        .with_item(2, 30, 5)
        .with_item(3, 100, 2)
        .with_status('pending')
        .build())

    assert len(order['items']) == 3
    assert order['customer_id'] == 123
```

### Phase 6: Validation and Testing

#### Step 9: Write Comprehensive Tests

```python
# Test coverage for refactored code
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    """Test suite for UserService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_cache = Mock()
        self.mock_logger = Mock()
        self.service = UserService(self.mock_db, self.mock_cache, self.mock_logger)

    def test_get_user_cache_hit(self):
        """Test cache hit scenario."""
        expected_user = {'id': 1, 'name': 'Alice'}
        self.mock_cache.get.return_value = expected_user

        result = self.service.get_user(1)

        assert result == expected_user
        self.mock_cache.get.assert_called_once_with('user:1')
        self.mock_db.query.assert_not_called()

    def test_get_user_cache_miss(self):
        """Test cache miss scenario."""
        self.mock_cache.get.return_value = None
        expected_user = {'id': 1, 'name': 'Alice'}
        self.mock_db.query.return_value = [expected_user]

        result = self.service.get_user(1)

        assert result == expected_user
        self.mock_cache.get.assert_called_once()
        self.mock_db.query.assert_called_once()
        self.mock_cache.set.assert_called_once_with('user:1', expected_user)

    def test_get_user_not_found(self):
        """Test user not found scenario."""
        self.mock_cache.get.return_value = None
        self.mock_db.query.return_value = []

        result = self.service.get_user(999)

        assert result is None
        self.mock_cache.set.assert_not_called()

    def test_get_user_database_error(self):
        """Test database error handling."""
        self.mock_cache.get.return_value = None
        self.mock_db.query.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            self.service.get_user(1)

        self.mock_logger.error.assert_called_once()

# Integration tests
def test_user_service_integration():
    """Integration test with real implementations."""
    db = InMemoryDatabase()
    cache = InMemoryCache()
    logger = SimpleLogger()

    service = UserService(db, cache, logger)

    # Add test user to database
    db.execute("INSERT INTO users VALUES (1, 'Alice')")

    # First call - cache miss
    user1 = service.get_user(1)
    assert user1['name'] == 'Alice'

    # Second call - cache hit
    user2 = service.get_user(1)
    assert user2['name'] == 'Alice'

    # Verify caching worked
    assert cache.get('user:1') is not None
```

## Expected Outcomes

After completing this refactoring:

1. **Improved testability**
   - Easy to write unit tests
   - Components can be tested in isolation
   - Fast test execution

2. **Better code structure**
   - Clear dependencies
   - Single responsibility principle
   - Loose coupling

3. **Higher test coverage**
   - Ability to test edge cases
   - Mock external dependencies
   - Test error conditions

4. **Maintainable codebase**
   - Easier to understand
   - Easier to modify
   - Easier to extend

## Success Criteria

- [ ] All hard-coded dependencies removed
- [ ] Constructor injection implemented
- [ ] Interfaces/protocols defined
- [ ] Global state eliminated
- [ ] Singletons replaced with DI
- [ ] Large methods broken down
- [ ] External dependencies extracted
- [ ] Test fixtures created
- [ ] Unit test coverage >80%
- [ ] Integration tests passing
- [ ] All tests run in <1 minute
- [ ] Mock objects used effectively

## Common Pitfalls

1. **Over-engineering**
   - Don't create interfaces for everything
   - Balance between testability and complexity

2. **Incomplete refactoring**
   - Ensure all dependencies are injected
   - Don't leave global state behind

3. **Poor abstraction boundaries**
   - Create meaningful interfaces
   - Don't leak implementation details

4. **Neglecting integration tests**
   - Unit tests aren't enough
   - Test real integrations too

## Related Skills

- **add-unit-tests**: Add comprehensive unit tests
- **code-complexity-analysis**: Analyze code complexity
- **dependency-upgrade**: Upgrade dependencies safely
- **migrate-python-2-to-3**: Python 2 to 3 migration
- **extract-microservice**: Extract microservices

## Additional Resources

### Books
- "Working Effectively with Legacy Code" by Michael Feathers
- "Refactoring" by Martin Fowler
- "Clean Code" by Robert Martin
- "Test Driven Development" by Kent Beck

### Patterns
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Test Double Patterns](http://xunitpatterns.com/Test%20Double.html)

### Tools
- **Python**: pytest, unittest.mock, factory_boy
- **JavaScript**: Jest, Sinon, test-data-bot
- **Java**: JUnit, Mockito, TestNG
- **C#**: NUnit, Moq, AutoFixture

---

**Note**: Refactoring for testability is an iterative process. Start with the most problematic areas and gradually improve the entire codebase.
