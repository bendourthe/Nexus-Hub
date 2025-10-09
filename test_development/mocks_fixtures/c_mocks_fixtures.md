# C Mocks & Fixtures

## Objective
Design and implement effective mocking strategies and fixture management using CMock and fff (fake function framework) to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests in C.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── mocks_fixtures/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/mocks_fixtures/` subdirectory for this testing phase
- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:
- `test_files/` - Actual test implementation files
- `test_data/` - Test fixtures, mock data, sample inputs
- `test_reports/` - Test execution reports, coverage reports, performance results
- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Fixture Setup
- [ ] Setup/teardown functions configured appropriately
- [ ] Test data builders created for flexible data generation
- [ ] Fixture factories implemented with realistic data
- [ ] Cleanup and memory management automated
- [ ] Fixtures documented with clear purposes

### Mocking Strategy
- [ ] External dependencies identified for mocking
- [ ] Function pointers or link-time substitution planned
- [ ] Mock implementations created with CMock or fff
- [ ] Verification methods used appropriately
- [ ] Over-mocking avoided

### Test Data Management
- [ ] Test data factories implemented
- [ ] Realistic test data patterns established
- [ ] Data builders for complex structures created
- [ ] Test data isolated per test
- [ ] Memory cleanup automated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Mocks & Fixtures Implementation

Please implement comprehensive mocking and fixture strategies for this C project following this protocol:

## Phase 1: Fixture Architecture Design

### Understanding C Testing Patterns with Unity

Unity is a popular C testing framework:

**Basic Setup/Teardown**:
```c
// test_user_service.c
#include "unity.h"
#include "user_service.h"
#include "database.h"

static Database *test_db;
static UserService *user_service;

void setUp(void) {
    // Runs before each test
    test_db = database_create("test.db");
    user_service = user_service_create(test_db);
}

void tearDown(void) {
    // Runs after each test - cleanup
    user_service_destroy(user_service);
    database_clear(test_db);
    database_destroy(test_db);
}

void test_user_creation(void) {
    User user = {
        .id = 0,
        .username = "testuser",
        .email = "test@example.com"
    };

    User *result = user_service_create_user(user_service, &user);

    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("testuser", result->username);

    user_destroy(result);
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_user_creation);
    return UNITY_END();
}
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Suite-Level Setup**:
```c
// test_database.c
#include "unity.h"
#include "database.h"

static Connection *shared_connection;

// Run once before all tests
void suiteSetUp(void) {
    shared_connection = connection_open("test.db");
    connection_init_schema(shared_connection);
}

// Run once after all tests
void suiteTearDown(void) {
    connection_drop_tables(shared_connection);
    connection_close(shared_connection);
}

void setUp(void) {
    // Clear data before each test
    connection_clear_data(shared_connection);
}

void tearDown(void) {
    // Nothing needed per test
}

void test_insert_user(void) {
    User user = {.id = 1, .username = "alice"};
    int result = connection_insert_user(shared_connection, &user);

    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_INT(1, connection_count_users(shared_connection));
}

void test_query_users(void) {
    User user = {.id = 1, .username = "alice"};
    connection_insert_user(shared_connection, &user);

    User *retrieved = connection_get_user(shared_connection, 1);

    TEST_ASSERT_NOT_NULL(retrieved);
    TEST_ASSERT_EQUAL_STRING("alice", retrieved->username);

    free(retrieved);
}

int main(void) {
    suiteSetUp();
    UNITY_BEGIN();
    RUN_TEST(test_insert_user);
    RUN_TEST(test_query_users);
    int result = UNITY_END();
    suiteTearDown();
    return result;
}
```

**2. Test-Level Fixtures with Memory Management**:
```c
void setUp(void) {
    // Allocate fresh resources
    test_db = malloc(sizeof(Database));
    test_db->connection = NULL;
    test_db->is_connected = false;

    database_init(test_db, "test.db");
}

void tearDown(void) {
    // Clean up and free memory
    database_cleanup(test_db);
    free(test_db);
    test_db = NULL;
}

void test_database_connection(void) {
    int result = database_connect(test_db);

    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_TRUE(test_db->is_connected);
}
```

