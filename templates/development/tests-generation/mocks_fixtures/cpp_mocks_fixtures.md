---
template_id: cpp_mocks_fixtures
template_name: Mocks & Fixtures - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: tests_generation
phase: mocks_fixtures
phase_number: 4
difficulty: intermediate
estimated_time_hours: 3-5
prerequisites:

  - tests_generation/test_cases/cpp_test_cases.md
related_templates:

  - tests_generation/performance_testing/cpp_performance_testing.md
tools:

  - google test

  - catch2

  - boost.test
tags:

  - test-development

  - cpp
---
# C++ Mocks & Fixtures

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                       ► │ ● CURRENT
│ Phase 5: Performance Testing                       ► │ [NEXT]
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 3 (Test Cases Development) should be completed first
**Next Step:** Phase 5 (Performance Testing)

---


## Objective
Design and implement effective mocking strategies and fixture management using Google Mock (GMock) and Trompeloeil to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests in C++.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/mocks_fixtures/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/mocks_fixtures/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Fixture Setup

- [ ] Test fixture classes configured appropriately

- [ ] Test data builders created for flexible data generation

- [ ] Fixture factories implemented with realistic data

- [ ] Cleanup and RAII patterns applied

- [ ] Fixtures documented with clear purposes

### Mocking Strategy

- [ ] External dependencies identified for mocking

- [ ] Interfaces defined for mockable components

- [ ] Mock implementations created with GMock or Trompeloeil

- [ ] Expectation methods used appropriately

- [ ] Over-mocking avoided

### Test Data Management

- [ ] Test data factories implemented

- [ ] Realistic test data patterns established

- [ ] Data builders for complex objects created

- [ ] Test data isolated per test

- [ ] RAII ensures automatic cleanup

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Mocks & Fixtures Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/mocks_fixtures"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:

  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`

  - Template files → `${OUTPUT_DIR}/templates/template.yaml`

  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

Please implement comprehensive mocking and fixture strategies for this C++ project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Fixture Architecture Design

### Understanding Google Test Fixtures

Google Test provides test fixtures for setup/teardown:

**Basic Setup/Teardown**:
```cpp
// test_user_service.cpp
#include <gtest/gtest.h>
#include "user_service.h"
#include "database.h"

class UserServiceTest : public ::testing::Test {
protected:
    // Runs before each test
    void SetUp() override {
        database_ = std::make_unique<Database>("test.db");
        user_service_ = std::make_unique<UserService>(database_.get());
    }

    // Runs after each test
    void TearDown() override {
        user_service_.reset();
        database_->ClearTestData();
        database_.reset();
    }

    // Member variables accessible in all tests
    std::unique_ptr<Database> database_;
    std::unique_ptr<UserService> user_service_;
};

TEST_F(UserServiceTest, CreateUser) {
    User user{"testuser", "test@example.com"};

    auto result = user_service_->CreateUser(user);

    ASSERT_NE(result, nullptr);
    EXPECT_EQ(result->username, "testuser");
}

TEST_F(UserServiceTest, FindUser) {
    User user{"alice", "alice@test.com"};
    user_service_->CreateUser(user);

    auto result = user_service_->FindUser(1);

    ASSERT_NE(result, nullptr);
    EXPECT_EQ(result->username, "alice");
}
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Suite-Level Setup (SetUpTestSuite/TearDownTestSuite)**:
```cpp
class DatabaseIntegrationTest : public ::testing::Test {
protected:
    // Runs once before all tests in this suite
    static void SetUpTestSuite() {
        shared_connection_ = std::make_shared<Connection>("test_db");
        shared_connection_->InitSchema();
    }

    // Runs once after all tests in this suite
    static void TearDownTestSuite() {
        shared_connection_->DropTables();
        shared_connection_.reset();
    }

    // Runs before each test
    void SetUp() override {
        shared_connection_->ClearData();
    }

    static std::shared_ptr<Connection> shared_connection_;
};

std::shared_ptr<Connection> DatabaseIntegrationTest::shared_connection_;

TEST_F(DatabaseIntegrationTest, InsertUser) {
    User user{1, "alice"};
    auto result = shared_connection_->Insert(user);

    EXPECT_EQ(result, 0);
    EXPECT_EQ(shared_connection_->CountUsers(), 1);
}

TEST_F(DatabaseIntegrationTest, QueryUsers) {
    User user{1, "alice"};
    shared_connection_->Insert(user);

    auto users = shared_connection_->Query("SELECT * FROM users");

    ASSERT_FALSE(users.empty());
    EXPECT_EQ(users[0].username, "alice");
}
```

