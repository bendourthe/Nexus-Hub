### Step 4: Implement Planning and Reasoning Loops

**Reflection Pattern (Self-Critique Loop)**:

```python
def reflect_and_improve(task: str, max_iterations: int = 3) -> str:
    """Generate output, critique it, and iterate until quality threshold is met."""
    draft = generate_initial_response(task)

    for iteration in range(max_iterations):
        critique = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}\n\n"
                        f"Current output:\n{draft}\n\n"
                        "Critique this output. Identify specific problems with:\n"
                        "1. Correctness: Are there factual or logical errors?\n"
                        "2. Completeness: Is anything missing?\n"
                        "3. Quality: Could the structure or clarity improve?\n\n"
                        "If the output is satisfactory, respond with ONLY 'APPROVED'.\n"
                        "Otherwise, list specific improvements needed."
                    ),
                }
            ],
        )

        critique_text = extract_text(critique.content)

        if "APPROVED" in critique_text:
            return draft

        # Revise based on critique
        revision = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}\n\n"
                        f"Previous output:\n{draft}\n\n"
                        f"Critique:\n{critique_text}\n\n"
                        "Revise the output to address every critique point. "
                        "Produce the complete revised version."
                    ),
                }
            ],
        )
        draft = extract_text(revision.content)

    return draft
```

**Goal Decomposition with Dependency Tracking**:

```python
@dataclass
class TaskNode:
    id: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed
    result: str | None = None


def build_task_graph(goal: str) -> list[TaskNode]:
    """Decompose a goal into a dependency-aware task graph."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=(
            "Decompose the goal into tasks. For each task, specify an ID, "
            "description, and list of dependency IDs (tasks that must complete "
            "first). Output as JSON array."
        ),
        messages=[{"role": "user", "content": goal}],
    )
    raw_tasks = json.loads(extract_text(response.content))
    return [TaskNode(**t) for t in raw_tasks]


def execute_task_graph(tasks: list[TaskNode]) -> dict[str, str]:
    """Execute tasks respecting dependency order."""
    results = {}
    while any(t.status == "pending" for t in tasks):
        ready = [
            t for t in tasks
            if t.status == "pending"
            and all(
                dep_task.status == "completed"
                for dep_task in tasks
                if dep_task.id in t.dependencies
            )
        ]
        for task in ready:
            task.status = "running"
            context = {d: results[d] for d in task.dependencies if d in results}
            task.result = run_react_agent(
                f"Execute: {task.description}\nContext: {json.dumps(context)}"
            )
            task.status = "completed"
            results[task.id] = task.result

    return results
```