### Fixture Factories

Create factories for flexible test data generation:

```c
// test_utils/user_factory.h
#ifndef USER_FACTORY_H
#define USER_FACTORY_H

#include "user.h"

typedef struct {
    int id_counter;
    User **created_users;
    size_t user_count;
    size_t capacity;
} UserFactory;

UserFactory *user_factory_create(void);
void user_factory_destroy(UserFactory *factory);

User *user_factory_build(UserFactory *factory);
User *user_factory_build_with_username(UserFactory *factory, const char *username);
User *user_factory_build_with_age(UserFactory *factory, int age);
User *user_factory_build_custom(UserFactory *factory,
                                  const char *username,
                                  const char *email,
                                  int age);

User **user_factory_build_batch(UserFactory *factory, size_t count);
void user_factory_reset(UserFactory *factory);

#endif // USER_FACTORY_H
```

```c
// test_utils/user_factory.c
#include "user_factory.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define INITIAL_CAPACITY 10

UserFactory *user_factory_create(void) {
    UserFactory *factory = malloc(sizeof(UserFactory));
    factory->id_counter = 0;
    factory->user_count = 0;
    factory->capacity = INITIAL_CAPACITY;
    factory->created_users = malloc(sizeof(User*) * INITIAL_CAPACITY);
    return factory;
}

void user_factory_destroy(UserFactory *factory) {
    if (factory == NULL) return;

    // Free all created users
    for (size_t i = 0; i < factory->user_count; i++) {
        user_destroy(factory->created_users[i]);
    }

    free(factory->created_users);
    free(factory);
}

static void add_to_tracking(UserFactory *factory, User *user) {
    if (factory->user_count >= factory->capacity) {
        factory->capacity *= 2;
        factory->created_users = realloc(factory->created_users,
                                        sizeof(User*) * factory->capacity);
    }
    factory->created_users[factory->user_count++] = user;
}

User *user_factory_build(UserFactory *factory) {
    factory->id_counter++;

    User *user = malloc(sizeof(User));
    user->id = factory->id_counter;

    // Generate default username
    char username[50];
    snprintf(username, sizeof(username), "user_%d", factory->id_counter);
    user->username = strdup(username);

    // Generate default email
    char email[100];
    snprintf(email, sizeof(email), "user%d@test.com", factory->id_counter);
    user->email = strdup(email);

    user->age = 25;
    user->is_active = true;
    user->created_at = time(NULL);

    add_to_tracking(factory, user);
    return user;
}

User *user_factory_build_custom(UserFactory *factory,
                                  const char *username,
                                  const char *email,
                                  int age) {
    factory->id_counter++;

    User *user = malloc(sizeof(User));
    user->id = factory->id_counter;
    user->username = strdup(username ? username : "default");
    user->email = strdup(email ? email : "default@test.com");
    user->age = age > 0 ? age : 25;
    user->is_active = true;
    user->created_at = time(NULL);

    add_to_tracking(factory, user);
    return user;
}

User **user_factory_build_batch(UserFactory *factory, size_t count) {
    User **users = malloc(sizeof(User*) * count);
    for (size_t i = 0; i < count; i++) {
        users[i] = user_factory_build(factory);
    }
    return users;
}

void user_factory_reset(UserFactory *factory) {
    for (size_t i = 0; i < factory->user_count; i++) {
        user_destroy(factory->created_users[i]);
    }
    factory->user_count = 0;
    factory->id_counter = 0;
}
```

