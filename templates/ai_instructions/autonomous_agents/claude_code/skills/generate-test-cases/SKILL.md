---
name: generate-test-cases
description: Create comprehensive unit, integration, and end-to-end tests with proper patterns and edge case coverage
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Testing
tags: [testing, test-cases, unit-tests, integration-tests, e2e, edge-cases, AAA-pattern, given-when-then]
priority: MEDIUM
based_on: Test Development Templates - Test Cases
---

# Generate Test Cases

Create comprehensive test suites covering unit tests, integration tests, and end-to-end scenarios with proper test patterns, edge case handling, and boundary testing across all supported languages.

## When to Use This Skill

Use this skill when:
- Implementing new features that need test coverage
- Adding tests to untested legacy code
- Improving test coverage for critical paths
- Systematically testing edge cases and boundaries
- Writing tests for bug fixes
- Creating regression test suites
- Documenting expected behavior through tests

**This skill is essential for**:
- New feature development with TDD
- Legacy code modernization
- Critical business logic validation
- API contract testing
- Integration point verification

## What This Skill Does

This skill helps you:
1. **Generate unit tests** for isolated functionality
2. **Create integration tests** for component interactions
3. **Develop E2E tests** for complete workflows
4. **Identify edge cases** and boundary conditions
5. **Apply test patterns** (AAA, Given-When-Then)
6. **Test error paths** and exception handling
7. **Verify input validation** thoroughly
8. **Test concurrent scenarios** where applicable

## Prerequisites

### Required
- Testing infrastructure set up (see `setup-test-infrastructure`)
- Understanding of code under test
- Knowledge of expected behavior
- Test framework familiarity

### Recommended
- Code coverage tool configured
- Mocking framework available
- Test data factories ready
- CI/CD pipeline configured

## Instructions

### Step 1: Identify Test Scenarios

Before writing tests, identify what needs to be tested:

**Happy Path Scenarios**:
- Normal execution with valid inputs
- Expected user workflows
- Common use cases

**Edge Cases**:
- Boundary values (min/max, zero, negative)
- Empty inputs (null, empty strings, empty arrays)
- Large inputs (performance boundaries)
- Special characters and Unicode
- Concurrent access

**Error Cases**:
- Invalid inputs
- Missing required data
- System failures (network, database)
- Permission errors
- Timeouts and rate limits

**Integration Points**:
- External API interactions
- Database operations
- File system access
- Message queues
- Third-party services

### Step 2: Write Unit Tests

Unit tests verify individual functions/methods in isolation.

