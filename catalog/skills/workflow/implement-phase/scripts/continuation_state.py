#!/usr/bin/env python3
"""Reconcile implementation observations without executing work or granting authority.

Callers own genuine reply, authorization and process verification. This module
projects their observations into one disposition; it never validates a signature,
changes a native goal, consumes consent or runs a command from supplied text.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from urllib.parse import urlsplit

STATES = ("working", "waiting_owner_action", "waiting_decision", "waiting_job",
          "blocked_external", "paused", "verified_complete")
ACTIVE_JOBS = {"running", "pending", "observation-timeout"}
TERMINAL_JOBS = {"succeeded", "failed"}


def _string(row: dict, key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"continuation requires nonempty {key}")
    return value


def _items(row: dict, key: str) -> list[dict]:
    value = row.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"continuation {key} must be a list of objects")
    return copy.deepcopy(value)


def _strings(row: dict, key: str) -> None:
    value = row.get(key)
    if not isinstance(value, list) or not value or any(not isinstance(s, str) or not s.strip() for s in value):
        raise ValueError(f"continuation requires nonempty {key} steps")


def _time(row: dict, key: str = "observed_at") -> None:
    value = datetime.fromisoformat(_string(row, key).replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError(f"continuation {key} requires a timezone")


def _request(row: dict) -> None:
    _string(row, "id")
    _string(row, "title")
    kind = row.get("kind")
    if kind == "action":
        _strings(row, "prerequisites")
        _strings(row, "steps")
        _string(row, "expected_result")
        _string(row, "acknowledgment")
    elif kind == "decision":
        options = _items(row, "options")
        if len(options) < 2:
            raise ValueError("continuation decision requires at least two options")
        for option in options:
            _string(option, "option")
            _string(option, "effect")
        _string(row, "reply")
        if row.get('manual_capture') is True:
            _strings(row, 'prerequisites')
            _strings(row, 'steps')
            _string(row, 'expected_result')
            _string(row, 'acknowledgment')
    elif kind != "question":
        raise ValueError("continuation request kind must be action, decision or question")
    if 'native_reconciliation' in row:
        metadata = row['native_reconciliation']
        native_round = row.get('native_round')
        if (not isinstance(native_round, dict) or not isinstance(native_round.get('key'), str)
                or not isinstance(native_round.get('nonce'), str)
                or row['id'] not in {'native:' + native_round['key'] + ':' + native_round['nonce'],
                                    'native:' + native_round['key'] + ':' + native_round['nonce'] + ':decision'}):
            raise ValueError('controller reconciliation requires an exact native request identity')
        if not isinstance(metadata, dict):
            raise ValueError('native reconciliation requires verified owner provenance')
        for field in ('outcome', 'reason', 'evidence', 'resume_when', 'provenance_sha256'):
            _string(metadata, field)
        if len(metadata['provenance_sha256']) != 64 or any(char not in '0123456789abcdef' for char in metadata['provenance_sha256']):
            raise ValueError('native reconciliation requires an exact provenance digest')


def _job(row: dict) -> None:
    for key in ("id", "name", "status", "resume_when", "evidence"):
        _string(row, key)
    _time(row)
    if not row.get("handle") and not row.get("url"):
        raise ValueError("continuation job requires an exact handle or URL")
    if row.get("handle") is not None:
        _string(row, "handle")
    if row.get("url") is not None:
        value = _string(row, "url")
        parsed = urlsplit(value)
        if (parsed.scheme not in {"https", "http"} or not parsed.hostname
                or parsed.username or parsed.password or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)):
            raise ValueError("continuation job URL requires HTTP(S), a host and no credentials")
    if row["status"] not in ACTIVE_JOBS | TERMINAL_JOBS:
        raise ValueError("continuation job has an unsupported observed status")
    if row["status"] in TERMINAL_JOBS and row.get("result_verified") is not True:
        raise ValueError("continuation terminal job requires a verified result")


def _merge(current: list[dict], previous: list[dict]) -> dict[str, dict]:
    if not isinstance(previous, list) or any(not isinstance(item, dict) for item in previous):
        raise ValueError("previous continuation items must be a list of objects")
    merged = {_string(item, "id"): copy.deepcopy(item) for item in previous}
    if len(merged) != len(previous):
        raise ValueError("previous continuation item ids must be unique")
    ids = [_string(item, "id") for item in current]
    if len(set(ids)) != len(ids):
        raise ValueError("continuation item ids must be unique")
    merged.update(zip(ids, current))
    return merged


def semantic_fingerprint(value: dict) -> str:
    """Observation time and elapsed time never establish material progress."""
    def stable(item):
        if isinstance(item, dict):
            return {key: stable({field: value for field, value in child.items() if field not in {"observed_at", "updated_at", "sha256"}
                        and not (field == "terminal_diagnostic" and child.get("status") == "failed" and child.get("first_failure_sha256"))})
                    if key == "provider_observation" and isinstance(child, dict) else stable(child)
                    for key, child in item.items()
                    if key not in {"observed_at", "elapsed", "fingerprint", "material_change", "observation_attempted_at", "provider_observation_hmac"}}
        if isinstance(item, list):
            return [stable(child) for child in item]
        return item
    return hashlib.sha256(json.dumps(stable(value), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reconcile(observation: dict, previous: dict | None = None) -> dict:
    """Return the required continue/wait/complete disposition from verified observations.

    A verified resolution is descriptive proof supplied by the owning controller,
    not a report overlay's authority to consume native approval or signed state.
    Previous unresolved requests and jobs cannot disappear by omission.
    """
    if not isinstance(observation, dict) or (previous is not None and not isinstance(previous, dict)):
        raise ValueError("continuation observation and previous state must be objects")
    previous = previous or {}
    objective = _string(observation, "objective")
    objective_complete = observation.get('objective_complete', previous.get('objective_complete', True))
    if type(objective_complete) is not bool:
        raise ValueError('objective completeness must be a boolean')
    if previous and previous.get('objective_complete', True) and objective_complete is False:
        raise ValueError('continuation must preserve the complete approved objective; completeness cannot be demoted')
    if (previous.get("objective", objective) != objective
            and not (previous.get('objective_complete') is False and objective_complete)):
        raise ValueError("continuation must preserve the complete approved objective")
    remaining = observation.get("remaining_tasks")
    if type(remaining) is not int or remaining < 0:
        raise ValueError("continuation remaining_tasks must be a nonnegative integer")
    paused = observation.get("paused", previous.get("paused", False))
    if type(paused) is not bool:
        raise ValueError("continuation paused must be a boolean")
    work = _items(observation, "work")
    for item in work:
        for key in ("id", "title", "evidence"):
            _string(item, key)
        if type(item.get("authorized")) is not bool or type(item.get("feasible")) is not bool:
            raise ValueError("continuation work needs explicit authorized and feasible observations")
    requests = _merge(_items(observation, "requests"), previous.get("requests", []))
    native = copy.deepcopy(observation.get("native_goal", previous.get("native_goal", {})))
    native_condition = None
    if not isinstance(native, dict):
        raise ValueError("continuation native_goal must be an object")
    if native:
        _string(native, "status")
        _time(native)
        if "resume_action" in native and not isinstance(native["resume_action"], dict):
            raise ValueError("native resume_action must be an owner-action object")
        if native["status"] in {"blocked", "stalled"} and native.get("resume_supported") is not True:
            action = native.get("resume_action")
            if isinstance(action, dict):
                _request(action)
                if action["kind"] != "action":
                    raise ValueError("native resume_action must be an owner action, not approval")
                requests[action["id"]] = copy.deepcopy(action)
            elif isinstance(native.get("external_condition"), dict):
                native_condition = copy.deepcopy(native["external_condition"])
            else:
                raise ValueError("unsupported native goal resume requires an explicit resume_action or evidenced external_condition")
    for item in requests.values():
        _request(item)
    resolved = _items(previous, "resolved_requests")
    prior_resolved = {_string(item, "request_id"): item for item in resolved}
    if any(item["id"] in prior_resolved for item in _items(observation, "requests")):
        raise ValueError("a fulfilled request id cannot be reused for a new request")
    for resolution in _items(observation, "resolutions"):
        request_id = _string(resolution, "request_id")
        if resolution.get("verified") is not True:
            continue
        _string(resolution, "evidence")
        request = requests.get(request_id)
        if request is None:
            if resolution == prior_resolved.get(request_id):
                continue
            raise ValueError("continuation resolution must refer to a pending request")
        if native.get("status") in {"blocked", "stalled"} and request_id == native.get("resume_action", {}).get("id"):
            # Acknowledgment is not proof that the host actually changed its goal.
            continue
        if request["kind"] == "decision":
            _string(resolution, "authority_receipt")
        requests.pop(request_id)
        resolved.append(resolution)
    current_jobs = _items(observation, "jobs")
    jobs = _merge(current_jobs, previous.get("jobs", []))
    old_jobs = {job["id"]: job for job in previous.get("jobs", [])}
    completed_jobs = _items(previous, "completed_jobs")
    completed_ids = {_string(item, "id") for item in completed_jobs}
    for job in list(jobs.values()):
        _job(job)
        old = old_jobs.get(job["id"])
        if old and (job.get("handle"), job.get("url")) != (old.get("handle"), old.get("url")):
            raise ValueError("continuation must retain the existing job handle and URL")
        if job["status"] in TERMINAL_JOBS:
            if job["id"] not in completed_ids:
                completed_jobs.append(job)
            jobs.pop(job["id"])
        elif job["id"] in completed_ids:
            raise ValueError("a completed job id cannot be reused for another process")
    conditions = _merge(_items(observation, "external_conditions"), previous.get("external_conditions", []))
    if native_condition is not None:
        conditions[_string(native_condition, "id")] = native_condition
    for condition in conditions.values():
        for key in ("id", "title", "evidence", "resume_when"):
            _string(condition, key)
        _time(condition)
    for resolution in _items(observation, "condition_resolutions"):
        if resolution.get("verified") is True:
            _string(resolution, "evidence")
            if conditions.pop(_string(resolution, "condition_id"), None) is None:
                raise ValueError("continuation resolution must refer to an external condition")
    completion = observation.get("completion", {})
    if not isinstance(completion, dict):
        raise ValueError("continuation completion must be an object")
    if paused:
        state, reason = "paused", "Explicitly paused by the owner"
    elif completion.get("verified") is True:
        if objective_complete is False:
            raise ValueError("verified native scope does not establish the complete approved objective")
        if remaining != 0:
            raise ValueError("verified completion contradicts remaining tasks")
        if requests or jobs or conditions:
            raise ValueError("verified completion cannot conceal unresolved requests, jobs or conditions")
        state, reason = "verified_complete", _string(completion, "evidence")
    elif any(item["authorized"] and item["feasible"] for item in work):
        state = "working"
        reason = next(item["title"] for item in work if item["authorized"] and item["feasible"])
    elif any(item["kind"] == "action" and not item.get("native_reconciliation") for item in requests.values()):
        state = "waiting_owner_action"
        reason = next(item["title"] for item in requests.values() if item["kind"] == "action" and not item.get("native_reconciliation"))
    elif any(item["kind"] == "decision" and not item.get('native_reconciliation') for item in requests.values()):
        state, reason = "waiting_decision", next(item['title'] for item in requests.values() if item["kind"] == "decision" and not item.get('native_reconciliation'))
    elif jobs:
        state, reason = "waiting_job", next(iter(jobs.values()))["name"]
    elif conditions:
        state, reason = "blocked_external", next(iter(conditions.values()))["title"]
    elif any(item["kind"] == "question" and not item.get("native_reconciliation") for item in requests.values()):
        state = "waiting_owner_action"
        reason = next(item["title"] for item in requests.values() if item["kind"] == "question" and not item.get("native_reconciliation"))
    else:
        if remaining == 0:
            raise ValueError("task marks alone do not establish verified completion; supply completion evidence or the remaining obligation")
        raise ValueError("unfinished implementation requires feasible authorized work or an evidenced waiting condition")
    result = {"objective": objective, "remaining_tasks": remaining, "paused": paused,
              "state": state, "directive": "continue" if state == "working" else "complete" if state == "verified_complete" else "wait",
              "reason": reason, "work": work, "requests": list(requests.values()), "jobs": list(jobs.values()),
              "external_conditions": list(conditions.values()), "native_goal": native,
              "resolved_requests": resolved, "completed_jobs": completed_jobs, "completion": completion}
    if objective_complete is False:
        result['objective_complete'] = False
        result['objective_source'] = _string(observation, 'objective_source')
    result["fingerprint"] = semantic_fingerprint(result)
    result["material_change"] = result["fingerprint"] != previous.get("fingerprint")
    return result