**Usage in Tests**:
```c
#include "unity.h"
#include "user_factory.h"

static UserFactory *factory;

void setUp(void) {
    factory = user_factory_create();
}

void tearDown(void) {
    user_factory_destroy(factory);
}

void test_create_users_with_defaults(void) {
    User *user1 = user_factory_build(factory);
    User *user2 = user_factory_build(factory);

    TEST_ASSERT_EQUAL_STRING("user_1", user1->username);
    TEST_ASSERT_EQUAL_STRING("user_2", user2->username);
    TEST_ASSERT_EQUAL_INT(1, user1->id);
    TEST_ASSERT_EQUAL_INT(2, user2->id);
}

void test_create_user_with_custom_data(void) {
    User *user = user_factory_build_custom(factory, "alice",
                                           "alice@example.com", 30);

    TEST_ASSERT_EQUAL_STRING("alice", user->username);
    TEST_ASSERT_EQUAL_STRING("alice@example.com", user->email);
    TEST_ASSERT_EQUAL_INT(30, user->age);
}

void test_create_batch_of_users(void) {
    User **users = user_factory_build_batch(factory, 5);

    for (int i = 0; i < 5; i++) {
        TEST_ASSERT_NOT_NULL(users[i]);
        TEST_ASSERT_TRUE(users[i]->is_active);
    }

    free(users); // Don't free individual users - factory manages them
}
```

### Builder Pattern for Complex Structures

```c
// test_utils/order_builder.h
#ifndef ORDER_BUILDER_H
#define ORDER_BUILDER_H

#include "order.h"

typedef struct OrderBuilder OrderBuilder;

OrderBuilder *order_builder_create(void);
void order_builder_destroy(OrderBuilder *builder);

OrderBuilder *order_builder_with_id(OrderBuilder *builder, int id);
OrderBuilder *order_builder_for_user(OrderBuilder *builder, int user_id);
OrderBuilder *order_builder_add_item(OrderBuilder *builder,
                                      int product_id,
                                      int quantity,
                                      double price);
OrderBuilder *order_builder_with_status(OrderBuilder *builder, OrderStatus status);
OrderBuilder *order_builder_with_address(OrderBuilder *builder, Address *address);

Order *order_builder_build(OrderBuilder *builder);

#endif // ORDER_BUILDER_H
```

```c
// test_utils/order_builder.c
#include "order_builder.h"
#include <stdlib.h>
#include <string.h>

struct OrderBuilder {
    Order order;
    OrderItem *items;
    size_t item_count;
    size_t item_capacity;
};

OrderBuilder *order_builder_create(void) {
    OrderBuilder *builder = malloc(sizeof(OrderBuilder));
    memset(&builder->order, 0, sizeof(Order));

    builder->order.status = ORDER_STATUS_PENDING;
    builder->order.total = 0.0;
    builder->item_capacity = 10;
    builder->item_count = 0;
    builder->items = malloc(sizeof(OrderItem) * builder->item_capacity);

    return builder;
}

void order_builder_destroy(OrderBuilder *builder) {
    if (builder == NULL) return;

    if (builder->order.shipping_address) {
        free(builder->order.shipping_address);
    }
    free(builder->items);
    free(builder);
}

OrderBuilder *order_builder_with_id(OrderBuilder *builder, int id) {
    builder->order.id = id;
    return builder;
}

OrderBuilder *order_builder_for_user(OrderBuilder *builder, int user_id) {
    builder->order.user_id = user_id;
    return builder;
}

OrderBuilder *order_builder_add_item(OrderBuilder *builder,
                                      int product_id,
                                      int quantity,
                                      double price) {
    if (builder->item_count >= builder->item_capacity) {
        builder->item_capacity *= 2;
        builder->items = realloc(builder->items,
                                sizeof(OrderItem) * builder->item_capacity);
    }

    OrderItem *item = &builder->items[builder->item_count++];
    item->product_id = product_id;
    item->quantity = quantity;
    item->price = price;

    builder->order.total += quantity * price;

    return builder;
}

OrderBuilder *order_builder_with_status(OrderBuilder *builder, OrderStatus status) {
    builder->order.status = status;
    return builder;
}

OrderBuilder *order_builder_with_address(OrderBuilder *builder, Address *address) {
    builder->order.shipping_address = malloc(sizeof(Address));
    memcpy(builder->order.shipping_address, address, sizeof(Address));
    return builder;
}

Order *order_builder_build(OrderBuilder *builder) {
    Order *order = malloc(sizeof(Order));
    memcpy(order, &builder->order, sizeof(Order));

    // Allocate and copy items
    order->items = malloc(sizeof(OrderItem) * builder->item_count);
    memcpy(order->items, builder->items, sizeof(OrderItem) * builder->item_count);
    order->item_count = builder->item_count;

    return order;
}
```