**Python Example (pytest)**:
```python
"""
Unit tests for user validation module.
"""
import pytest
from myapp.validation import validate_email, validate_age


class TestEmailValidation:
    """Test email validation function."""

    def test_validate_email_accepts_valid_simple_email(self):
        """Test that simple valid email is accepted."""
        # Arrange
        email = "user@example.com"

        # Act
        result = validate_email(email)

        # Assert
        assert result is True

    def test_validate_email_accepts_email_with_subdomain(self):
        """Test that email with subdomain is accepted."""
        assert validate_email("user@mail.example.com") is True

    def test_validate_email_accepts_email_with_plus(self):
        """Test that email with + is accepted."""
        assert validate_email("user+tag@example.com") is True

    def test_validate_email_rejects_email_without_at_symbol(self):
        """Test that email without @ is rejected."""
        assert validate_email("userexample.com") is False

    def test_validate_email_rejects_email_without_domain(self):
        """Test that email without domain is rejected."""
        assert validate_email("user@") is False

    def test_validate_email_rejects_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_email("") is False

    def test_validate_email_rejects_none(self):
        """Test that None is rejected."""
        assert validate_email(None) is False

    def test_validate_email_rejects_multiple_at_symbols(self):
        """Test that email with multiple @ is rejected."""
        assert validate_email("user@@example.com") is False

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "first.last@example.co.uk",
        "user+tag@example.org",
        "123@test.com"
    ])
    def test_validate_email_accepts_various_valid_formats(self, email):
        """Test various valid email formats."""
        assert validate_email(email) is True

    @pytest.mark.parametrize("email", [
        "invalid",
        "@example.com",
        "user@",
        "user name@example.com",
        "user@example",
        ""
    ])
    def test_validate_email_rejects_various_invalid_formats(self, email):
        """Test various invalid email formats."""
        assert validate_email(email) is False


class TestAgeValidation:
    """Test age validation function."""

    def test_validate_age_accepts_valid_age(self):
        """Test that valid age is accepted."""
        assert validate_age(25) is True

    def test_validate_age_accepts_minimum_age(self):
        """Test that minimum age (18) is accepted."""
        assert validate_age(18) is True

    def test_validate_age_accepts_maximum_age(self):
        """Test that maximum age (120) is accepted."""
        assert validate_age(120) is True

    def test_validate_age_rejects_below_minimum(self):
        """Test that age below 18 is rejected."""
        assert validate_age(17) is False

    def test_validate_age_rejects_above_maximum(self):
        """Test that age above 120 is rejected."""
        assert validate_age(121) is False

    def test_validate_age_rejects_negative_age(self):
        """Test that negative age is rejected."""
        assert validate_age(-1) is False

    def test_validate_age_rejects_zero(self):
        """Test that zero age is rejected."""
        assert validate_age(0) is False

    def test_validate_age_rejects_non_integer(self):
        """Test that non-integer is rejected."""
        with pytest.raises(TypeError):
            validate_age("25")

    def test_validate_age_rejects_none(self):
        """Test that None is rejected."""
        with pytest.raises(TypeError):
            validate_age(None)
```

**JavaScript Example (Jest)**:
```javascript
/**

 * Unit tests for user validation module
 */
import { validateEmail, validateAge } from '../src/validation';

describe('Email Validation', () => {
  describe('Valid emails', () => {
    test('accepts simple valid email', () => {
      // Arrange
      const email = 'user@example.com';

      // Act
      const result = validateEmail(email);

      // Assert
      expect(result).toBe(true);
    });

    test('accepts email with subdomain', () => {
      expect(validateEmail('user@mail.example.com')).toBe(true);
    });

    test('accepts email with plus sign', () => {
      expect(validateEmail('user+tag@example.com')).toBe(true);
    });

    test.each([
      'user@example.com',
      'first.last@example.co.uk',
      'user+tag@example.org',
      '123@test.com'
    ])('accepts various valid formats: %s', (email) => {
      expect(validateEmail(email)).toBe(true);
    });
  });

  describe('Invalid emails', () => {
    test('rejects email without @ symbol', () => {
      expect(validateEmail('userexample.com')).toBe(false);
    });

    test('rejects email without domain', () => {
      expect(validateEmail('user@')).toBe(false);
    });

    test('rejects empty string', () => {
      expect(validateEmail('')).toBe(false);
    });

    test('rejects null', () => {
      expect(validateEmail(null)).toBe(false);
    });

    test('rejects multiple @ symbols', () => {
      expect(validateEmail('user@@example.com')).toBe(false);
    });

    test.each([
      'invalid',
      '@example.com',
      'user@',
      'user name@example.com',
      'user@example',
      ''
    ])('rejects various invalid formats: %s', (email) => {
      expect(validateEmail(email)).toBe(false);
    });
  });
});

describe('Age Validation', () => {
  describe('Valid ages', () => {
    test('accepts valid age', () => {
      expect(validateAge(25)).toBe(true);
    });

    test('accepts minimum age (18)', () => {
      expect(validateAge(18)).toBe(true);
    });

    test('accepts maximum age (120)', () => {
      expect(validateAge(120)).toBe(true);
    });
  });

  describe('Invalid ages', () => {
    test('rejects below minimum', () => {
      expect(validateAge(17)).toBe(false);
    });

    test('rejects above maximum', () => {
      expect(validateAge(121)).toBe(false);
    });

    test('rejects negative age', () => {
      expect(validateAge(-1)).toBe(false);
    });

    test('rejects zero', () => {
      expect(validateAge(0)).toBe(false);
    });

    test('throws on non-number', () => {
      expect(() => validateAge('25')).toThrow();
    });

    test('throws on null', () => {
      expect(() => validateAge(null)).toThrow();
    });
  });
});
```