**2. Parameterized Tests with Fixtures**:
```cpp
class UserValidationTest : public ::testing::TestWithParam<
    std::tuple<std::string, std::string, bool>> {
protected:
    void SetUp() override {
        validator_ = std::make_unique<UserValidator>();
    }

    std::unique_ptr<UserValidator> validator_;
};

TEST_P(UserValidationTest, ValidateUser) {
    auto [username, email, expected_valid] = GetParam();

    User user{username, email};
    bool result = validator_->Validate(user);

    EXPECT_EQ(result, expected_valid);
}

INSTANTIATE_TEST_SUITE_P(
    ValidationCases,
    UserValidationTest,
    ::testing::Values(
        std::make_tuple("alice", "alice@test.com", true),
        std::make_tuple("", "bob@test.com", false),
        std::make_tuple("charlie", "invalid-email", false),
        std::make_tuple("dave", "dave@test.com", true)
    )
);
```

**3. Nested Test Contexts**:
```cpp
class UserApiTest : public ::testing::Test {
protected:
    void SetUp() override {
        api_client_ = std::make_unique<ApiClient>();
    }

    std::unique_ptr<ApiClient> api_client_;
};

// Nested context for GET endpoints
class UserApiGetTest : public UserApiTest {
protected:
    void SetUp() override {
        UserApiTest::SetUp();
        // Additional setup for GET tests
        test_users_ = {
            User{1, "alice", "alice@test.com"},
            User{2, "bob", "bob@test.com"}
        };
        SeedDatabase(test_users_);
    }

    std::vector<User> test_users_;
};

TEST_F(UserApiGetTest, GetAllUsers) {
    auto response = api_client_->Get("/users");

    EXPECT_EQ(response.status_code, 200);
    EXPECT_EQ(response.users.size(), 2);
}

// Nested context for POST endpoints
class UserApiPostTest : public UserApiTest {
protected:
    void SetUp() override {
        UserApiTest::SetUp();
        // Additional setup for POST tests
    }
};

TEST_F(UserApiPostTest, CreateUser) {
    User new_user{0, "charlie", "charlie@test.com"};

    auto response = api_client_->Post("/users", new_user);

    EXPECT_EQ(response.status_code, 201);
    ASSERT_NE(response.user, nullptr);
    EXPECT_GT(response.user->id, 0);
}
```

### Fixture Factories

Create factories for flexible test data generation:

```cpp
// test_utils/user_factory.h
#pragma once

#include "user.h"
#include <memory>
#include <vector>
#include <functional>

class UserFactory {
public:
    UserFactory() : id_counter_(0) {}

    User Create() {
        return Create([](User&) {});
    }

    User Create(std::function<void(User&)> configure) {
        ++id_counter_;

        User user;
        user.id = id_counter_;
        user.username = "user_" + std::to_string(id_counter_);
        user.email = "user" + std::to_string(id_counter_) + "@test.com";
        user.age = 25;
        user.is_active = true;
        user.created_at = std::chrono::system_clock::now();

        configure(user);

        created_users_.push_back(user);
        return user;
    }

    std::vector<User> CreateBatch(size_t count) {
        return CreateBatch(count, [](User&) {});
    }

    std::vector<User> CreateBatch(size_t count,
                                  std::function<void(User&)> configure) {
        std::vector<User> users;
        users.reserve(count);

        for (size_t i = 0; i < count; ++i) {
            users.push_back(Create(configure));
        }

        return users;
    }

    void Reset() {
        id_counter_ = 0;
        created_users_.clear();
    }

    const std::vector<User>& GetCreatedUsers() const {
        return created_users_;
    }

private:
    int64_t id_counter_;
    std::vector<User> created_users_;
};

// Usage in tests
class UserOperationsTest : public ::testing::Test {
protected:
    void SetUp() override {
        factory_ = std::make_unique<UserFactory>();
    }

    std::unique_ptr<UserFactory> factory_;
};

TEST_F(UserOperationsTest, CreateWithDefaults) {
    auto user1 = factory_->Create();
    auto user2 = factory_->Create();

    EXPECT_EQ(user1.username, "user_1");
    EXPECT_EQ(user2.username, "user_2");
}

TEST_F(UserOperationsTest, CreateWithCustomData) {
    auto user = factory_->Create([](User& u) {
        u.username = "alice";
        u.email = "alice@example.com";
        u.age = 30;
    });

    EXPECT_EQ(user.username, "alice");
    EXPECT_EQ(user.age, 30);
}

TEST_F(UserOperationsTest, CreateBatch) {
    auto users = factory_->CreateBatch(5, [](User& u) {
        u.is_active = false;
    });

    ASSERT_EQ(users.size(), 5);
    for (const auto& user : users) {
        EXPECT_FALSE(user.is_active);
    }
}
```

