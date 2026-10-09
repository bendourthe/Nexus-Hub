"""The guide's Cheatsheets `/implement` card follows `catalog/commands/implement.md` (v4.13.6 T059).

v4.13.2 made `/implement <plan>` run the whole plan, but the card kept saying
"Implement one plan phase" for two releases because nothing compared the two. This
test parses the "Argument resolution" bullets of the command file and asserts that
every invocation form and every mode token they list appears on the card, so a new
mode or scope in the command file fails here until the card teaches it.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMAND = ROOT / "catalog" / "commands" / "implement.md"
GUIDE = ROOT / "guides" / "website" / "nexus-hub-guide.html"
# A second code span in a bullet introduced this way is another accepted spelling of that mode.
ALIAS = re.compile(r"(?:\band|\balso)\s+`([^`]+)`")


def _bullets() -> list[str]:
    text = COMMAND.read_text(encoding="utf-8")
    section = text.split("## Argument resolution\n", 1)[1].split("\n## ", 1)[0]
    bullets = [line[2:] for line in section.splitlines() if line.startswith("- `/implement")]
    assert len(bullets) >= 8, "the Argument resolution list changed shape; update this parser"
    return bullets


def forms() -> list[str]:
    """Each bullet's invocation without the command name: `<plan>`, `vX.Y`, `(bare)`, `<plan> phase <N>`..."""
    found = []
    for bullet in _bullets():
        invocation = bullet.split("`", 2)[1]
        rest = invocation.removeprefix("/implement").strip()
        found.append(rest or "(bare)")
    return found


def mode_tokens() -> set[str]:
    """Literal words of every form (placeholders excluded) plus each bullet's named aliases."""
    tokens = {word for form in forms() for word in form.split() if not word.startswith("<") and word != "(bare)"}
    for bullet in _bullets():
        tokens.update(alias for alias in ALIAS.findall(bullet) if not alias.startswith('"'))
    return tokens


def _card() -> tuple[list[str], str]:
    text = GUIDE.read_text(encoding="utf-8").split('id="page-cheatsheets"', 1)[1]
    match = re.search(r'class="cs-name">/implement</span>([\s\S]*?)</article>', text)
    assert match, "the Cheatsheets page has no /implement card"
    body = match.group(1)
    scopes = [html.unescape(s).strip() for s in re.findall(r'<div class="cs-scope"><code[^>]*>([^<]+)</code>', body)]
    visible = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return scopes, visible


def test_the_parser_reads_the_expected_modes() -> None:
    """Guards the parser itself: if it silently read nothing, every card would pass."""
    assert {"vX.Y", "(bare)", "<plan>", "pause"} <= set(forms())
    assert {"phase", "next", "phase-by-phase", "full", "in-full", "pause", "vX.Y"} <= mode_tokens()


@pytest.mark.parametrize("form", forms())
def test_every_scope_form_is_a_card_scope(form: str) -> None:
    scopes, _ = _card()
    assert form in scopes, f"/implement {form} is in implement.md but not on the Cheatsheets card: {scopes}"


@pytest.mark.parametrize("token", sorted(mode_tokens()))
def test_every_mode_token_appears_on_the_card(token: str) -> None:
    _, visible = _card()
    assert re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", visible), f"mode token {token!r} missing"


def test_the_card_no_longer_teaches_one_phase_as_the_default() -> None:
    _, visible = _card()
    assert "Implement one plan phase" not in visible
    assert "ask which phase to run" not in visible
    assert "whole plan by default" in visible
    assert "every queued plan in that minor" in visible
    assert "approval paste starts the run" in visible and "native goal" in visible


def test_the_card_shows_a_minor_and_a_per_plan_example() -> None:
    body = GUIDE.read_text(encoding="utf-8").split('class="cs-name">/implement</span>', 1)[1].split("</article>", 1)[0]
    copies = re.findall(r'data-copy="(/implement[^"]*)"', body)
    assert copies[0] == "/implement v0.5"
    assert any(re.fullmatch(r"/implement [a-z0-9-]+", c) and c != "/implement v0.5" for c in copies[1:])


def test_the_update_card_names_the_closing_pull_request_and_the_checked_cleanup() -> None:
    text = GUIDE.read_text(encoding="utf-8").split('id="page-cheatsheets"', 1)[1]
    body = text.split('class="cs-name">/update</span>', 1)[1].split("</article>", 1)[0]
    release = re.search(r'<code[^>]*>release</code><span[^>]*>([^<]+)</span>', body)
    assert release, "the /update card has no release scope"
    assert "closing pull request" in release.group(1)
    assert "checked cleanup" in release.group(1) and "merged, idle" in release.group(1)


COMMANDS_DIR = ROOT / "catalog" / "commands"
_SCOPES = re.compile(r"Recognized scopes: ((?:`[^`]+`(?:, )?)+)\.")


def _cheatsheet_card(name: str) -> str | None:
    text = GUIDE.read_text(encoding="utf-8").split('id="page-cheatsheets"', 1)[1]
    marker = f'class="cs-name">/{name}</span>'
    if marker not in text:
        return None
    return text.split(marker, 1)[1].split("</article>", 1)[0]


@pytest.mark.parametrize("command", sorted(p.stem for p in COMMANDS_DIR.glob("*.md")))
def test_every_command_file_has_a_cheatsheet_card(command: str) -> None:
    # v4.13.9: /visualize shipped without a card because only /implement was compared.
    assert _cheatsheet_card(command) is not None, f"/{command} has no card on the Cheatsheets page"


def _declared_scopes() -> list[tuple[str, str]]:
    pairs = []
    for path in sorted(COMMANDS_DIR.glob("*.md")):
        match = _SCOPES.search(path.read_text(encoding="utf-8"))
        if match:
            pairs += [(path.stem, scope) for scope in re.findall(r"`([^`]+)`", match.group(1))]
    return pairs


@pytest.mark.parametrize(("command", "scope"), _declared_scopes())
def test_every_declared_scope_appears_on_its_card(command: str, scope: str) -> None:
    card = _cheatsheet_card(command)
    assert card is not None, f"/{command} has no card"
    assert f'<code data-ty="code">{html.escape(scope)}</code>' in card, f"/{command} card does not list the `{scope}` scope"


def test_the_review_card_teaches_the_one_commit_form_and_drafts() -> None:
    card = html.unescape(_cheatsheet_card("review") or "")
    assert "changes <sha>" in card
    assert "never posts" in card