**Java Example (JUnit 5)**:
```java
package com.example.validation;

import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Email Validation Tests")
class EmailValidationTest {

    @Nested
    @DisplayName("Valid emails")
    class ValidEmails {

        @Test
        @DisplayName("Should accept simple valid email")
        void acceptsSimpleValidEmail() {
            // Arrange
            String email = "user@example.com";

            // Act
            boolean result = EmailValidator.validate(email);

            // Assert
            assertTrue(result);
        }

        @Test
        @DisplayName("Should accept email with subdomain")
        void acceptsEmailWithSubdomain() {
            assertTrue(EmailValidator.validate("user@mail.example.com"));
        }

        @ParameterizedTest(name = "Should accept valid email: {0}")
        @ValueSource(strings = {
            "user@example.com",
            "first.last@example.co.uk",
            "user+tag@example.org",
            "123@test.com"
        })
        void acceptsVariousValidFormats(String email) {
            assertTrue(EmailValidator.validate(email));
        }
    }

    @Nested
    @DisplayName("Invalid emails")
    class InvalidEmails {

        @Test
        @DisplayName("Should reject email without @ symbol")
        void rejectsEmailWithoutAtSymbol() {
            assertFalse(EmailValidator.validate("userexample.com"));
        }

        @Test
        @DisplayName("Should reject empty string")
        void rejectsEmptyString() {
            assertFalse(EmailValidator.validate(""));
        }

        @Test
        @DisplayName("Should reject null")
        void rejectsNull() {
            assertFalse(EmailValidator.validate(null));
        }

        @ParameterizedTest(name = "Should reject invalid email: {0}")
        @ValueSource(strings = {
            "invalid",
            "@example.com",
            "user@",
            "user name@example.com",
            "user@example"
        })
        void rejectsVariousInvalidFormats(String email) {
            assertFalse(EmailValidator.validate(email));
        }
    }
}

@DisplayName("Age Validation Tests")
class AgeValidationTest {

    @Nested
    @DisplayName("Valid ages")
    class ValidAges {

        @Test
        @DisplayName("Should accept valid age")
        void acceptsValidAge() {
            assertTrue(AgeValidator.validate(25));
        }

        @Test
        @DisplayName("Should accept minimum age (18)")
        void acceptsMinimumAge() {
            assertTrue(AgeValidator.validate(18));
        }

        @Test
        @DisplayName("Should accept maximum age (120)")
        void acceptsMaximumAge() {
            assertTrue(AgeValidator.validate(120));
        }
    }

    @Nested
    @DisplayName("Invalid ages")
    class InvalidAges {

        @Test
        @DisplayName("Should reject below minimum")
        void rejectsBelowMinimum() {
            assertFalse(AgeValidator.validate(17));
        }

        @Test
        @DisplayName("Should reject above maximum")
        void rejectsAboveMaximum() {
            assertFalse(AgeValidator.validate(121));
        }

        @Test
        @DisplayName("Should reject negative age")
        void rejectsNegativeAge() {
            assertFalse(AgeValidator.validate(-1));
        }

        @Test
        @DisplayName("Should throw exception for null")
        void throwsOnNull() {
            assertThrows(IllegalArgumentException.class,
                () -> AgeValidator.validate(null));
        }
    }
}
```

