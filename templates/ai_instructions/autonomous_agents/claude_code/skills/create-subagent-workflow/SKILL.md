---
template_id: SKILL
template_name: Create-Subagent-Workflow - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: create-subagent-workflow
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:

  - skills

  - generic
---
# create-subagent-workflow

---
category: security-quality
priority: MEDIUM
languages: [python, javascript, typescript, all]
requires_user_input: true
estimated_duration: 2-6 hours
---

## Overview

Design and implement multi-agent workflows where Claude Code delegates tasks to specialized sub-agents, coordinates their work, aggregates results, and handles failures gracefully.

## When to Use This Skill

- Complex tasks requiring specialized expertise

- Parallel processing of independent subtasks

- Different context requirements for different operations

- Need for specialized prompts or constraints

- Task decomposition and delegation patterns

- Building agent orchestration systems

## Prerequisites

- Understanding of Claude Code agent architecture

- Familiarity with prompt engineering

- Knowledge of task decomposition

- Error handling and retry patterns

- Understanding of context management

## Step-by-Step Instructions

### Phase 1: Workflow Design

#### Step 1: Identify Agent Specializations

**Common agent specialization patterns:**

```python
"""
Agent Specialization Taxonomy

1. Code Generation Agents

   - Backend API developer

   - Frontend UI developer

   - Database schema designer

   - Test writer

   - Documentation writer

2. Analysis Agents

   - Code reviewer

   - Security auditor

   - Performance analyzer

   - Dependency checker

   - Complexity analyzer

3. Refactoring Agents

   - Legacy code modernizer

   - Pattern implementer

   - Performance optimizer

   - Test coverage improver

4. Infrastructure Agents

   - Docker configuration specialist

   - CI/CD pipeline builder

   - Cloud deployment specialist

   - Monitoring setup agent

5. Domain-Specific Agents

   - Machine learning specialist

   - Web scraping expert

   - Data transformation specialist

   - API integration specialist
"""

class AgentSpecialization:
    """Define agent specializations and capabilities."""

    AGENTS = {
        'code_reviewer': {
            'name': 'Code Review Specialist',
            'expertise': ['code quality', 'best practices', 'bug detection'],
            'prompt_template': """
You are a code review specialist. Review the following code for:

- Code quality and readability

- Potential bugs and edge cases

- Performance issues

- Security vulnerabilities

- Best practice violations

Code to review:
{code}

Provide detailed feedback with specific line numbers and suggestions.
""",
            'max_tokens': 4000
        },

        'test_writer': {
            'name': 'Test Suite Developer',
            'expertise': ['unit testing', 'integration testing', 'test coverage'],
            'prompt_template': """
You are a testing specialist. Write comprehensive tests for:

Code:
{code}

Requirements:

- Unit tests for all functions

- Edge case coverage

- Mock external dependencies

- Clear test names and documentation

- Follow {framework} testing patterns

Framework: {framework}
""",
            'max_tokens': 6000
        },

        'api_designer': {
            'name': 'API Architecture Specialist',
            'expertise': ['REST API design', 'GraphQL', 'API documentation'],
            'prompt_template': """
You are an API design specialist. Design a {api_type} API for:

Requirements:
{requirements}

Provide:

1. Endpoint structure

2. Request/response schemas

3. Error handling

4. Authentication approach

5. OpenAPI specification
""",
            'max_tokens': 5000
        },

        'database_architect': {
            'name': 'Database Schema Designer',
            'expertise': ['database design', 'normalization', 'indexing'],
            'prompt_template': """
You are a database architecture specialist. Design database schema for:

Requirements:
{requirements}

Technology: {database_type}

Provide:

1. Entity-relationship diagram (text format)

2. Table definitions with types

3. Indexes and constraints

4. Migration scripts

5. Performance considerations
""",
            'max_tokens': 5000
        },

        'security_auditor': {
            'name': 'Security Analysis Specialist',
            'expertise': ['security vulnerabilities', 'OWASP', 'penetration testing'],
            'prompt_template': """
You are a security auditing specialist. Analyze this code for vulnerabilities:

Code:
{code}

Check for:

- SQL injection

- XSS vulnerabilities

- Authentication/authorization issues

- Sensitive data exposure

- OWASP Top 10 vulnerabilities

Provide detailed findings with severity levels and remediation steps.
""",
            'max_tokens': 4000
        }
    }

    @classmethod
    def get_agent(cls, agent_type: str) -> dict:
        """Get agent configuration by type."""
        return cls.AGENTS.get(agent_type, {})

    @classmethod
    def list_agents(cls) -> list:
        """List all available agent types."""
        return list(cls.AGENTS.keys())
```