### Builder Pattern for Complex Objects

```cpp
// test_utils/order_builder.h
#pragma once

#include "order.h"
#include <optional>
#include <vector>

class OrderBuilder {
public:
    OrderBuilder() {
        order_.status = OrderStatus::Pending;
        order_.total = 0.0;
    }

    OrderBuilder& WithId(int64_t id) {
        order_.id = id;
        return *this;
    }

    OrderBuilder& ForUser(int64_t user_id) {
        order_.user_id = user_id;
        return *this;
    }

    OrderBuilder& AddItem(int64_t product_id, int quantity, double price) {
        OrderItem item{product_id, quantity, price};
        order_.items.push_back(item);
        order_.total += quantity * price;
        return *this;
    }

    OrderBuilder& WithStatus(OrderStatus status) {
        order_.status = status;
        return *this;
    }

    OrderBuilder& WithShippingAddress(const Address& address) {
        order_.shipping_address = address;
        return *this;
    }

    Order Build() const {
        return order_;
    }

    std::unique_ptr<Order> BuildUnique() const {
        return std::make_unique<Order>(order_);
    }

    std::shared_ptr<Order> BuildShared() const {
        return std::make_shared<Order>(order_);
    }

private:
    Order order_;
};

// Usage
TEST(OrderProcessingTest, BuildComplexOrder) {
    Address address{"123 Main St", "Boston", "MA", "02101"};

    auto order = OrderBuilder()
        .WithId(1)
        .ForUser(100)
        .AddItem(1, 2, 10.00)
        .AddItem(2, 1, 15.00)
        .WithStatus(OrderStatus::Confirmed)
        .WithShippingAddress(address)
        .Build();

    EXPECT_EQ(order.total, 35.00);
    EXPECT_EQ(order.items.size(), 2);
    EXPECT_EQ(order.status, OrderStatus::Confirmed);
}
```

## Phase 2: Mocking with Google Mock (GMock)

### Understanding GMock

GMock is part of Google Test for creating mock objects:

**Define Interface**:
```cpp
// user_repository.h
class UserRepository {
public:
    virtual ~UserRepository() = default;

    virtual bool Save(const User& user) = 0;
    virtual std::optional<User> FindById(int64_t id) = 0;
    virtual std::vector<User> FindAll() = 0;
    virtual bool Delete(int64_t id) = 0;
};
```

**Create Mock**:
```cpp
// mocks/mock_user_repository.h
#include <gmock/gmock.h>
#include "user_repository.h"

class MockUserRepository : public UserRepository {
public:
    MOCK_METHOD(bool, Save, (const User& user), (override));
    MOCK_METHOD(std::optional<User>, FindById, (int64_t id), (override));
    MOCK_METHOD(std::vector<User>, FindAll, (), (override));
    MOCK_METHOD(bool, Delete, (int64_t id), (override));
};
```

**Using Mocks in Tests**:
```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "mock_user_repository.h"
#include "user_service.h"

using ::testing::Return;
using ::testing::_;
using ::testing::Ref;

class UserServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        mock_repository_ = std::make_shared<MockUserRepository>();
        service_ = std::make_unique<UserService>(mock_repository_);
    }

    std::shared_ptr<MockUserRepository> mock_repository_;
    std::unique_ptr<UserService> service_;
};

TEST_F(UserServiceTest, CreateUser) {
    User user{"alice", "alice@test.com"};

    // Set expectation
    EXPECT_CALL(*mock_repository_, Save(Ref(user)))
        .WillOnce(Return(true));

    // Execute
    bool result = service_->CreateUser(user);

    // Verify
    EXPECT_TRUE(result);
    // Expectations automatically verified by GMock
}

TEST_F(UserServiceTest, FindUser) {
    User expected_user{1, "alice", "alice@test.com"};

    // Set expectation with return value
    EXPECT_CALL(*mock_repository_, FindById(1))
        .WillOnce(Return(std::make_optional(expected_user)));

    // Execute
    auto result = service_->GetUser(1);

    // Verify
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result->username, "alice");
}
```