**C# Example (xUnit)**:
```csharp
using Xunit;
using FluentAssertions;
using MyApp.Validation;

namespace MyApp.Tests.Unit
{
    public class EmailValidationTests
    {
        public class ValidEmails
        {
            [Fact]
            public void ShouldAcceptSimpleValidEmail()
            {
                // Arrange
                var email = "user@example.com";

                // Act
                var result = EmailValidator.Validate(email);

                // Assert
                result.Should().BeTrue();
            }

            [Fact]
            public void ShouldAcceptEmailWithSubdomain()
            {
                EmailValidator.Validate("user@mail.example.com")
                    .Should().BeTrue();
            }

            [Theory]
            [InlineData("user@example.com")]
            [InlineData("first.last@example.co.uk")]
            [InlineData("user+tag@example.org")]
            [InlineData("123@test.com")]
            public void ShouldAcceptVariousValidFormats(string email)
            {
                EmailValidator.Validate(email).Should().BeTrue();
            }
        }

        public class InvalidEmails
        {
            [Fact]
            public void ShouldRejectEmailWithoutAtSymbol()
            {
                EmailValidator.Validate("userexample.com")
                    .Should().BeFalse();
            }

            [Fact]
            public void ShouldRejectEmptyString()
            {
                EmailValidator.Validate(string.Empty)
                    .Should().BeFalse();
            }

            [Fact]
            public void ShouldRejectNull()
            {
                EmailValidator.Validate(null).Should().BeFalse();
            }

            [Theory]
            [InlineData("invalid")]
            [InlineData("@example.com")]
            [InlineData("user@")]
            [InlineData("user name@example.com")]
            public void ShouldRejectVariousInvalidFormats(string email)
            {
                EmailValidator.Validate(email).Should().BeFalse();
            }
        }
    }

    public class AgeValidationTests
    {
        public class ValidAges
        {
            [Fact]
            public void ShouldAcceptValidAge()
            {
                AgeValidator.Validate(25).Should().BeTrue();
            }

            [Fact]
            public void ShouldAcceptMinimumAge()
            {
                AgeValidator.Validate(18).Should().BeTrue();
            }

            [Fact]
            public void ShouldAcceptMaximumAge()
            {
                AgeValidator.Validate(120).Should().BeTrue();
            }
        }

        public class InvalidAges
        {
            [Fact]
            public void ShouldRejectBelowMinimum()
            {
                AgeValidator.Validate(17).Should().BeFalse();
            }

            [Fact]
            public void ShouldRejectAboveMaximum()
            {
                AgeValidator.Validate(121).Should().BeFalse();
            }

            [Fact]
            public void ShouldRejectNegativeAge()
            {
                AgeValidator.Validate(-1).Should().BeFalse();
            }

            [Fact]
            public void ShouldThrowOnNull()
            {
                Action act = () => AgeValidator.Validate(null);
                act.Should().Throw<ArgumentNullException>();
            }
        }
    }
}
```

**Go Example**:
```go
package validation_test

import (
    "testing"
    "myapp/validation"
)

// TestValidateEmail_ValidEmails tests valid email scenarios
func TestValidateEmail_ValidEmails(t *testing.T) {
    tests := []struct {
        name  string
        email string
    }{
        {"simple valid email", "user@example.com"},
        {"email with subdomain", "user@mail.example.com"},
        {"email with plus", "user+tag@example.com"},
        {"numeric user", "123@test.com"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Arrange
            email := tt.email

            // Act
            result := validation.ValidateEmail(email)

            // Assert
            if !result {
                t.Errorf("ValidateEmail(%q) = false, want true", email)
            }
        })
    }
}

// TestValidateEmail_InvalidEmails tests invalid email scenarios
func TestValidateEmail_InvalidEmails(t *testing.T) {
    tests := []struct {
        name  string
        email string
    }{
        {"no at symbol", "userexample.com"},
        {"no domain", "user@"},
        {"empty string", ""},
        {"multiple at symbols", "user@@example.com"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := validation.ValidateEmail(tt.email)
            if result {
                t.Errorf("ValidateEmail(%q) = true, want false", tt.email)
            }
        })
    }
}

// TestValidateAge_ValidAges tests valid age scenarios
func TestValidateAge_ValidAges(t *testing.T) {
    tests := []struct {
        name string
        age  int
        want bool
    }{
        {"valid age", 25, true},
        {"minimum age", 18, true},
        {"maximum age", 120, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := validation.ValidateAge(tt.age)
            if got != tt.want {
                t.Errorf("ValidateAge(%d) = %v, want %v", tt.age, got, tt.want)
            }
        })
    }
}

// TestValidateAge_InvalidAges tests invalid age scenarios
func TestValidateAge_InvalidAges(t *testing.T) {
    tests := []struct {
        name string
        age  int
    }{
        {"below minimum", 17},
        {"above maximum", 121},
        {"negative", -1},
        {"zero", 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if validation.ValidateAge(tt.age) {
                t.Errorf("ValidateAge(%d) should return false", tt.age)
            }
        })
    }
}
```

