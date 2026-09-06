### Step 5: Orchestrate Multi-Agent Systems

**Supervisor Pattern (Hub-and-Spoke)**:

```python
@dataclass
class AgentConfig:
    name: str
    system_prompt: str
    tools: list[dict]
    model: str = "claude-sonnet-4-20250514"


class SupervisorOrchestrator:
    """A supervisor agent delegates tasks to specialist agents."""

    def __init__(self, specialists: list[AgentConfig]):
        self.specialists = {s.name: s for s in specialists}

    def run(self, goal: str) -> str:
        """Supervisor decomposes goal and delegates to specialists."""
        specialist_descriptions = "\n".join(
            f"- {s.name}: {s.system_prompt[:100]}..."
            for s in self.specialists.values()
        )

        # Supervisor decides which specialists to invoke and in what order
        plan_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=(
                "You are a supervisor agent. You delegate tasks to specialists.\n"
                f"Available specialists:\n{specialist_descriptions}\n\n"
                "For the given goal, output a JSON array of delegation steps:\n"
                '[{"specialist": "name", "task": "what to do", "depends_on": []}]'
            ),
            messages=[{"role": "user", "content": goal}],
        )

        delegations = json.loads(extract_text(plan_response.content))
        results = {}

        for step in delegations:
            specialist = self.specialists[step["specialist"]]
            context = {d: results[d] for d in step.get("depends_on", []) if d in results}
            result = self._run_specialist(
                specialist, step["task"], context
            )
            results[step["specialist"]] = result

        return self._synthesize(goal, results)

    def _run_specialist(
        self, config: AgentConfig, task: str, context: dict
    ) -> str:
        """Run a single specialist agent."""
        messages = [
            {
                "role": "user",
                "content": f"Task: {task}\nContext: {json.dumps(context)}",
            }
        ]
        response = client.messages.create(
            model=config.model,
            max_tokens=4096,
            system=config.system_prompt,
            tools=config.tools,
            messages=messages,
        )
        return extract_text(response.content)

    def _synthesize(self, goal: str, results: dict) -> str:
        """Combine specialist results into a final answer."""
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Original goal: {goal}\n\n"
                        f"Specialist results:\n{json.dumps(results, indent=2)}\n\n"
                        "Synthesize these results into a coherent final answer."
                    ),
                }
            ],
        )
        return extract_text(response.content)
```
