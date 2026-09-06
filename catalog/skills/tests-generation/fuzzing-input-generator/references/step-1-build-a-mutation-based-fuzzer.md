### Step 1: Build a Mutation-Based Fuzzer

**Python:**
```python
import random
import struct
from typing import Callable


class MutationFuzzer:
    """Simple mutation-based fuzzer that applies random mutations to seed inputs."""

    INTERESTING_BYTES = [0x00, 0x01, 0x7F, 0x80, 0xFF]
    INTERESTING_INTS = [0, 1, -1, 0x7FFFFFFF, -0x80000000, 0xFFFFFFFF, 0x100, 0x1000]

    def __init__(self, seeds: list[bytes], max_mutations: int = 10):
        self.corpus = list(seeds)
        self.max_mutations = max_mutations

    def mutate(self, data: bytes) -> bytes:
        """Apply a random mutation to the input bytes."""
        if len(data) == 0:
            return bytes([random.randint(0, 255)])

        mutation = random.choice([
            self._bit_flip,
            self._byte_replace,
            self._byte_insert,
            self._byte_delete,
            self._block_duplicate,
            self._arithmetic_mutate,
        ])
        return mutation(bytearray(data))

    def _bit_flip(self, data: bytearray) -> bytes:
        idx = random.randint(0, len(data) - 1)
        bit = random.randint(0, 7)
        data[idx] ^= (1 << bit)
        return bytes(data)

    def _byte_replace(self, data: bytearray) -> bytes:
        idx = random.randint(0, len(data) - 1)
        data[idx] = random.choice(self.INTERESTING_BYTES)
        return bytes(data)

    def _byte_insert(self, data: bytearray) -> bytes:
        idx = random.randint(0, len(data))
        data.insert(idx, random.randint(0, 255))
        return bytes(data)

    def _byte_delete(self, data: bytearray) -> bytes:
        if len(data) <= 1:
            return bytes(data)
        idx = random.randint(0, len(data) - 1)
        del data[idx]
        return bytes(data)

    def _block_duplicate(self, data: bytearray) -> bytes:
        if len(data) < 2:
            return bytes(data)
        start = random.randint(0, len(data) - 2)
        length = random.randint(1, min(16, len(data) - start))
        block = data[start:start + length]
        insert_at = random.randint(0, len(data))
        return bytes(data[:insert_at] + block + data[insert_at:])

    def _arithmetic_mutate(self, data: bytearray) -> bytes:
        if len(data) < 4:
            return bytes(data)
        idx = random.randint(0, len(data) - 4)
        value = struct.unpack_from("<I", data, idx)[0]
        value += random.choice([-1, 1, -256, 256])
        value &= 0xFFFFFFFF
        struct.pack_into("<I", data, idx, value)
        return bytes(data)

    def generate(self, count: int) -> list[bytes]:
        """Generate `count` mutated inputs from the corpus."""
        results = []
        for _ in range(count):
            seed = random.choice(self.corpus)
            mutated = seed
            num_mutations = random.randint(1, self.max_mutations)
            for _ in range(num_mutations):
                mutated = self.mutate(mutated)
            results.append(mutated)
        return results

    def fuzz(self, target: Callable[[bytes], None], iterations: int = 1000):
        """Run the fuzzer against a target function, catching crashes."""
        crashes = []
        for i in range(iterations):
            test_input = self.generate(1)[0]
            try:
                target(test_input)
            except Exception as e:
                crashes.append({
                    "input": test_input,
                    "error": str(e),
                    "type": type(e).__name__,
                    "iteration": i,
                })
        return crashes


# Usage example: fuzz a JSON parser
def fuzz_json_parser():
    import json

    seeds = [
        b'{}',
        b'[]',
        b'{"key": "value"}',
        b'[1, 2, 3]',
        b'{"nested": {"deep": true}}',
    ]

    fuzzer = MutationFuzzer(seeds, max_mutations=5)

    def target(data: bytes):
        json.loads(data.decode("utf-8", errors="replace"))

    crashes = fuzzer.fuzz(target, iterations=10000)
    print(f"Found {len(crashes)} unique crash types")
    unique_types = set(c["type"] for c in crashes)
    for t in unique_types:
        example = next(c for c in crashes if c["type"] == t)
        print(f"  {t}: {example['error'][:80]}")
```