**Usage**:
```c
void test_order_processing(void) {
    Address address = {
        .street = "123 Main St",
        .city = "Boston",
        .state = "MA"
    };

    OrderBuilder *builder = order_builder_create();
    Order *order = order_builder_with_id(builder, 1)
        ->order_builder_for_user(builder, 100)
        ->order_builder_add_item(builder, 1, 2, 10.00)
        ->order_builder_add_item(builder, 2, 1, 15.00)
        ->order_builder_with_status(builder, ORDER_STATUS_CONFIRMED)
        ->order_builder_with_address(builder, &address)
        ->order_builder_build(builder);

    TEST_ASSERT_EQUAL_DOUBLE(35.00, order->total);
    TEST_ASSERT_EQUAL_INT(2, order->item_count);

    order_destroy(order);
    order_builder_destroy(builder);
}
```

## Phase 2: Mocking with fff (Fake Function Framework)

### Understanding fff

fff is a simple, header-only C mocking framework:

**Setup**:
```c
// Download fff.h from https://github.com/meekrosoft/fff
// Include in your test files

#include "fff.h"
DEFINE_FFF_GLOBALS;

// Define fake functions
FAKE_VALUE_FUNC(int, database_connect, Database*);
FAKE_VALUE_FUNC(User*, database_find_user, Database*, int);
FAKE_VALUE_FUNC(int, database_save_user, Database*, User*);
FAKE_VOID_FUNC(database_disconnect, Database*);
```

**Using Fakes in Tests**:
```c
#include "unity.h"
#include "fff.h"
#include "user_service.h"

DEFINE_FFF_GLOBALS;

// Declare fakes for database functions
FAKE_VALUE_FUNC(int, database_connect, Database*);
FAKE_VALUE_FUNC(User*, database_find_user, Database*, int);
FAKE_VALUE_FUNC(int, database_save_user, Database*, User*);
FAKE_VOID_FUNC(database_disconnect, Database*);

void setUp(void) {
    // Reset all fakes before each test
    RESET_FAKE(database_connect);
    RESET_FAKE(database_find_user);
    RESET_FAKE(database_save_user);
    RESET_FAKE(database_disconnect);
    FFF_RESET_HISTORY();
}

void tearDown(void) {
}

void test_user_service_create(void) {
    Database db;
    UserService *service = user_service_create(&db);

    // Configure fake return value
    database_connect_fake.return_val = 0; // Success

    User user = {.username = "alice"};
    database_save_user_fake.return_val = 0; // Success

    // Execute
    int result = user_service_add_user(service, &user);

    // Verify
    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_INT(1, database_save_user_fake.call_count);
    TEST_ASSERT_EQUAL_PTR(&db, database_save_user_fake.arg0_val);

    user_service_destroy(service);
}

void test_user_service_find_user(void) {
    Database db;
    UserService *service = user_service_create(&db);

    User expected_user = {.id = 1, .username = "alice"};
    database_find_user_fake.return_val = &expected_user;

    // Execute
    User *result = user_service_get_user(service, 1);

    // Verify
    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("alice", result->username);
    TEST_ASSERT_EQUAL_INT(1, database_find_user_fake.call_count);
    TEST_ASSERT_EQUAL_INT(1, database_find_user_fake.arg1_val);

    user_service_destroy(service);
}
```

### When to Mock vs Use Real Objects

**Use Mocks For**:
- External APIs and hardware interfaces
- File system operations
- Network operations
- Database connections
- Time functions (time, clock_gettime)
- System calls

**Use Real Objects For**:
- Pure functions
- Simple data structures
- Mathematical operations
- String manipulation
- Business logic