#### Step 2: Design Workflow Architecture

**Workflow pattern examples:**

```python
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

class WorkflowType(Enum):
    """Types of agent workflows."""
    SEQUENTIAL = "sequential"      # Tasks run in order
    PARALLEL = "parallel"          # Tasks run concurrently
    HIERARCHICAL = "hierarchical"  # Coordinator delegates to workers
    PIPELINE = "pipeline"          # Output of one is input to next
    CONDITIONAL = "conditional"    # Branching based on results

@dataclass
class AgentTask:
    """Definition of a task for an agent."""
    agent_type: str
    task_name: str
    inputs: Dict[str, Any]
    dependencies: List[str] = None  # Task names this depends on
    timeout: int = 300  # Seconds
    retry_count: int = 3
    critical: bool = True  # Fail workflow if this fails

@dataclass
class WorkflowDefinition:
    """Definition of a multi-agent workflow."""
    name: str
    description: str
    workflow_type: WorkflowType
    tasks: List[AgentTask]
    final_aggregator: Callable = None

# Example: Sequential workflow for feature development
feature_development_workflow = WorkflowDefinition(
    name="Complete Feature Development",
    description="Develop, test, and document a new feature",
    workflow_type=WorkflowType.SEQUENTIAL,
    tasks=[
        AgentTask(
            agent_type="api_designer",
            task_name="design_api",
            inputs={
                "requirements": "User authentication API with JWT",
                "api_type": "REST"
            }
        ),
        AgentTask(
            agent_type="backend_developer",
            task_name="implement_api",
            inputs={
                "api_spec": "{design_api.result}"  # Reference previous result
            },
            dependencies=["design_api"]
        ),
        AgentTask(
            agent_type="test_writer",
            task_name="write_tests",
            inputs={
                "code": "{implement_api.result}",
                "framework": "pytest"
            },
            dependencies=["implement_api"]
        ),
        AgentTask(
            agent_type="doc_writer",
            task_name="write_docs",
            inputs={
                "code": "{implement_api.result}",
                "api_spec": "{design_api.result}"
            },
            dependencies=["implement_api", "design_api"]
        )
    ]
)

# Example: Parallel workflow for code analysis
code_analysis_workflow = WorkflowDefinition(
    name="Comprehensive Code Analysis",
    description="Run multiple code analysis tasks in parallel",
    workflow_type=WorkflowType.PARALLEL,
    tasks=[
        AgentTask(
            agent_type="code_reviewer",
            task_name="review_quality",
            inputs={"code": "source_code.py"}
        ),
        AgentTask(
            agent_type="security_auditor",
            task_name="security_scan",
            inputs={"code": "source_code.py"}
        ),
        AgentTask(
            agent_type="performance_analyzer",
            task_name="performance_check",
            inputs={"code": "source_code.py"}
        ),
        AgentTask(
            agent_type="complexity_analyzer",
            task_name="complexity_analysis",
            inputs={"code": "source_code.py"}
        )
    ]
)

# Example: Hierarchical workflow with coordinator
microservice_deployment_workflow = WorkflowDefinition(
    name="Microservice Deployment",
    description="Coordinate deployment of microservice with all components",
    workflow_type=WorkflowType.HIERARCHICAL,
    tasks=[
        # Coordinator task
        AgentTask(
            agent_type="deployment_coordinator",
            task_name="plan_deployment",
            inputs={"service_name": "order-service"}
        ),
        # Worker tasks (run after coordinator)
        AgentTask(
            agent_type="docker_specialist",
            task_name="build_container",
            inputs={"dockerfile": "{plan_deployment.dockerfile}"},
            dependencies=["plan_deployment"]
        ),
        AgentTask(
            agent_type="kubernetes_specialist",
            task_name="create_k8s_manifests",
            inputs={"service_spec": "{plan_deployment.spec}"},
            dependencies=["plan_deployment"]
        ),
        AgentTask(
            agent_type="monitoring_specialist",
            task_name="setup_monitoring",
            inputs={"service_name": "{plan_deployment.service_name}"},
            dependencies=["plan_deployment"]
        )
    ]
)
```