### When to Mock vs Use Real Objects

**Use Mocks For**:

- External APIs and services

- Database operations in unit tests

- File system operations

- Network requests

- Slow dependencies

- Non-deterministic behavior

**Use Real Objects For**:

- POD types and simple classes

- Value objects

- Pure functions

- Integration tests

- Critical business logic

```cpp
// GOOD - Mock external service
TEST_F(UserServiceTest, FetchFromExternalApi) {
    auto mock_api = std::make_shared<MockExternalApi>();

    EXPECT_CALL(*mock_api, GetUser(1))
        .WillOnce(Return(User{1, "alice"}));

    auto service = UserService(mock_api);
    auto result = service.FetchFromApi(1);

    EXPECT_EQ(result.username, "alice");
}

// GOOD - Use real object for simple logic
TEST(CalculatorTest, Sum) {
    std::vector<double> items = {10.0, 20.0, 30.0};
    double result = Calculator::Sum(items);
    EXPECT_EQ(result, 60.0);
}

// BAD - Over-mocking
TEST(CalculatorTest, SumWithMock) {
    auto mock_calc = std::make_shared<MockCalculator>();
    EXPECT_CALL(*mock_calc, Sum(_)).WillOnce(Return(60.0));
    // Testing mock behavior, not real code
}
```

### GMock Matchers and Actions

**Common Matchers**:
```cpp
using ::testing::_;          // Any value
using ::testing::Eq;         // Equal to
using ::testing::Ref;        // Reference to
using ::testing::Pointee;    // Pointer points to
using ::testing::NotNull;    // Not null pointer
using ::testing::IsNull;     // Null pointer
using ::testing::Gt;         // Greater than
using ::testing::Lt;         // Less than
using ::testing::Contains;   // Container contains

// Any argument
EXPECT_CALL(*mock, Method(_));

// Specific value
EXPECT_CALL(*mock, Method(Eq(42)));

// Reference to specific object
User user{"alice"};
EXPECT_CALL(*mock, Save(Ref(user)));

// Pointer matching
EXPECT_CALL(*mock, Process(Pointee(Eq(10))));

// Custom matcher
EXPECT_CALL(*mock, Save(
    ::testing::Property(&User::age, Gt(18))
));

// Multiple arguments
EXPECT_CALL(*mock, Method(Eq(1), Gt(10), NotNull()));
```

**Common Actions**:
```cpp
using ::testing::Return;
using ::testing::ReturnRef;
using ::testing::Throw;
using ::testing::Invoke;
using ::testing::DoAll;
using ::testing::SetArgPointee;

// Return value
EXPECT_CALL(*mock, GetValue())
    .WillOnce(Return(42));

// Return reference
User user{"alice"};
EXPECT_CALL(*mock, GetUser())
    .WillOnce(ReturnRef(user));

// Throw exception
EXPECT_CALL(*mock, Connect())
    .WillOnce(Throw(std::runtime_error("Connection failed")));

// Call actual function
EXPECT_CALL(*mock, Process(_))
    .WillOnce(Invoke([](int x) { return x * 2; }));

// Multiple returns
EXPECT_CALL(*mock, GetStatus())
    .WillOnce(Return(Status::Pending))
    .WillOnce(Return(Status::Complete))
    .WillRepeatedly(Return(Status::Complete));

// Set output parameter
EXPECT_CALL(*mock, GetData(_, _))
    .WillOnce(DoAll(
        SetArgPointee<1>(100),
        Return(true)
    ));
```

**Cardinality**:
```cpp
using ::testing::AtLeast;
using ::testing::AtMost;
using ::testing::Between;
using ::testing::Exactly;

// Called exactly once (default)
EXPECT_CALL(*mock, Method());

// Called at least once
EXPECT_CALL(*mock, Method()).Times(AtLeast(1));

// Called at most 3 times
EXPECT_CALL(*mock, Method()).Times(AtMost(3));

// Called between 2 and 5 times
EXPECT_CALL(*mock, Method()).Times(Between(2, 5));

// Called exactly 3 times
EXPECT_CALL(*mock, Method()).Times(Exactly(3));

// Never called
EXPECT_CALL(*mock, Method()).Times(0);
```

**Call Order**:
```cpp
using ::testing::InSequence;

TEST_F(UserServiceTest, CallOrder) {
    InSequence seq;

    EXPECT_CALL(*mock_repository_, Connect());
    EXPECT_CALL(*mock_repository_, Save(_));
    EXPECT_CALL(*mock_repository_, Disconnect());

    service_->CreateAndSaveUser(user);
}
```