### Step 3: Write Integration Tests

Integration tests verify multiple components working together.

**Python Example (Database Integration)**:
```python
"""
Integration tests for user repository.
"""
import pytest
from myapp.repository import UserRepository
from myapp.database import Database


@pytest.fixture(scope="module")
def test_database():
    """Create test database for integration tests."""
    db = Database("test_db")
    db.setup_schema()
    yield db
    db.teardown()


@pytest.fixture
def user_repository(test_database):
    """Create user repository with clean database."""
    test_database.clear_all_tables()
    return UserRepository(test_database)


class TestUserRepository:
    """Integration tests for UserRepository."""

    def test_create_user_inserts_into_database(self, user_repository):
        """Test that creating user persists to database."""
        # Arrange
        user_data = {
            "username": "alice",
            "email": "alice@test.com",
            "age": 25
        }

        # Act
        user = user_repository.create(user_data)

        # Assert
        assert user.id is not None
        retrieved = user_repository.get_by_id(user.id)
        assert retrieved.username == "alice"
        assert retrieved.email == "alice@test.com"

    def test_update_user_modifies_database_record(self, user_repository):
        """Test that updating user changes database."""
        # Arrange
        user = user_repository.create({
            "username": "bob",
            "email": "bob@test.com"
        })

        # Act
        user_repository.update(user.id, {"email": "newemail@test.com"})

        # Assert
        updated = user_repository.get_by_id(user.id)
        assert updated.email == "newemail@test.com"
        assert updated.username == "bob"  # Unchanged

    def test_delete_user_removes_from_database(self, user_repository):
        """Test that deleting user removes record."""
        # Arrange
        user = user_repository.create({
            "username": "charlie",
            "email": "charlie@test.com"
        })

        # Act
        user_repository.delete(user.id)

        # Assert
        retrieved = user_repository.get_by_id(user.id)
        assert retrieved is None

    def test_find_by_email_queries_database(self, user_repository):
        """Test finding user by email."""
        # Arrange
        user_repository.create({
            "username": "dave",
            "email": "dave@test.com"
        })

        # Act
        found = user_repository.find_by_email("dave@test.com")

        # Assert
        assert found is not None
        assert found.username == "dave"

    def test_list_users_returns_all_users(self, user_repository):
        """Test listing all users."""
        # Arrange
        user_repository.create({"username": "user1", "email": "user1@test.com"})
        user_repository.create({"username": "user2", "email": "user2@test.com"})
        user_repository.create({"username": "user3", "email": "user3@test.com"})

        # Act
        users = user_repository.list()

        # Assert
        assert len(users) == 3
        usernames = [u.username for u in users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames
```

