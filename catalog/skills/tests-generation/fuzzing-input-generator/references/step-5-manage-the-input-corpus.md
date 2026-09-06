### Step 5: Manage the Input Corpus

**Python:**
```python
import hashlib
import os
import json
from pathlib import Path


class CorpusManager:
    """Manage fuzz test input corpus with deduplication and coverage tracking."""

    def __init__(self, corpus_dir: str):
        self.corpus_dir = Path(corpus_dir)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.coverage_map = {}

    def add_seed(self, data: bytes, name: str = None) -> str:
        """Add a seed input to the corpus."""
        digest = hashlib.sha256(data).hexdigest()[:16]
        filename = name or f"seed_{digest}"
        filepath = self.corpus_dir / filename
        filepath.write_bytes(data)
        return str(filepath)

    def add_if_new_coverage(self, data: bytes, coverage: set) -> bool:
        """Add input to corpus only if it covers new code paths."""
        new_paths = coverage - set(self.coverage_map.keys())
        if new_paths:
            digest = hashlib.sha256(data).hexdigest()[:16]
            filepath = self.corpus_dir / f"cov_{digest}"
            filepath.write_bytes(data)
            for path in new_paths:
                self.coverage_map[path] = str(filepath)
            return True
        return False

    def load_corpus(self) -> list[bytes]:
        """Load all inputs from the corpus directory."""
        inputs = []
        for filepath in sorted(self.corpus_dir.iterdir()):
            if filepath.is_file():
                inputs.append(filepath.read_bytes())
        return inputs

    def minimize_corpus(self, coverage_fn):
        """Remove corpus entries that do not contribute unique coverage."""
        entries = []
        for filepath in sorted(self.corpus_dir.iterdir()):
            if filepath.is_file():
                data = filepath.read_bytes()
                coverage = coverage_fn(data)
                entries.append((filepath, data, coverage))

        # Greedy set cover: keep entries that contribute unique coverage
        total_coverage = set()
        kept = []
        entries.sort(key=lambda e: len(e[2]), reverse=True)
        for filepath, data, coverage in entries:
            new_coverage = coverage - total_coverage
            if new_coverage:
                kept.append(filepath)
                total_coverage |= coverage
            else:
                filepath.unlink()

        return len(kept)
```
