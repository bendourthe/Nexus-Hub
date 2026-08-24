### Step 3: Build Memory Systems

Agents need memory to maintain context across turns, learn from past interactions, and recall relevant information.

**Memory Type Overview**:

| Type | Scope | Storage | Use Case |
|------|-------|---------|----------|
| **Working** | Current conversation | Message history | Immediate context |
| **Episodic** | Past interactions | Database | Recall similar tasks |
| **Semantic** | Domain knowledge | Vector store | Fact retrieval |
| **Procedural** | Learned workflows | Key-value store | Skill reuse |

**Working Memory (Conversation Buffer with Summarization)**:

```python
from dataclasses import dataclass


@dataclass
class WorkingMemory:
    messages: list[dict]
    max_tokens: int = 100_000
    summary: str = ""

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if self.estimate_tokens() > self.max_tokens * 0.8:
            self.compact()

    def compact(self):
        """Summarize older messages to free context space."""
        # Keep the most recent messages intact
        keep_recent = 6
        old_messages = self.messages[:-keep_recent]
        recent_messages = self.messages[-keep_recent:]

        summary_prompt = (
            f"Previous summary: {self.summary}\n\n"
            f"New messages to summarize:\n"
            f"{format_messages(old_messages)}\n\n"
            "Produce a concise summary preserving key decisions, "
            "findings, and action items."
        )
        self.summary = call_llm_for_summary(summary_prompt)
        self.messages = recent_messages

    def get_context(self) -> list[dict]:
        """Return messages with summary prepended if available."""
        if self.summary:
            summary_msg = {
                "role": "user",
                "content": f"[Context from earlier in this conversation]\n{self.summary}"
            }
            return [summary_msg] + self.messages
        return self.messages

    def estimate_tokens(self) -> int:
        return sum(len(m["content"]) // 4 for m in self.messages)
```

**Long-Term Episodic Memory**:

```python
import hashlib
from datetime import datetime


class EpisodicMemory:
    """Store and recall past agent interactions by similarity."""

    def __init__(self, vector_store, embedding_model):
        self.store = vector_store
        self.embedder = embedding_model

    def record_episode(self, task: str, trajectory: list[dict], outcome: str):
        """Save a completed task episode for future recall."""
        episode = {
            "task": task,
            "trajectory_summary": summarize_trajectory(trajectory),
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat(),
            "id": hashlib.sha256(f"{task}{datetime.utcnow()}".encode()).hexdigest()[:16],
        }
        embedding = self.embedder.embed(f"{task} {outcome}")
        self.store.upsert(id=episode["id"], vector=embedding, metadata=episode)

    def recall(self, current_task: str, top_k: int = 3) -> list[dict]:
        """Recall past episodes similar to the current task."""
        query_embedding = self.embedder.embed(current_task)
        results = self.store.query(vector=query_embedding, top_k=top_k)
        return [
            {
                "task": r.metadata["task"],
                "approach": r.metadata["trajectory_summary"],
                "outcome": r.metadata["outcome"],
                "similarity": r.score,
            }
            for r in results
        ]
```
