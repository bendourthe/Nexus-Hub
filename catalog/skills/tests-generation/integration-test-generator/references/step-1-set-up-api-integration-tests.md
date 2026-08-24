### Step 1: Set Up API Integration Tests

**Python (FastAPI + pytest + httpx):**
```python
import pytest
from httpx import AsyncClient, ASGITransport
from myapp.main import app
from myapp.database import get_db, Base, engine


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Async HTTP client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestUserApi:
    """Integration tests for the /users API endpoints."""

    async def test_create_user_returns_201(self, client):
        response = await client.post("/users", json={
            "email": "alice@example.com",
            "name": "Alice",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "alice@example.com"
        assert "id" in data

    async def test_create_duplicate_email_returns_409(self, client):
        await client.post("/users", json={
            "email": "bob@example.com",
            "name": "Bob",
        })
        response = await client.post("/users", json={
            "email": "bob@example.com",
            "name": "Bob Again",
        })
        assert response.status_code == 409

    async def test_get_user_by_id(self, client):
        create_response = await client.post("/users", json={
            "email": "carol@example.com",
            "name": "Carol",
        })
        user_id = create_response.json()["id"]

        get_response = await client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Carol"

    async def test_get_nonexistent_user_returns_404(self, client):
        response = await client.get("/users/99999")
        assert response.status_code == 404

    async def test_delete_user_returns_204(self, client):
        create_response = await client.post("/users", json={
            "email": "dave@example.com",
            "name": "Dave",
        })
        user_id = create_response.json()["id"]

        delete_response = await client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204

        get_response = await client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    async def test_list_users_with_pagination(self, client):
        for i in range(15):
            await client.post("/users", json={
                "email": f"user{i}@example.com",
                "name": f"User {i}",
            })
        response = await client.get("/users?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15

    async def test_create_user_with_invalid_email_returns_422(self, client):
        response = await client.post("/users", json={
            "email": "not-an-email",
            "name": "Invalid",
        })
        assert response.status_code == 422
```

**JavaScript (Express + supertest + Jest):**
```javascript
const request = require("supertest");
const { createApp } = require("../src/app");
const { setupDatabase, teardownDatabase, getDb } = require("../src/database");

let app;
let db;

beforeAll(async () => {
  db = await setupDatabase({ inMemory: true });
  app = createApp({ db });
});

afterAll(async () => {
  await teardownDatabase(db);
});

afterEach(async () => {
  await db("users").truncate();
});

describe("POST /users", () => {
  test("creates a user and returns 201", async () => {
    const response = await request(app)
      .post("/users")
      .send({ email: "alice@example.com", name: "Alice" })
      .expect(201);

    expect(response.body).toMatchObject({
      email: "alice@example.com",
      name: "Alice",
    });
    expect(response.body.id).toBeDefined();
  });

  test("returns 409 for duplicate email", async () => {
    await request(app)
      .post("/users")
      .send({ email: "bob@example.com", name: "Bob" })
      .expect(201);

    await request(app)
      .post("/users")
      .send({ email: "bob@example.com", name: "Bob Again" })
      .expect(409);
  });

  test("returns 422 for invalid email", async () => {
    await request(app)
      .post("/users")
      .send({ email: "not-an-email", name: "Invalid" })
      .expect(422);
  });
});

describe("GET /users/:id", () => {
  test("returns the user by ID", async () => {
    const createResponse = await request(app)
      .post("/users")
      .send({ email: "carol@example.com", name: "Carol" })
      .expect(201);

    const response = await request(app)
      .get(`/users/${createResponse.body.id}`)
      .expect(200);

    expect(response.body.name).toBe("Carol");
  });

  test("returns 404 for nonexistent user", async () => {
    await request(app).get("/users/99999").expect(404);
  });
});

describe("DELETE /users/:id", () => {
  test("deletes the user and returns 204", async () => {
    const createResponse = await request(app)
      .post("/users")
      .send({ email: "dave@example.com", name: "Dave" })
      .expect(201);

    await request(app)
      .delete(`/users/${createResponse.body.id}`)
      .expect(204);

    await request(app)
      .get(`/users/${createResponse.body.id}`)
      .expect(404);
  });
});
```

**Java (Spring Boot + JUnit 5 + MockMvc):**
```java
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class UserApiIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @AfterEach
    void tearDown() {
        userRepository.deleteAll();
    }

    @Test
    void createUserReturns201() throws Exception {
        mockMvc.perform(post("/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email": "alice@example.com", "name": "Alice"}
                    """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.email").value("alice@example.com"))
                .andExpect(jsonPath("$.id").isNumber());
    }

    @Test
    void duplicateEmailReturns409() throws Exception {
        mockMvc.perform(post("/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email": "bob@example.com", "name": "Bob"}
                    """))
                .andExpect(status().isCreated());

        mockMvc.perform(post("/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email": "bob@example.com", "name": "Bob Again"}
                    """))
                .andExpect(status().isConflict());
    }

    @Test
    void getUserByIdReturns200() throws Exception {
        var result = mockMvc.perform(post("/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email": "carol@example.com", "name": "Carol"}
                    """))
                .andExpect(status().isCreated())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        int userId = com.fasterxml.jackson.databind.ObjectMapper
                .readTree(body).get("id").asInt();

        mockMvc.perform(get("/users/" + userId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Carol"));
    }

    @Test
    void getNonexistentUserReturns404() throws Exception {
        mockMvc.perform(get("/users/99999"))
                .andExpect(status().isNotFound());
    }
}
```