### Phase 2: Implementation

#### Step 3: Implement Workflow Executor

```python
# workflow_executor.py
"""
Multi-agent workflow execution engine.
"""
import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime
import json

class WorkflowExecutor:
    """Execute multi-agent workflows with coordination and error handling."""

    def __init__(self):
        self.results = {}
        self.errors = {}
        self.execution_log = []

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_inputs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow based on type.

        Returns:
            Dict containing all task results and execution metadata
        """
        self.log_event("workflow_start", {
            "name": workflow.name,
            "type": workflow.workflow_type.value,
            "task_count": len(workflow.tasks)
        })

        start_time = time.time()

        try:
            if workflow.workflow_type == WorkflowType.SEQUENTIAL:
                result = await self._execute_sequential(workflow, initial_inputs)
            elif workflow.workflow_type == WorkflowType.PARALLEL:
                result = await self._execute_parallel(workflow, initial_inputs)
            elif workflow.workflow_type == WorkflowType.HIERARCHICAL:
                result = await self._execute_hierarchical(workflow, initial_inputs)
            elif workflow.workflow_type == WorkflowType.PIPELINE:
                result = await self._execute_pipeline(workflow, initial_inputs)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")

            execution_time = time.time() - start_time

            # Run final aggregator if provided
            if workflow.final_aggregator:
                result = workflow.final_aggregator(result)

            self.log_event("workflow_complete", {
                "name": workflow.name,
                "execution_time": execution_time,
                "tasks_completed": len(self.results),
                "tasks_failed": len(self.errors)
            })

            return {
                "success": len(self.errors) == 0,
                "results": self.results,
                "errors": self.errors,
                "execution_time": execution_time,
                "execution_log": self.execution_log
            }

        except Exception as e:
            self.log_event("workflow_failed", {
                "name": workflow.name,
                "error": str(e)
            })
            raise

    async def _execute_sequential(
        self,
        workflow: WorkflowDefinition,
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially."""
        for task in workflow.tasks:
            # Resolve input references from previous tasks
            resolved_inputs = self._resolve_inputs(task.inputs, initial_inputs)

            # Execute task
            result = await self._execute_task(task, resolved_inputs)

            # Store result
            self.results[task.task_name] = result

            # Check if critical task failed
            if task.critical and task.task_name in self.errors:
                raise Exception(f"Critical task {task.task_name} failed")

        return self.results

    async def _execute_parallel(
        self,
        workflow: WorkflowDefinition,
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks in parallel."""
        # Create tasks for all parallel executions
        tasks = []
        for task_def in workflow.tasks:
            resolved_inputs = self._resolve_inputs(task_def.inputs, initial_inputs)
            tasks.append(self._execute_task(task_def, resolved_inputs))

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Store results and check for critical failures
        for task_def, result in zip(workflow.tasks, results):
            if isinstance(result, Exception):
                self.errors[task_def.task_name] = str(result)
                if task_def.critical:
                    raise result
            else:
                self.results[task_def.task_name] = result

        return self.results

    async def _execute_hierarchical(
        self,
        workflow: WorkflowDefinition,
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute hierarchical workflow with coordinator and workers."""
        # First, execute coordinator task
        coordinator_task = workflow.tasks[0]
        coordinator_inputs = self._resolve_inputs(
            coordinator_task.inputs,
            initial_inputs
        )
        coordinator_result = await self._execute_task(
            coordinator_task,
            coordinator_inputs
        )
        self.results[coordinator_task.task_name] = coordinator_result

        # Then execute worker tasks in parallel
        worker_tasks = workflow.tasks[1:]
        worker_executions = []

        for task_def in worker_tasks:
            resolved_inputs = self._resolve_inputs(task_def.inputs, initial_inputs)
            worker_executions.append(self._execute_task(task_def, resolved_inputs))

        # Wait for all workers
        results = await asyncio.gather(*worker_executions, return_exceptions=True)

        # Store worker results
        for task_def, result in zip(worker_tasks, results):
            if isinstance(result, Exception):
                self.errors[task_def.task_name] = str(result)
            else:
                self.results[task_def.task_name] = result

        return self.results

    async def _execute_pipeline(
        self,
        workflow: WorkflowDefinition,
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute pipeline where output of each stage is input to next."""
        current_input = initial_inputs

        for task in workflow.tasks:
            # Use output from previous task as input
            resolved_inputs = self._resolve_inputs(task.inputs, current_input)

            # Execute task
            result = await self._execute_task(task, resolved_inputs)

            # Store result
            self.results[task.task_name] = result

            # Pass result to next stage
            current_input = result

            if task.critical and task.task_name in self.errors:
                raise Exception(f"Critical pipeline stage {task.task_name} failed")

        return self.results

    async def _execute_task(
        self,
        task: AgentTask,
        inputs: Dict[str, Any]
    ) -> Any:
        """
        Execute single agent task with retry logic.

        This is where you would integrate with actual Claude Code agent execution.
        """
        self.log_event("task_start", {
            "task_name": task.task_name,
            "agent_type": task.agent_type
        })

        for attempt in range(task.retry_count):
            try:
                # Get agent configuration
                agent_config = AgentSpecialization.get_agent(task.agent_type)

                if not agent_config:
                    raise ValueError(f"Unknown agent type: {task.agent_type}")

                # Format prompt with inputs
                prompt = agent_config['prompt_template'].format(**inputs)

                # Execute agent (simulated here - replace with actual Claude Code invocation)
                result = await self._invoke_agent(
                    prompt=prompt,
                    max_tokens=agent_config['max_tokens'],
                    timeout=task.timeout
                )

                self.log_event("task_complete", {
                    "task_name": task.task_name,
                    "attempt": attempt + 1
                })

                return result

            except Exception as e:
                self.log_event("task_error", {
                    "task_name": task.task_name,
                    "attempt": attempt + 1,
                    "error": str(e)
                })

                if attempt == task.retry_count - 1:
                    # Final attempt failed
                    self.errors[task.task_name] = str(e)
                    if task.critical:
                        raise
                    return None

                # Wait before retry (exponential backoff)
                await asyncio.sleep(2 ** attempt)

    async def _invoke_agent(
        self,
        prompt: str,
        max_tokens: int,
        timeout: int
    ) -> str:
        """
        Invoke Claude Code agent with prompt.

        IMPLEMENTATION NOTE:
        In actual usage, this would invoke Claude Code's agent API.
        For now, this is a placeholder that simulates agent execution.
        """
        # Simulate agent execution time
        await asyncio.sleep(1)

        # In production, this would be:
        # result = await claude_code_agent.execute(
        #     prompt=prompt,
        #     max_tokens=max_tokens,
        #     timeout=timeout
        # )

        return f"[Agent response to: {prompt[:50]}...]"

    def _resolve_inputs(
        self,
        inputs: Dict[str, Any],
        additional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve input references to previous task results.

        References format: {task_name.result} or {task_name.field}
        """
        resolved = {}

        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                # Extract reference
                ref = value[1:-1]

                if '.' in ref:
                    # Reference to specific field: {task_name.field}
                    task_name, field = ref.split('.', 1)

                    if task_name in self.results:
                        result = self.results[task_name]
                        if isinstance(result, dict):
                            resolved[key] = result.get(field)
                        else:
                            resolved[key] = result
                    else:
                        # Task not executed yet - leave unresolved
                        resolved[key] = value
                else:
                    # Reference to entire result: {task_name}
                    resolved[key] = self.results.get(ref, value)
            else:
                resolved[key] = value

        # Add additional context
        resolved.update(additional_context or {})

        return resolved

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log execution event."""
        self.execution_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        })

    def generate_report(self, output_file: str = "workflow_report.json"):
        """Generate execution report."""
        report = {
            "results": self.results,
            "errors": self.errors,
            "execution_log": self.execution_log,
            "summary": {
                "total_tasks": len(self.results) + len(self.errors),
                "successful_tasks": len(self.results),
                "failed_tasks": len(self.errors),
                "success_rate": len(self.results) / (len(self.results) + len(self.errors))
                    if (len(self.results) + len(self.errors)) > 0 else 0
            }
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Workflow report saved to {output_file}")
        return report

# Example usage
async def main():
    """Example workflow execution."""
    # Create workflow
    workflow = code_analysis_workflow

    # Execute workflow
    executor = WorkflowExecutor()
    result = await executor.execute_workflow(
        workflow,
        initial_inputs={"source_code": "def example(): pass"}
    )

    # Generate report
    executor.generate_report()

    # Print summary
    print(f"\nWorkflow Results:")
    print(f"  Success: {result['success']}")
    print(f"  Tasks completed: {len(result['results'])}")
    print(f"  Tasks failed: {len(result['errors'])}")
    print(f"  Execution time: {result['execution_time']:.2f}s")

if __name__ == '__main__':
    asyncio.run(main())
```

