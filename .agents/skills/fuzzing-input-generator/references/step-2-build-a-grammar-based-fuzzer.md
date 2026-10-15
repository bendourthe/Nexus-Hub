### Step 2: Build a Grammar-Based Fuzzer

**Python:**
```python
import random
import string


class GrammarFuzzer:
    """Generate inputs from a context-free grammar with controlled randomness."""

    def __init__(self, grammar: dict, start: str = "<start>", max_depth: int = 10):
        self.grammar = grammar
        self.start = start
        self.max_depth = max_depth

    def generate(self, symbol: str = None, depth: int = 0) -> str:
        if symbol is None:
            symbol = self.start

        if symbol not in self.grammar:
            return symbol  # Terminal symbol

        expansions = self.grammar[symbol]

        if depth >= self.max_depth:
            # Choose the shortest expansion to terminate
            expansions = sorted(expansions, key=lambda e: len(e))
            expansion = expansions[0]
        else:
            expansion = random.choice(expansions)

        result = ""
        for part in expansion:
            result += self.generate(part, depth + 1)
        return result


# JSON grammar for fuzzing JSON parsers
JSON_GRAMMAR = {
    "<start>": [["<value>"]],
    "<value>": [
        ["<object>"], ["<array>"], ["<string>"], ["<number>"],
        ["true"], ["false"], ["null"],
    ],
    "<object>": [
        ["{", "}"],
        ["{", "<members>", "}"],
    ],
    "<members>": [
        ["<pair>"],
        ["<pair>", ",", "<members>"],
    ],
    "<pair>": [["<string>", ":", "<value>"]],
    "<array>": [
        ["[", "]"],
        ["[", "<elements>", "]"],
    ],
    "<elements>": [
        ["<value>"],
        ["<value>", ",", "<elements>"],
    ],
    "<string>": [
        ['"', "<chars>", '"'],
        ['"', '"'],
    ],
    "<chars>": [
        ["<char>"],
        ["<char>", "<chars>"],
    ],
    "<char>": [[c] for c in string.ascii_letters + string.digits + " _-"],
    "<number>": [
        ["<digits>"],
        ["-", "<digits>"],
        ["<digits>", ".", "<digits>"],
        ["<digits>", "e", "<digits>"],
    ],
    "<digits>": [
        ["<digit>"],
        ["<digit>", "<digits>"],
    ],
    "<digit>": [[str(d)] for d in range(10)],
}

# Generate fuzzed JSON inputs
fuzzer = GrammarFuzzer(JSON_GRAMMAR, max_depth=8)
for _ in range(10):
    fuzzed_json = fuzzer.generate()
    print(repr(fuzzed_json))
```

**JavaScript:**
```javascript
class GrammarFuzzer {
  constructor(grammar, start = "<start>", maxDepth = 10) {
    this.grammar = grammar;
    this.start = start;
    this.maxDepth = maxDepth;
  }

  generate(symbol = null, depth = 0) {
    if (symbol === null) symbol = this.start;
    if (!(symbol in this.grammar)) return symbol;

    let expansions = this.grammar[symbol];

    if (depth >= this.maxDepth) {
      expansions = [...expansions].sort((a, b) => a.length - b.length);
      expansions = [expansions[0]];
    }

    const expansion = expansions[Math.floor(Math.random() * expansions.length)];
    return expansion.map((part) => this.generate(part, depth + 1)).join("");
  }
}

// SQL grammar for fuzzing SQL parsers
const SQL_GRAMMAR = {
  "<start>": [["<statement>"]],
  "<statement>": [
    ["SELECT ", "<columns>", " FROM ", "<table>"],
    ["SELECT ", "<columns>", " FROM ", "<table>", " WHERE ", "<condition>"],
    ["INSERT INTO ", "<table>", " VALUES (", "<values>", ")"],
  ],
  "<columns>": [["*"], ["<column>"], ["<column>", ", ", "<columns>"]],
  "<column>": [["id"], ["name"], ["email"], ["age"], ["created_at"]],
  "<table>": [["users"], ["orders"], ["products"]],
  "<condition>": [
    ["<column>", " = ", "<literal>"],
    ["<column>", " > ", "<number>"],
    ["<column>", " IS NULL"],
    ["<condition>", " AND ", "<condition>"],
  ],
  "<values>": [["<literal>"], ["<literal>", ", ", "<values>"]],
  "<literal>": [["'", "<word>", "'"], ["<number>"], ["NULL"]],
  "<word>": [["test"], ["hello"], ["admin"], ["' OR 1=1 --"]],
  "<number>": [["0"], ["1"], ["-1"], ["999999"], ["2147483647"]],
};

const fuzzer = new GrammarFuzzer(SQL_GRAMMAR, "<start>", 6);
for (let i = 0; i < 10; i++) {
  console.log(fuzzer.generate());
}
```
