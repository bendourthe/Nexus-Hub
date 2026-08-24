### Step 3: Set Up Coverage-Guided Fuzzing

**Python (with Atheris, Google's Python fuzzer):**
```python
# Install: pip install atheris

import atheris
import sys
import json


@atheris.instrument_func
def fuzz_json_parser(data):
    """Coverage-guided fuzz target for the JSON parser."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        json_str = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
        json.loads(json_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass  # Expected errors, not crashes


@atheris.instrument_func
def fuzz_url_parser(data):
    """Coverage-guided fuzz target for URL parsing."""
    from urllib.parse import urlparse, parse_qs
    try:
        fdp = atheris.FuzzedDataProvider(data)
        url = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
        parsed = urlparse(url)
        if parsed.query:
            parse_qs(parsed.query)
    except Exception:
        pass  # Document but do not suppress unexpected exceptions


def main():
    atheris.Setup(sys.argv, fuzz_json_parser)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

# Run: python fuzz_target.py -max_total_time=60 corpus/
```

**Java (Jazzer):**
```java
import com.code_intelligence.jazzer.api.FuzzedDataProvider;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Jazzer fuzz target for Jackson JSON parser.
 * Run: jazzer --target_class=JsonFuzzTarget --corpus=corpus/
 */
public class JsonFuzzTarget {

    private static final ObjectMapper mapper = new ObjectMapper();

    public static void fuzzerTestOneInput(FuzzedDataProvider data) {
        String jsonStr = data.consumeRemainingAsString();
        try {
            mapper.readTree(jsonStr);
        } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
            // Expected: malformed JSON
        } catch (Exception e) {
            // Unexpected exception type indicates a potential bug
            throw e;
        }
    }
}
```