### Phase 3: Error Handling and Recovery

#### Step 4: Implement Robust Error Handling

```python
# error_handling.py
"""
Error handling and recovery strategies for multi-agent workflows.
"""
from enum import Enum
from typing import Any, Callable

class RecoveryStrategy(Enum):
    """Error recovery strategies."""
    RETRY = "retry"                    # Retry failed task
    FALLBACK = "fallback"              # Use alternative agent
    SKIP = "skip"                      # Skip task, continue workflow
    COMPENSATE = "compensate"          # Run compensating action
    FAIL_WORKFLOW = "fail_workflow"    # Stop entire workflow

class ErrorHandler:
    """Handle errors in multi-agent workflows."""

    def __init__(self):
        self.recovery_strategies = {}
        self.compensating_actions = {}

    def register_strategy(
        self,
        task_name: str,
        strategy: RecoveryStrategy,
        fallback_agent: str = None,
        compensating_action: Callable = None
    ):
        """Register error recovery strategy for task."""
        self.recovery_strategies[task_name] = {
            'strategy': strategy,
            'fallback_agent': fallback_agent,
            'compensating_action': compensating_action
        }

    async def handle_error(
        self,
        task: AgentTask,
        error: Exception,
        workflow_context: Dict[str, Any]
    ) -> Any:
        """Handle task error according to registered strategy."""
        strategy_config = self.recovery_strategies.get(task.task_name, {})
        strategy = strategy_config.get('strategy', RecoveryStrategy.FAIL_WORKFLOW)

        if strategy == RecoveryStrategy.RETRY:
            # Already handled by task retry logic
            return None

        elif strategy == RecoveryStrategy.FALLBACK:
            # Try alternative agent
            fallback_agent = strategy_config.get('fallback_agent')
            if fallback_agent:
                print(f"Trying fallback agent: {fallback_agent}")
                # Execute with fallback agent
                fallback_task = AgentTask(
                    agent_type=fallback_agent,
                    task_name=f"{task.task_name}_fallback",
                    inputs=task.inputs
                )
                return await self._execute_task(fallback_task, task.inputs)

        elif strategy == RecoveryStrategy.SKIP:
            # Skip task and continue
            print(f"Skipping failed task: {task.task_name}")
            return None

        elif strategy == RecoveryStrategy.COMPENSATE:
            # Run compensating action
            compensate = strategy_config.get('compensating_action')
            if compensate:
                await compensate(workflow_context)

        elif strategy == RecoveryStrategy.FAIL_WORKFLOW:
            # Propagate error to fail workflow
            raise error

        return None

# Example: Workflow with error handling
workflow_with_recovery = WorkflowDefinition(
    name="Robust Feature Development",
    description="Feature development with error recovery",
    workflow_type=WorkflowType.SEQUENTIAL,
    tasks=[
        AgentTask(
            agent_type="api_designer",
            task_name="design_api",
            inputs={"requirements": "User auth API"},
            # If this fails, try simplified approach
        ),
        AgentTask(
            agent_type="backend_developer",
            task_name="implement_api",
            inputs={"api_spec": "{design_api.result}"},
            dependencies=["design_api"],
            critical=True  # Must succeed
        ),
        AgentTask(
            agent_type="test_writer",
            task_name="write_tests",
            inputs={"code": "{implement_api.result}"},
            dependencies=["implement_api"],
            critical=False  # Can skip if fails
        )
    ]
)

# Register recovery strategies
error_handler = ErrorHandler()

error_handler.register_strategy(
    "design_api",
    RecoveryStrategy.FALLBACK,
    fallback_agent="simple_api_designer"
)

error_handler.register_strategy(
    "write_tests",
    RecoveryStrategy.SKIP  # Continue without tests if this fails
)
```

