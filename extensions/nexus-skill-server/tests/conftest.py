from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add src to path so nexus_skill_server is importable without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

SAMPLE_SKILLS = [
    {
        "name": "code-review-security",
        "title": "Code Review Security",
        "description": "Security-focused code review checklist",
        "long_description": "A comprehensive security review process.",
        "summary_l0": "Perform security-focused code review with OWASP-aligned checks",
        "overview_l1": "This skill guides a thorough security review of code changes. Use when reviewing PRs for security issues, conducting pre-merge audits, or checking for OWASP Top 10 vulnerabilities. Produces a structured report with severity ratings and remediation guidance. Trigger phrases: security review, vulnerability check, secure code review.",
        "category": "Code Review",
        "language": "Multi-language",
        "tags": ["security", "code-review", "owasp", "vulnerability"],
        "priority": "HIGH",
        "tools_required": ["Read", "Grep", "Glob"],
        "path": "catalog/skills/code-review/code-review-security/",
        "file": "catalog/skills/code-review/code-review-security/SKILL.md",
        "size": {"lines": 450, "characters": 18000, "tokens_estimate": 3600},
    },
    {
        "name": "ai-agent-development",
        "title": "AI Agent Development",
        "description": "Build autonomous AI agents with tool use and memory",
        "long_description": "End-to-end guide for building AI agents.",
        "summary_l0": "Build autonomous AI agents with tool use, memory, and multi-agent orchestration",
        "overview_l1": "This skill provides patterns for building AI agents using ReAct, Plan-and-Execute, and multi-agent architectures. Use when creating agents with tool use, implementing memory systems, or orchestrating multiple agents. Produces working agent code with evaluation harnesses. Trigger phrases: build agent, agent development, tool use, multi-agent.",
        "category": "AI Development",
        "language": "Python",
        "tags": ["ai", "agents", "tool-use", "memory", "orchestration"],
        "priority": "CRITICAL",
        "tools_required": ["Read", "Write", "Bash"],
        "path": "catalog/skills/ai-development/ai-agent-development/",
        "file": "catalog/skills/ai-development/ai-agent-development/SKILL.md",
        "size": {"lines": 999, "characters": 35382, "tokens_estimate": 7076},
    },
    {
        "name": "kubernetes-ops",
        "title": "Kubernetes Operations",
        "description": "Manage Kubernetes clusters and workloads",
        "long_description": "Production Kubernetes operations guide.",
        "summary_l0": "Manage Kubernetes clusters, deployments, and troubleshooting",
        "overview_l1": "This skill covers Kubernetes operations including deployment management, scaling, networking, and troubleshooting. Use when deploying to K8s, debugging pod issues, or configuring ingress and services. Trigger phrases: kubernetes, k8s, pod, deployment, kubectl.",
        "category": "Infrastructure",
        "language": "Multi-language",
        "tags": ["kubernetes", "k8s", "devops", "infrastructure", "containers"],
        "priority": "HIGH",
        "tools_required": ["Bash", "Read"],
        "path": "catalog/skills/infrastructure/kubernetes-ops/",
        "file": "catalog/skills/infrastructure/kubernetes-ops/SKILL.md",
        "size": {"lines": 600, "characters": 24000, "tokens_estimate": 4800},
    },
]

SAMPLE_BUNDLES = {
    "metadata": {"version": "1.0.0"},
    "bundles": [
        {
            "id": "core-developer",
            "name": "Core Developer",
            "description": "Essential skills for every developer",
            "skills": ["code-review-security", "ai-agent-development"],
        },
        {
            "id": "devops-engineer",
            "name": "DevOps Engineer",
            "description": "Infrastructure and deployment skills",
            "skills": ["kubernetes-ops"],
        },
    ],
}


@pytest.fixture
def sample_skills_json(tmp_path: Path) -> Path:
    """Create a temporary skills.json with sample data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    skills_json = data_dir / "skills.json"
    skills_json.write_text(json.dumps({
        "metadata": {"version": "test-1.0"},
        "statistics": {"total_skills": len(SAMPLE_SKILLS)},
        "skills": SAMPLE_SKILLS,
    }), encoding="utf-8")

    bundles_json = data_dir / "bundles.json"
    bundles_json.write_text(json.dumps(SAMPLE_BUNDLES), encoding="utf-8")

    return tmp_path


@pytest.fixture
def sample_skills_with_content(sample_skills_json: Path) -> Path:
    """Create sample skills.json plus actual SKILL.md files on disk."""
    for skill in SAMPLE_SKILLS:
        skill_dir = sample_skills_json / skill["path"]
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = sample_skills_json / skill["file"]
        skill_file.write_text(f"---\nname: {skill['name']}\ndescription: {skill['description']}\n---\n\n# {skill['title']}\n\nFull content for {skill['name']}.\n", encoding="utf-8")

    return sample_skills_json