## Phase 3: Mocking with Trompeloeil

### Understanding Trompeloeil

Trompeloeil is a modern C++ mocking framework:

```cpp
// Install: header-only library
// Download from https://github.com/rollbear/trompeloeil
```

**Create Mock**:
```cpp
#include <trompeloeil.hpp>

class MockUserRepository : public UserRepository {
public:
    MAKE_MOCK1(Save, bool(const User&), override);
    MAKE_MOCK1(FindById, std::optional<User>(int64_t), override);
    MAKE_MOCK0(FindAll, std::vector<User>(), override);
    MAKE_MOCK1(Delete, bool(int64_t), override);
};
```

**Using Trompeloeil Mocks**:
```cpp
#include <catch2/catch.hpp>
#include <trompeloeil.hpp>

TEST_CASE("UserService creates user") {
    auto mock_repo = std::make_shared<MockUserRepository>();
    auto service = UserService(mock_repo);

    User user{"alice", "alice@test.com"};

    // Set expectation
    REQUIRE_CALL(*mock_repo, Save(user))
        .RETURN(true);

    // Execute
    bool result = service.CreateUser(user);

    // Verify
    REQUIRE(result);
}

TEST_CASE("UserService finds user") {
    auto mock_repo = std::make_shared<MockUserRepository>();
    auto service = UserService(mock_repo);

    User expected{1, "alice", "alice@test.com"};

    REQUIRE_CALL(*mock_repo, FindById(1))
        .RETURN(std::make_optional(expected));

    auto result = service.GetUser(1);

    REQUIRE(result.has_value());
    REQUIRE(result->username == "alice");
}
```

**Trompeloeil Features**:
```cpp
using trompeloeil::_;
using trompeloeil::eq;
using trompeloeil::gt;

// Any argument
REQUIRE_CALL(*mock, Method(_));

// Specific value
REQUIRE_CALL(*mock, Method(eq(42)));

// Greater than
REQUIRE_CALL(*mock, Method(gt(10)));

// Custom matcher
REQUIRE_CALL(*mock, Save(
    trompeloeil::make_matcher<User>(
        [](const User& u) { return u.age > 18; },
        [](std::ostream& os, const User& u) {
            os << "user with age > 18, got " << u.age;
        }
    )
));

// Side effects
REQUIRE_CALL(*mock, Process(_))
    .SIDE_EFFECT(processed_count++)
    .RETURN(true);

// Sequences
auto seq = trompeloeil::sequence{};
REQUIRE_CALL(*mock, Connect()).IN_SEQUENCE(seq);
REQUIRE_CALL(*mock, Save(_)).IN_SEQUENCE(seq);
REQUIRE_CALL(*mock, Disconnect()).IN_SEQUENCE(seq);
```

## Phase 4: Advanced Testing Techniques

### Mocking HTTP Clients

```cpp
class MockHttpClient : public HttpClient {
public:
    MOCK_METHOD(Response, Get, (const std::string& url), (override));
    MOCK_METHOD(Response, Post, (const std::string& url, const std::string& body), (override));
};

TEST_F(ApiClientTest, GetUser) {
    auto mock_http = std::make_shared<MockHttpClient>();
    auto client = ApiClient(mock_http);

    Response expected_response{200, R"({"id":1,"username":"alice"})"};

    EXPECT_CALL(*mock_http, Get("/api/users/1"))
        .WillOnce(Return(expected_response));

    auto user = client.GetUser(1);

    ASSERT_TRUE(user.has_value());
    EXPECT_EQ(user->username, "alice");
}
```

### Mocking Time

```cpp
class Clock {
public:
    virtual ~Clock() = default;
    virtual std::chrono::system_clock::time_point Now() const = 0;
};

class MockClock : public Clock {
public:
    MOCK_METHOD(std::chrono::system_clock::time_point, Now, (), (const, override));
};

TEST_F(TimestampServiceTest, GenerateTimestamp) {
    auto mock_clock = std::make_shared<MockClock>();
    auto service = TimestampService(mock_clock);

    auto fixed_time = std::chrono::system_clock::from_time_t(1705320000);

    EXPECT_CALL(*mock_clock, Now())
        .WillOnce(Return(fixed_time));

    auto timestamp = service.GenerateTimestamp();

    EXPECT_EQ(timestamp, "2024-01-15T12:00:00Z");
}
```

