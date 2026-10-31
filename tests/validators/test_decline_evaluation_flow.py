"""A fresh result flows only within its current evaluation; nothing is cached."""

import hashlib

import pytest

from .test_conditional_decline import decline as decline
import check_plan_completion as ck
import completion_minor as cm


def ready(decline):
    ctx, view = decline.ctx, decline.view
    receipt = ck.conditional_request(ctx, view, decline.request)
    receipt["capture"] = {"origin": "native-answer"}
    view.update(
        scope="member",
        minor="v0.2",
        version=ctx.version,
        plan_path=ctx.rel,
        nonce="test-nonce",
    )
    view["approvals"]["conditional_outcome"] = receipt
    return ctx, view


def token(ctx, view):
    return (
        ctx,
        hashlib.sha256(
            ck._canonical(view["approvals"]["conditional_outcome"])
        ).hexdigest(),
        view["nonce"],
        view["plan_sha256"],
    )


def test_each_evaluation_refreshes_then_passes_its_own_result(decline, monkeypatch):
    ctx, view = ready(decline)
    original = ck.conditional_status
    calls, proofs = [], []

    def fresh(*a):
        calls.append(True)
        return original(*a)

    def gaps(context, record, proof=None):
        proofs.append(proof)
        state, anchor = cm.completion_anchor(
            ck, context, record, record, _decline_evaluation=proof
        )
        assert state == "met" and anchor == decline.request["merge"]
        return "met", 0

    monkeypatch.setattr(ck, "conditional_status", fresh)
    monkeypatch.setattr(ck, "_gaps_status", gaps)
    for _ in range(2):
        ctx.budget = ck.Budget(20)
        ck.evaluate(ctx, view)
    assert len(calls) == 2 and len(proofs) == 2
    assert proofs[0] is not proofs[1]
    assert not hasattr(ctx, "_decline_evaluation") and "_decline_evaluation" not in view


@pytest.mark.parametrize(
    "change", ["context", "nonce", "plan", "receipt", "expired", "member"]
)
def test_context_scoped_proof_rejects_substitution(decline, monkeypatch, change):
    ctx, view = ready(decline)
    proof = token(ctx, view)
    if change == "context":
        proof = (object(), *proof[1:])
    elif change == "nonce":
        proof = (*proof[:2], "different", proof[3])
    elif change == "plan":
        proof = (*proof[:3], "0" * 64)
    elif change == "receipt":
        view["approvals"]["conditional_outcome"]["request"]["merge"] = "0" * 40
    elif change == "expired":
        ctx.budget = ck.Budget(-1)
    else:
        view["version"] = "v0.2.1"
    monkeypatch.setattr(
        ck,
        "conditional_status",
        lambda *a: pytest.fail("invalid proof must not trigger a fallback grant"),
    )
    assert cm.completion_anchor(ck, ctx, view, view, _decline_evaluation=proof) == (
        "cannot-verify",
        None,
    )


def test_no_token_uses_fresh_verification_each_time(decline, monkeypatch):
    ctx, view = ready(decline)
    original = ck.conditional_status
    calls = []

    def fresh(*a):
        calls.append(True)
        return original(*a)

    monkeypatch.setattr(ck, "conditional_status", fresh)
    for _ in range(2):
        ctx.budget = ck.Budget(20)
        assert cm.completion_anchor(ck, ctx, view, view)[0] == "met"
    assert len(calls) == 2
