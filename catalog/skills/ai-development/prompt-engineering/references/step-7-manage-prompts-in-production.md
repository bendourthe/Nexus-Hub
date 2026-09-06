### Step 7: Manage Prompts in Production

**Prompt Version Management**:

```python
import hashlib
from datetime import datetime


@dataclass
class PromptVersion:
    """A versioned prompt with metadata and lineage tracking."""
    name: str
    version: str
    content: str
    model: str
    created_at: str = ""
    parent_version: str | None = None
    eval_score: float | None = None
    notes: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:12]


class PromptRegistry:
    """Registry for managing prompt versions."""

    def __init__(self):
        self.prompts: dict[str, list[PromptVersion]] = {}

    def register(self, prompt: PromptVersion):
        """Register a new prompt version."""
        if prompt.name not in self.prompts:
            self.prompts[prompt.name] = []
        self.prompts[prompt.name].append(prompt)

    def get_latest(self, name: str) -> PromptVersion:
        """Get the latest version of a named prompt."""
        versions = self.prompts.get(name, [])
        if not versions:
            raise KeyError(f"No prompt registered with name: {name}")
        return versions[-1]

    def get_version(self, name: str, version: str) -> PromptVersion:
        """Get a specific version of a named prompt."""
        for pv in self.prompts.get(name, []):
            if pv.version == version:
                return pv
        raise KeyError(f"Prompt {name} version {version} not found")

    def compare(self, name: str, v1: str, v2: str) -> dict:
        """Compare two versions of a prompt."""
        p1 = self.get_version(name, v1)
        p2 = self.get_version(name, v2)
        return {
            "name": name,
            "versions": [v1, v2],
            "content_changed": p1.content_hash != p2.content_hash,
            "model_changed": p1.model != p2.model,
            "eval_delta": (
                (p2.eval_score or 0) - (p1.eval_score or 0)
                if p1.eval_score and p2.eval_score else None
            ),
        }


# Usage
registry = PromptRegistry()

registry.register(PromptVersion(
    name="ticket-classifier",
    version="1.0.0",
    content=CLASSIFICATION_SYSTEM,
    model="claude-sonnet-4-20250514",
    eval_score=0.87,
    notes="Initial version",
))

registry.register(PromptVersion(
    name="ticket-classifier",
    version="1.1.0",
    content=CLASSIFICATION_SYSTEM_V2,
    model="claude-sonnet-4-20250514",
    parent_version="1.0.0",
    eval_score=0.92,
    notes="Added few-shot examples, improved category descriptions",
))
```