### Mocking File System

```cpp
class FileSystem {
public:
    virtual ~FileSystem() = default;
    virtual std::string ReadFile(const std::string& path) = 0;
    virtual bool WriteFile(const std::string& path, const std::string& content) = 0;
};

class MockFileSystem : public FileSystem {
public:
    MOCK_METHOD(std::string, ReadFile, (const std::string&), (override));
    MOCK_METHOD(bool, WriteFile, (const std::string&, const std::string&), (override));
};

TEST_F(ConfigServiceTest, ReadConfig) {
    auto mock_fs = std::make_shared<MockFileSystem>();
    auto service = ConfigService(mock_fs);

    EXPECT_CALL(*mock_fs, ReadFile("config.txt"))
        .WillOnce(Return("setting=value\n"));

    auto config = service.LoadConfig("config.txt");

    EXPECT_EQ(config["setting"], "value");
}
```

### Using Faker Libraries

```cpp
// Using faker-cxx library
#include <faker-cxx/faker.h>

class UserFactoryWithFaker {
public:
    User CreateRandom() {
        return User{
            .id = faker::Number::integer<int64_t>(1, 1000000),
            .username = faker::Internet::username(),
            .email = faker::Internet::email(),
            .age = faker::Number::integer(18, 80),
            .first_name = faker::Person::firstName(),
            .last_name = faker::Person::lastName()
        };
    }

    std::vector<User> CreateRandomBatch(size_t count) {
        std::vector<User> users;
        users.reserve(count);
        for (size_t i = 0; i < count; ++i) {
            users.push_back(CreateRandom());
        }
        return users;
    }
};
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Suite-Level Setup** (SetUpTestSuite/TearDownTestSuite):

- [fixture_name]: [purpose, setup, teardown]

**Test-Level Setup** (SetUp/TearDown):

- [fixture_name]: [purpose, RAII usage]

**Fixture Factories**:

- [factory_name]: [creates what, lambda configuration]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Tool (GMock/Trompeloeil) | Reason |
|------------|------------------|--------------------------|--------|
| [API/Service] | [mock/fake] | [tool] | [justification] |

**Mock Configurations**:
```cpp
// Example mock setup
auto mock_repository = std::make_shared<MockUserRepository>();

EXPECT_CALL(*mock_repository, Save(_))
    .WillOnce(Return(true));
```

### Test Data Factories
**Factory Classes**:

- UserFactory: [lambda configuration, RAII]

- OrderFactory: [lambda configuration, RAII]

**Builder Classes**:

- [builder_name]: [purpose, fluent interface, smart pointers]

### Usage Examples
```cpp
// Example test using fixtures and mocks
class UserRegistrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        mock_email_ = std::make_shared<MockEmailService>();
        service_ = std::make_unique<UserService>(mock_email_);
        factory_ = std::make_unique<UserFactory>();
    }

    std::shared_ptr<MockEmailService> mock_email_;
    std::unique_ptr<UserService> service_;
    std::unique_ptr<UserFactory> factory_;
};

TEST_F(UserRegistrationTest, RegisterUser) {
    auto user = factory_->Create([](User& u) {
        u.username = "alice";
    });

    EXPECT_CALL(*mock_email_, SendWelcome(_))
        .WillOnce(Return(true));

    auto result = service_->RegisterUser(user);

    EXPECT_TRUE(result.has_value());
}
```

### Best Practices Implemented

- [ ] RAII ensures automatic cleanup

- [ ] Smart pointers manage memory

- [ ] Interfaces enable mocking

- [ ] Test data factories use lambda configuration

- [ ] Expectations clearly define behavior

- [ ] Parameterized tests for multiple cases

### Common Pitfalls Avoided

- Not using virtual destructors in interfaces

- Manual memory management instead of smart pointers

- Over-mocking value objects

- Complex expectation setups

- Testing mock behavior instead of real code

### Next Steps

- [ ] Implement remaining fixtures for integration tests

- [ ] Add factories for all domain classes

- [ ] Document fixture usage for team

- [ ] Set up mock interfaces for external dependencies

- [ ] Review mock coverage and necessity

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Comprehensive fixture setup** using Google Test patterns

2. **Mock configurations** for external dependencies

3. **Test data factories** using modern C++ features

4. **Builder patterns** with fluent interfaces

5. **Usage documentation** with examples

6. **Best practices guide** for GMock and Trompeloeil

7. **Fixture and mock catalog** for easy reference
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