### Phase 4: Monitoring and Optimization

#### Step 5: Add Workflow Monitoring

```python
# workflow_monitor.py
"""
Monitor and analyze multi-agent workflow performance.
"""
import time
from collections import defaultdict
from typing import Dict, List

class WorkflowMonitor:
    """Monitor workflow execution metrics."""

    def __init__(self):
        self.metrics = defaultdict(list)
        self.task_durations = {}
        self.agent_performance = defaultdict(lambda: {'success': 0, 'failure': 0})

    def record_task_start(self, task_name: str, agent_type: str):
        """Record task start time."""
        self.metrics[task_name].append({
            'start_time': time.time(),
            'agent_type': agent_type
        })

    def record_task_complete(
        self,
        task_name: str,
        agent_type: str,
        success: bool
    ):
        """Record task completion."""
        if task_name in self.metrics and self.metrics[task_name]:
            start_time = self.metrics[task_name][-1]['start_time']
            duration = time.time() - start_time
            self.task_durations[task_name] = duration

            # Update agent performance
            if success:
                self.agent_performance[agent_type]['success'] += 1
            else:
                self.agent_performance[agent_type]['failure'] += 1

    def generate_performance_report(self) -> Dict:
        """Generate performance analysis report."""
        return {
            'task_durations': self.task_durations,
            'average_task_duration': sum(self.task_durations.values()) / len(self.task_durations)
                if self.task_durations else 0,
            'slowest_tasks': sorted(
                self.task_durations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'agent_performance': dict(self.agent_performance),
            'total_tasks': sum(
                perf['success'] + perf['failure']
                for perf in self.agent_performance.values()
            )
        }

    def print_summary(self):
        """Print performance summary."""
        report = self.generate_performance_report()

        print("\n" + "="*60)
        print("WORKFLOW PERFORMANCE REPORT")
        print("="*60)
        print(f"\nTotal tasks: {report['total_tasks']}")
        print(f"Average duration: {report['average_task_duration']:.2f}s")

        print("\nSlowest tasks:")
        for task_name, duration in report['slowest_tasks']:
            print(f"  {task_name}: {duration:.2f}s")

        print("\nAgent performance:")
        for agent, perf in report['agent_performance'].items():
            total = perf['success'] + perf['failure']
            success_rate = (perf['success'] / total * 100) if total > 0 else 0
            print(f"  {agent}:")
            print(f"    Success: {perf['success']}/{total} ({success_rate:.1f}%)")
```