```c
// GOOD - Mock external dependency
void test_network_request(void) {
    FAKE_VALUE_FUNC(int, http_get, const char*, char*, size_t);
    http_get_fake.return_val = 200;

    char response[1024];
    int result = fetch_user_data(1, response, sizeof(response));

    TEST_ASSERT_EQUAL_INT(200, result);
}

// GOOD - Use real function
void test_calculate_total(void) {
    double items[] = {10.0, 20.0, 30.0};
    double result = calculate_total(items, 3);
    TEST_ASSERT_EQUAL_DOUBLE(60.0, result);
}

// BAD - Over-mocking
void test_add_numbers(void) {
    FAKE_VALUE_FUNC(int, add, int, int);
    add_fake.return_val = 5;
    // Testing mock behavior, not real code
}
```

### fff Features

**Custom Return Values**:
```c
// Different return values per call
database_connect_fake.return_val_seq = (int[]){-1, 0, 0};
database_connect_fake.return_val_seq_len = 3;

// First call returns -1 (error)
// Second and third calls return 0 (success)
```

**Custom Implementations**:
```c
static User* custom_find_user(Database *db, int id) {
    static User user;
    if (id == 1) {
        user.id = 1;
        user.username = "alice";
        return &user;
    }
    return NULL;
}

void test_with_custom_impl(void) {
    database_find_user_fake.custom_fake = custom_find_user;

    User *result = user_service_get_user(service, 1);
    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("alice", result->username);

    result = user_service_get_user(service, 99);
    TEST_ASSERT_NULL(result);
}
```

**Argument Capture**:
```c
void test_argument_capture(void) {
    User user = {.username = "alice"};

    user_service_add_user(service, &user);

    // Check arguments passed to fake
    TEST_ASSERT_EQUAL_INT(1, database_save_user_fake.call_count);
    TEST_ASSERT_EQUAL_STRING("alice",
                             database_save_user_fake.arg1_val->username);
}
```

**Call History**:
```c
void test_call_order(void) {
    user_service_create_and_save(service, "alice");

    // Verify order of calls
    TEST_ASSERT_EQUAL_INT(0, fff.call_history[0]); // database_connect
    TEST_ASSERT_EQUAL_INT(1, fff.call_history[1]); // database_save_user
    TEST_ASSERT_EQUAL_INT(2, fff.call_history[2]); // database_disconnect
}
```

## Phase 3: Mocking with CMock

### Understanding CMock

CMock is part of the Ceedling build system and generates mocks from headers:

**Generate Mock**:
```bash
# Install Ruby and Ceedling
gem install ceedling

# Create project
ceedling new my_project

# CMock generates mocks from header files
# In project.yml:
:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :enforce_strict_ordering: TRUE
```

**Generated Mock Usage**:
```c
// Given header: database.h
// CMock generates: mock_database.h and mock_database.c

#include "unity.h"
#include "mock_database.h"
#include "user_service.h"

void setUp(void) {
}

void tearDown(void) {
}

void test_user_service_save(void) {
    User user = {.id = 1, .username = "alice"};

    // Set expectation
    database_save_user_ExpectAndReturn(&user, 0);

    // Execute
    int result = user_service_save(&user);

    // Verify
    TEST_ASSERT_EQUAL_INT(0, result);
    // CMock automatically verifies expectations
}

void test_user_service_find(void) {
    User expected = {.id = 1, .username = "alice"};

    // Set expectation with return value
    database_find_user_ExpectAndReturn(1, &expected);

    // Execute
    User *result = user_service_find(1);

    // Verify
    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("alice", result->username);
}
```

## Phase 4: Additional Mocking Techniques

### Function Pointer Injection

```c
// user_service.h
typedef struct {
    int (*save_func)(User*);
    User* (*find_func)(int);
} DatabaseFunctions;

typedef struct {
    DatabaseFunctions *db_funcs;
} UserService;

UserService *user_service_create(DatabaseFunctions *funcs);
```