**JavaScript:**
```javascript
class MutationFuzzer {
  static INTERESTING_BYTES = [0x00, 0x01, 0x7f, 0x80, 0xff];

  constructor(seeds, maxMutations = 10) {
    this.corpus = seeds.map((s) =>
      typeof s === "string" ? Buffer.from(s) : s
    );
    this.maxMutations = maxMutations;
  }

  mutate(data) {
    if (data.length === 0) {
      return Buffer.from([Math.floor(Math.random() * 256)]);
    }

    const mutations = [
      this.bitFlip,
      this.byteReplace,
      this.byteInsert,
      this.byteDelete,
    ];
    const mutation = mutations[Math.floor(Math.random() * mutations.length)];
    return mutation.call(this, Buffer.from(data));
  }

  bitFlip(data) {
    const idx = Math.floor(Math.random() * data.length);
    const bit = Math.floor(Math.random() * 8);
    data[idx] ^= 1 << bit;
    return data;
  }

  byteReplace(data) {
    const idx = Math.floor(Math.random() * data.length);
    data[idx] =
      MutationFuzzer.INTERESTING_BYTES[
        Math.floor(Math.random() * MutationFuzzer.INTERESTING_BYTES.length)
      ];
    return data;
  }

  byteInsert(data) {
    const idx = Math.floor(Math.random() * (data.length + 1));
    const byte = Math.floor(Math.random() * 256);
    return Buffer.concat([data.slice(0, idx), Buffer.from([byte]), data.slice(idx)]);
  }

  byteDelete(data) {
    if (data.length <= 1) return data;
    const idx = Math.floor(Math.random() * data.length);
    return Buffer.concat([data.slice(0, idx), data.slice(idx + 1)]);
  }

  fuzz(target, iterations = 1000) {
    const crashes = [];
    for (let i = 0; i < iterations; i++) {
      const seed = this.corpus[Math.floor(Math.random() * this.corpus.length)];
      let mutated = Buffer.from(seed);
      const numMutations = Math.floor(Math.random() * this.maxMutations) + 1;
      for (let m = 0; m < numMutations; m++) {
        mutated = this.mutate(mutated);
      }
      try {
        target(mutated);
      } catch (e) {
        crashes.push({ input: mutated, error: e.message, iteration: i });
      }
    }
    return crashes;
  }
}

// Usage: fuzz a JSON parser
const fuzzer = new MutationFuzzer(['{}', '[]', '{"key":"value"}']);
const crashes = fuzzer.fuzz((data) => {
  JSON.parse(data.toString("utf-8"));
}, 10000);
console.log(`Found ${crashes.length} crashes`);
```

**Java:**
```java
import java.util.*;

public class MutationFuzzer {

    private static final byte[] INTERESTING = {0x00, 0x01, 0x7F, (byte) 0x80, (byte) 0xFF};
    private final List<byte[]> corpus;
    private final Random rng;
    private final int maxMutations;

    public MutationFuzzer(List<byte[]> seeds, int maxMutations) {
        this.corpus = new ArrayList<>(seeds);
        this.rng = new Random();
        this.maxMutations = maxMutations;
    }

    public byte[] mutate(byte[] data) {
        if (data.length == 0) {
            return new byte[]{(byte) rng.nextInt(256)};
        }
        int mutation = rng.nextInt(3);
        byte[] copy = data.clone();
        return switch (mutation) {
            case 0 -> bitFlip(copy);
            case 1 -> byteReplace(copy);
            case 2 -> byteInsert(copy);
            default -> copy;
        };
    }

    private byte[] bitFlip(byte[] data) {
        int idx = rng.nextInt(data.length);
        int bit = rng.nextInt(8);
        data[idx] ^= (byte) (1 << bit);
        return data;
    }

    private byte[] byteReplace(byte[] data) {
        int idx = rng.nextInt(data.length);
        data[idx] = INTERESTING[rng.nextInt(INTERESTING.length)];
        return data;
    }

    private byte[] byteInsert(byte[] data) {
        int idx = rng.nextInt(data.length + 1);
        byte[] result = new byte[data.length + 1];
        System.arraycopy(data, 0, result, 0, idx);
        result[idx] = (byte) rng.nextInt(256);
        System.arraycopy(data, idx, result, idx + 1, data.length - idx);
        return result;
    }

    public record CrashInfo(byte[] input, String error, int iteration) {}

    public List<CrashInfo> fuzz(java.util.function.Consumer<byte[]> target, int iterations) {
        var crashes = new ArrayList<CrashInfo>();
        for (int i = 0; i < iterations; i++) {
            byte[] seed = corpus.get(rng.nextInt(corpus.size()));
            byte[] mutated = seed.clone();
            int numMuts = rng.nextInt(maxMutations) + 1;
            for (int m = 0; m < numMuts; m++) {
                mutated = mutate(mutated);
            }
            try {
                target.accept(mutated);
            } catch (Exception e) {
                crashes.add(new CrashInfo(mutated, e.getMessage(), i));
            }
        }
        return crashes;
    }
}
```