**JavaScript Example (API Integration)**:
```javascript
/**

 * Integration tests for user API
 */
import request from 'supertest';
import app from '../src/app';
import { setupDatabase, clearDatabase } from './helpers/database';

describe('User API Integration', () => {
  beforeAll(async () => {
    await setupDatabase();
  });

  afterAll(async () => {
    await clearDatabase();
  });

  beforeEach(async () => {
    await clearDatabase();
  });

  describe('POST /api/users', () => {
    test('creates user and returns 201', async () => {
      // Arrange
      const userData = {
        username: 'alice',
        email: 'alice@test.com',
        age: 25
      };

      // Act
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);

      // Assert
      expect(response.body).toHaveProperty('id');
      expect(response.body.username).toBe('alice');
      expect(response.body.email).toBe('alice@test.com');
    });

    test('returns 400 for invalid email', async () => {
      const userData = {
        username: 'bob',
        email: 'invalid-email',
        age: 30
      };

      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('email');
    });

    test('returns 409 for duplicate username', async () => {
      // Arrange - create first user
      await request(app)
        .post('/api/users')
        .send({
          username: 'charlie',
          email: 'charlie1@test.com',
          age: 25
        });

      // Act - try to create duplicate
      const response = await request(app)
        .post('/api/users')
        .send({
          username: 'charlie',
          email: 'charlie2@test.com',
          age: 25
        })
        .expect(409);

      // Assert
      expect(response.body.error).toContain('username already exists');
    });
  });

  describe('GET /api/users/:id', () => {
    test('returns user by ID', async () => {
      // Arrange - create user
      const createResponse = await request(app)
        .post('/api/users')
        .send({
          username: 'dave',
          email: 'dave@test.com'
        });

      const userId = createResponse.body.id;

      // Act
      const response = await request(app)
        .get(`/api/users/${userId}`)
        .expect(200);

      // Assert
      expect(response.body.id).toBe(userId);
      expect(response.body.username).toBe('dave');
    });

    test('returns 404 for non-existent user', async () => {
      const response = await request(app)
        .get('/api/users/99999')
        .expect(404);

      expect(response.body.error).toContain('not found');
    });
  });

  describe('PUT /api/users/:id', () => {
    test('updates user and returns updated data', async () => {
      // Arrange
      const createResponse = await request(app)
        .post('/api/users')
        .send({
          username: 'eve',
          email: 'eve@test.com'
        });

      const userId = createResponse.body.id;

      // Act
      const response = await request(app)
        .put(`/api/users/${userId}`)
        .send({ email: 'newemail@test.com' })
        .expect(200);

      // Assert
      expect(response.body.email).toBe('newemail@test.com');
      expect(response.body.username).toBe('eve'); // Unchanged
    });
  });

  describe('DELETE /api/users/:id', () => {
    test('deletes user and returns 204', async () => {
      // Arrange
      const createResponse = await request(app)
        .post('/api/users')
        .send({
          username: 'frank',
          email: 'frank@test.com'
        });

      const userId = createResponse.body.id;

      // Act
      await request(app)
        .delete(`/api/users/${userId}`)
        .expect(204);

      // Assert - verify deletion
      await request(app)
        .get(`/api/users/${userId}`)
        .expect(404);
    });
  });
});
```

### Step 4: Write End-to-End Tests

E2E tests verify complete user workflows.

**Python Example (E2E Workflow)**:
```python
"""
End-to-end tests for user registration workflow.
"""
import pytest
from myapp.app import create_app
from myapp.database import Database


@pytest.fixture(scope="module")
def app():
    """Create test application."""
    app = create_app(test_mode=True)
    yield app


@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope="module")
def database():
    """Set up test database."""
    db = Database("test_e2e_db")
    db.setup_schema()
    yield db
    db.teardown()


class TestUserRegistrationWorkflow:
    """E2E tests for complete user registration workflow."""

    def test_complete_user_registration_and_login(self, client, database):
        """Test complete workflow: register -> verify email -> login."""
        database.clear_all_tables()

        # Step 1: User registration
        register_response = client.post('/api/register', json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "SecurePass123!"
        })
        assert register_response.status_code == 201
        user_id = register_response.get_json()["user_id"]

        # Step 2: Verify email (get verification token from database)
        token = database.get_verification_token(user_id)
        verify_response = client.post(f'/api/verify-email/{token}')
        assert verify_response.status_code == 200

        # Step 3: Login with verified account
        login_response = client.post('/api/login', json={
            "username": "newuser",
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 200
        assert "access_token" in login_response.get_json()

        # Step 4: Access protected resource with token
        access_token = login_response.get_json()["access_token"]
        profile_response = client.get(
            '/api/profile',
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_response.status_code == 200
        profile = profile_response.get_json()
        assert profile["username"] == "newuser"
        assert profile["email"] == "newuser@test.com"
        assert profile["email_verified"] is True
```