```c
// test_user_service.c
static int mock_save(User *user) {
    // Mock implementation
    return 0;
}

static User* mock_find(int id) {
    static User user = {.id = 1, .username = "alice"};
    return &user;
}

void test_with_function_pointers(void) {
    DatabaseFunctions mock_funcs = {
        .save_func = mock_save,
        .find_func = mock_find
    };

    UserService *service = user_service_create(&mock_funcs);

    User user = {.username = "alice"};
    int result = user_service_save(service, &user);

    TEST_ASSERT_EQUAL_INT(0, result);

    user_service_destroy(service);
}
```

### Link-Time Substitution

```c
// Real implementation in production code
int __attribute__((weak)) database_connect(Database *db) {
    // Real database connection
    return connect_to_database(db);
}

// Test implementation overrides weak symbol
int database_connect(Database *db) {
    // Mock behavior
    return 0; // Success
}
```

### Mocking Time Functions

```c
// time_provider.h
typedef time_t (*TimeFunc)(time_t*);

typedef struct {
    TimeFunc time_func;
} TimeProvider;

void time_provider_init(TimeProvider *provider, TimeFunc func);
time_t time_provider_now(TimeProvider *provider);
```

```c
// test_timestamp.c
static time_t mock_time(time_t *t) {
    // Return fixed time: 2024-01-15 12:00:00
    time_t fixed = 1705320000;
    if (t) *t = fixed;
    return fixed;
}

void test_timestamp_generation(void) {
    TimeProvider provider;
    time_provider_init(&provider, mock_time);

    time_t result = generate_timestamp(&provider);

    TEST_ASSERT_EQUAL_INT64(1705320000, result);
}
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Suite-Level Setup**:
- [fixture_name]: [purpose, setup, teardown]

**Test-Level Setup** (setUp/tearDown):
- [fixture_name]: [purpose, memory management]

**Fixture Factories**:
- [factory_name]: [creates what, memory management]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Tool (fff/CMock) | Reason |
|------------|------------------|------------------|--------|
| [API/Module] | [fake/mock] | [tool] | [justification] |

**Mock Configurations**:
```c
// Example mock setup with fff
FAKE_VALUE_FUNC(int, database_connect, Database*);

void setUp(void) {
    RESET_FAKE(database_connect);
    database_connect_fake.return_val = 0;
}
```

### Test Data Factories
**Factory Functions**:
- UserFactory: [creation functions, memory management]
- OrderFactory: [creation functions, memory management]

**Builder Structs**:
- [builder_name]: [purpose, fluent methods, cleanup]

### Usage Examples
```c
// Example test using fixtures and mocks
void test_user_registration(void) {
    UserFactory *factory = user_factory_create();
    FAKE_VALUE_FUNC(int, email_send, const char*, const char*);
    email_send_fake.return_val = 0;

    User *user = user_factory_build_custom(factory, "alice",
                                           "alice@test.com", 25);

    int result = user_service_register(service, user);

    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_INT(1, email_send_fake.call_count);

    user_factory_destroy(factory);
}
```

### Best Practices Implemented
- [ ] Memory properly allocated and freed
- [ ] setUp/tearDown ensure clean state
- [ ] Factories track allocations for cleanup
- [ ] Mocks reset between tests
- [ ] No memory leaks (verified with valgrind)
- [ ] Function pointers used for testability

### Common Pitfalls Avoided
- Memory leaks from forgotten frees
- Not resetting fakes between tests
- Over-mocking simple functions
- Complex test setup obscuring intent
- Not using weak symbols for mockability

### Next Steps
- [ ] Implement remaining fixtures for integration tests
- [ ] Add factories for all domain structures
- [ ] Document fixture usage for team
- [ ] Set up CMock for automatic mock generation
- [ ] Run valgrind to verify no memory leaks
~~~

## Output Format

The AI assistant should deliver:

1. **Comprehensive fixture setup** with proper memory management
2. **Mock configurations** using fff or CMock
3. **Test data factories** with allocation tracking
4. **Builder patterns** for complex structures
5. **Usage documentation** with examples
6. **Best practices guide** for C testing
7. **Fixture and mock catalog** for easy reference
