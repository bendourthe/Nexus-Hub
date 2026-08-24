### Step 2: Set Up the Minimal Environment

Determine what environment setup the test needs and configure it with the minimum required state.

**Python: Environment setup helpers**

```python
import tempfile
import os
from contextlib import contextmanager
from unittest.mock import MagicMock

@contextmanager
def minimal_file_system(files: dict[str, str]):
    """Create a temporary file system with only the files needed for reproduction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for relative_path, content in files.items():
            full_path = os.path.join(tmpdir, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            yield tmpdir
        finally:
            os.chdir(original_cwd)


@contextmanager
def minimal_database_state(records: list[dict], table_name: str = "test_table"):
    """Create an in-memory SQLite database with minimal test data."""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    if records:
        columns = records[0].keys()
        col_defs = ", ".join(f"{col} TEXT" for col in columns)
        cursor.execute(f"CREATE TABLE {table_name} ({col_defs})")

        placeholders = ", ".join("?" for _ in columns)
        for record in records:
            values = tuple(str(v) for v in record.values())
            cursor.execute(
                f"INSERT INTO {table_name} VALUES ({placeholders})", values
            )
        conn.commit()

    try:
        yield conn
    finally:
        conn.close()


def create_mock_dependency(interface_methods: dict[str, any]) -> MagicMock:
    """Create a mock object with specific return values for reproduction."""
    mock = MagicMock()
    for method_name, return_value in interface_methods.items():
        if callable(return_value):
            getattr(mock, method_name).side_effect = return_value
        else:
            getattr(mock, method_name).return_value = return_value
    return mock
```

**JavaScript: Environment setup helpers**

```javascript
const fs = require("fs");
const path = require("path");
const os = require("os");

function createMinimalFileSystem(files) {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "repro-"));

  for (const [relativePath, content] of Object.entries(files)) {
    const fullPath = path.join(tmpDir, relativePath);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, content);
  }

  return {
    rootDir: tmpDir,
    cleanup() {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    },
  };
}

function createMockDependency(interfaceMethods) {
  const mock = {};
  for (const [method, behavior] of Object.entries(interfaceMethods)) {
    if (typeof behavior === "function") {
      mock[method] = jest.fn().mockImplementation(behavior);
    } else {
      mock[method] = jest.fn().mockReturnValue(behavior);
    }
  }
  return mock;
}

function withEnvironmentVariables(vars, testFn) {
  const original = {};
  for (const [key, value] of Object.entries(vars)) {
    original[key] = process.env[key];
    process.env[key] = value;
  }

  try {
    return testFn();
  } finally {
    for (const [key] of Object.entries(vars)) {
      if (original[key] === undefined) {
        delete process.env[key];
      } else {
        process.env[key] = original[key];
      }
    }
  }
}
```

**Java: Environment setup helpers**

```java
import java.nio.file.*;
import java.util.*;

public class MinimalEnvironment implements AutoCloseable {
    private final Path tempDir;

    public MinimalEnvironment(Map<String, String> files) throws Exception {
        this.tempDir = Files.createTempDirectory("repro-");

        for (var entry : files.entrySet()) {
            Path filePath = tempDir.resolve(entry.getKey());
            Files.createDirectories(filePath.getParent());
            Files.writeString(filePath, entry.getValue());
        }
    }

    public Path getRoot() {
        return tempDir;
    }

    public Path resolve(String relativePath) {
        return tempDir.resolve(relativePath);
    }

    @Override
    public void close() throws Exception {
        // Recursively delete temp directory
        Files.walk(tempDir)
            .sorted(Comparator.reverseOrder())
            .forEach(path -> {
                try { Files.delete(path); }
                catch (Exception ignored) {}
            });
    }
}
```