### Step 5: Test Edge Cases and Boundaries

**Boundary Testing Example**:
```python
"""
Edge case and boundary testing.
"""
import pytest


class TestBoundaryConditions:
    """Test boundary values and edge cases."""

    @pytest.mark.parametrize("value,expected", [
        (0, "zero"),
        (1, "positive"),
        (-1, "negative"),
        (2147483647, "max_int"),   # Max 32-bit int
        (-2147483648, "min_int"),   # Min 32-bit int
    ])
    def test_integer_boundaries(self, value, expected):
        """Test integer boundary values."""
        result = classify_number(value)
        assert result == expected

    def test_empty_collection_handling(self):
        """Test behavior with empty collections."""
        assert process_items([]) == []
        assert calculate_sum([]) == 0
        assert find_max([]) is None

    def test_large_collection_handling(self):
        """Test behavior with very large collections."""
        large_list = list(range(1000000))
        result = process_items(large_list)
        assert len(result) == 1000000

    def test_unicode_string_handling(self):
        """Test Unicode and special character handling."""
        assert process_text("Hello 你好 مرحبا") is not None
        assert process_text("Emoji: 😀🎉") is not None
        assert process_text("Special: !@#$%^&*()") is not None

    def test_null_and_empty_string_handling(self):
        """Test null and empty string scenarios."""
        assert validate_input(None) is False
        assert validate_input("") is False
        assert validate_input("   ") is False  # Whitespace only

    def test_concurrent_access(self):
        """Test concurrent access scenarios."""
        import threading

        counter = Counter()
        threads = []

        def increment():
            for _ in range(1000):
                counter.increment()

        # Create 10 threads
        for _ in range(10):
            thread = threading.Thread(target=increment)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify thread-safe behavior
        assert counter.value == 10000
```

## Common Patterns

### Pattern 1: Arrange-Act-Assert (AAA)

Clear structure for all tests:

```python
def test_user_creation():
    # Arrange: Set up test data and conditions
    user_data = {"username": "alice", "email": "alice@test.com"}

    # Act: Execute the functionality under test
    result = create_user(user_data)

    # Assert: Verify expected outcomes
    assert result.id is not None
    assert result.username == "alice"
```

### Pattern 2: Given-When-Then (BDD Style)

```python
def test_user_login():
    # Given: A registered user exists
    user = create_user({"username": "bob", "password": "pass123"})

    # When: User attempts to login
    result = login(username="bob", password="pass123")

    # Then: Login succeeds and returns token
    assert result.success is True
    assert result.token is not None
```

### Pattern 3: Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (1, 1),
    (2, 4),
    (3, 9),
    (10, 100),
])
def test_square_function(input, expected):
    """Test square function with multiple inputs."""
    assert square(input) == expected
```

## Success Criteria

- [ ] Unit tests cover all public functions
- [ ] Integration tests verify component interactions
- [ ] E2E tests validate complete workflows
- [ ] Edge cases and boundaries tested
- [ ] Error paths tested
- [ ] Test naming follows conventions
- [ ] Tests follow AAA or Given-When-Then pattern
- [ ] Parametrized tests used where appropriate
- [ ] Test coverage meets minimum threshold (80%+)
- [ ] Tests run reliably and consistently

## Related Skills

- [`test-driven-development`](../test-driven-development/SKILL.md) - Write tests first
- [`setup-test-infrastructure`](../setup-test-infrastructure/SKILL.md) - Set up framework
- [`create-mocks-fixtures`](../create-mocks-fixtures/SKILL.md) - Create test data
- [`analyze-code-coverage`](../analyze-code-coverage/SKILL.md) - Measure coverage

## Additional Resources

### Testing Patterns
- [Arrange-Act-Assert Pattern](https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/)
- [Given-When-Then](https://martinfowler.com/bliki/GivenWhenThen.html)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

### Best Practices
- [Unit Testing Best Practices](https://docs.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices)
- [JavaScript Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)

---

**Version**: 1.0.0
**Last Updated**: January 2025
**Based on**: Test Development Templates - Test Cases