## Expected Outcomes

After implementing this workflow:

1. **Coordinated multi-agent system**

   - Tasks delegated to specialized agents

   - Results aggregated effectively

   - Dependencies managed correctly

2. **Robust error handling**

   - Failures handled gracefully

   - Recovery strategies applied

   - Workflows don't fail catastrophically

3. **Performance optimized**

   - Parallel execution where possible

   - Bottlenecks identified and resolved

   - Resource utilization efficient

4. **Maintainable architecture**

   - Clear agent responsibilities

   - Reusable workflow patterns

   - Easy to extend and modify

## Success Criteria

- [ ] Agent specializations clearly defined

- [ ] Workflow types implemented (sequential, parallel, hierarchical)

- [ ] Task dependencies resolved correctly

- [ ] Error handling and retry logic working

- [ ] Parallel execution functioning

- [ ] Result aggregation successful

- [ ] Monitoring and logging in place

- [ ] Performance acceptable

## Common Pitfalls

1. **Over-specialization**

   - Don't create too many specialized agents

   - Balance specialization with maintainability

2. **Dependency hell**

   - Keep dependencies simple

   - Avoid circular dependencies

3. **Context explosion**

   - Be mindful of token limits

   - Use context management strategies

4. **Poor error handling**

   - Always handle agent failures

   - Provide fallback strategies

## Related Skills

- **optimize-context-usage**: Manage token usage efficiently

- **refactor-for-testability**: Make code testable

- **setup-python-project**: Project structure

## Additional Resources

### Patterns
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)

- [Orchestration vs Choreography](https://www.thoughtworks.com/insights/blog/microservices/orchestration-vs-choreography)

### Tools
- [Apache Airflow](https://airflow.apache.org/) - Workflow orchestration

- [Temporal](https://temporal.io/) - Durable execution

- [Prefect](https://www.prefect.io/) - Workflow management

---

**Note**: This skill demonstrates patterns for multi-agent coordination. Actual implementation will depend on your specific Claude Code integration and requirements.
