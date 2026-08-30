#!/usr/bin/env bash
# HTML Responsive Guard - PreToolUse Hook for Claude Code
# Blocks fixed px/ch max-width declarations on text-bearing HTML/CSS selectors.
# Part of Nexus-Hub

set -euo pipefail

# --- Runtime controls ---
# Disable by name:        export NEXUS_DISABLED_HOOKS=html-responsive-guard
# Skip non-essential:     export NEXUS_HOOK_PROFILE=minimal
_HOOK_NAME="html-responsive-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

# A supported Nexus-Hub installation includes Python. Using it here keeps the
# multiline JSON and CSS parsing active on hosts that do not provide jq.
if command -v python3 >/dev/null 2>&1; then
  _PYTHON=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
  _PYTHON=$(command -v python)
else
  exit 0
fi

_INPUT=$(cat)
[ -n "${_INPUT:-}" ] || exit 0

set +e
printf '%s' "$_INPUT" | "$_PYTHON" -c '
import json
import re
import sys

HOOK = "html-responsive-guard"
RULE = "catalog/rules/html/responsive-layout.md"
PATH_RE = re.compile(r"\.(?:html?|xhtml|css)$", re.IGNORECASE)
DECL_RE = re.compile(r"\bmax-width\s*:\s*-?(?:\d+(?:\.\d+)?|\.\d+)\s*(?:px|ch)\b", re.IGNORECASE)
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<([a-z][a-z0-9:-]*)\b([^>]*)>", re.IGNORECASE | re.DOTALL)
STYLE_ATTR_RE = re.compile(r"\bstyle\s*=\s*([\"\047])(.*?)\1", re.IGNORECASE | re.DOTALL)
CLASS_ATTR_RE = re.compile(r"\bclass\s*=\s*([\"\047])(.*?)\1", re.IGNORECASE | re.DOTALL)
ID_ATTR_RE = re.compile(r"\bid\s*=\s*([\"\047])(.*?)\1", re.IGNORECASE | re.DOTALL)
MEDIA_TAGS = {"img", "video", "canvas", "svg", "picture", "iframe", "object", "embed", "figure"}
TEXT_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "figcaption", "dd", "dt", "label", "legend", "caption", "summary", "time", "address", "code"}
CONTAINER_NAMES = {"container", "wrapper", "shell", "layout", "page", "frame", "viewport", "inner", "outer"}
MEDIA_NAMES = {"media", "image", "video", "visual", "artwork", "illustration"}
TEXT_NAMES = {"copy", "text", "prose", "paragraph", "title", "subtitle", "heading", "headline", "description", "intro", "lead", "caption", "label", "message", "note", "summary"}


def named_token(name, candidates):
    parts = {part for part in re.split(r"[-_]", name.lower()) if part}
    return bool(parts & candidates)


def terminal_target(selector):
    pieces = [part for part in re.split(r"\s+|[>+~]", selector.strip()) if part]
    return pieces[-1] if pieces else ""


def target_tokens(target):
    return [match.group(1).lower() for match in re.finditer(r"[.#]([a-z0-9_-]+)", target, re.IGNORECASE)]


def direct_tag(target, names):
    match = re.match(r"^([a-z][a-z0-9:-]*)", target.strip(), re.IGNORECASE)
    return bool(match and match.group(1).lower() in names)


def permitted_target(target):
    if direct_tag(target, MEDIA_TAGS):
        return True
    tokens = target_tokens(target)
    return any(named_token(token, CONTAINER_NAMES | MEDIA_NAMES) for token in tokens)


def text_target(target):
    if direct_tag(target, TEXT_TAGS):
        return True
    return any(named_token(token, TEXT_NAMES) for token in target_tokens(target))


def text_selector(selector):
    for part in selector.split(","):
        target = terminal_target(part)
        if not target or direct_tag(target, MEDIA_TAGS):
            continue
        if text_target(target):
            return True
        if permitted_target(target):
            continue
    return False


def inline_text(tag, attrs):
    tag = tag.lower()
    if tag in MEDIA_TAGS:
        return False
    if tag in TEXT_TAGS:
        return True
    names = []
    for pattern in (CLASS_ATTR_RE, ID_ATTR_RE):
        match = pattern.search(attrs)
        if match:
            names.extend(re.split(r"\s+", match.group(2)))
    if any(named_token(name, TEXT_NAMES) for name in names):
        return True
    if any(named_token(name, CONTAINER_NAMES | MEDIA_NAMES) for name in names):
        return False
    return False


def find_declaration(path, content):
    clean = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    css_blocks = []
    if path.lower().endswith(".css"):
        css_blocks.append(clean)
    else:
        css_blocks.extend(STYLE_RE.findall(clean))
        if not css_blocks and "{" in clean and DECL_RE.search(clean):
            css_blocks.append(clean)

    for css in css_blocks:
        for rule_match in RULE_RE.finditer(css):
            selector, body = rule_match.groups()
            declaration = DECL_RE.search(body)
            if declaration and text_selector(selector):
                return declaration.group(0)

    if not path.lower().endswith(".css"):
        for tag_match in TAG_RE.finditer(clean):
            tag, attrs = tag_match.groups()
            style = STYLE_ATTR_RE.search(attrs)
            if not style:
                continue
            declaration = DECL_RE.search(style.group(2))
            if declaration and inline_text(tag, attrs):
                return declaration.group(0)
    return None


try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
if not isinstance(tool_input, dict):
    sys.exit(0)
path = tool_input.get("file_path") or tool_input.get("path")
content = tool_input.get("content")
if content is None:
    content = tool_input.get("new_string")
if not isinstance(path, str) or not isinstance(content, str) or not content or not PATH_RE.search(path):
    sys.exit(0)

declaration = find_declaration(path, content)
if not declaration:
    sys.exit(0)

print(f"[{HOOK}] BLOCKED: {declaration} in {path} violates {RULE}.", file=sys.stderr)
print("Fixed px/ch text caps must move to a responsive container.", file=sys.stderr)
sys.exit(2)
'
_STATUS=$?
set -e

if [ "$_STATUS" -eq 2 ]; then exit 2; fi
# Malformed payloads, irrelevant paths, and internal parsing failures fail open.
exit 0
