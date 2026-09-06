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

_json_skip_ws() {
  local char
  while [ "$_JSON_POS" -lt "$_JSON_LEN" ]; do
    char="${_JSON_TEXT:_JSON_POS:1}"
    case "$char" in
      ' '|$'\t'|$'\n'|$'\r') _JSON_POS=$((_JSON_POS + 1)) ;;
      *) break ;;
    esac
  done
}

_json_parse_string() {
  local char escape hex
  [ "${_JSON_TEXT:_JSON_POS:1}" = '"' ] || return 1
  _JSON_POS=$((_JSON_POS + 1))
  _JSON_STRING_START=$_JSON_POS
  _JSON_STRING_SIMPLE=1
  while [ "$_JSON_POS" -lt "$_JSON_LEN" ]; do
    char="${_JSON_TEXT:_JSON_POS:1}"
    case "$char" in
      '"')
        _JSON_LAST_STRING="${_JSON_TEXT:_JSON_STRING_START:$((_JSON_POS - _JSON_STRING_START))}"
        _JSON_LAST_STRING_SIMPLE=$_JSON_STRING_SIMPLE
        _JSON_LAST_TYPE="string"
        _JSON_POS=$((_JSON_POS + 1))
        return 0
        ;;
      \\)
        _JSON_STRING_SIMPLE=0
        _JSON_POS=$((_JSON_POS + 1))
        [ "$_JSON_POS" -lt "$_JSON_LEN" ] || return 1
        escape="${_JSON_TEXT:_JSON_POS:1}"
        case "$escape" in
          \"|\\|/|b|f|n|r|t) _JSON_POS=$((_JSON_POS + 1)) ;;
          u)
            _JSON_POS=$((_JSON_POS + 1))
            [ $((_JSON_POS + 4)) -le "$_JSON_LEN" ] || return 1
            hex="${_JSON_TEXT:_JSON_POS:4}"
            [[ "$hex" =~ ^[0-9a-fA-F]{4}$ ]] || return 1
            _JSON_POS=$((_JSON_POS + 4))
            ;;
          *) return 1 ;;
        esac
        ;;
      $'\n'|$'\r'|$'\t') return 1 ;;
      *) _JSON_POS=$((_JSON_POS + 1)) ;;
    esac
  done
  return 1
}

_json_parse_number() {
  local remaining token
  remaining="${_JSON_TEXT:_JSON_POS}"
  if [[ "$remaining" =~ ^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)? ]]; then
    token="${BASH_REMATCH[0]}"
    _JSON_POS=$((_JSON_POS + ${#token}))
    return 0
  fi
  return 1
}

_json_parse_array() {
  local depth="$1" context="$2" char child_context
  _JSON_POS=$((_JSON_POS + 1))
  _json_skip_ws
  if [ "${_JSON_TEXT:_JSON_POS:1}" = ']' ]; then
    _JSON_POS=$((_JSON_POS + 1))
    _JSON_LAST_TYPE="array"
    return 0
  fi
  if [ "$context" = "tool_input" ] || [ "$context" = "tool_input_nested" ]; then
    child_context="tool_input_nested"
  else
    child_context="other"
  fi
  while true; do
    _json_parse_value "$((depth + 1))" "$child_context" || return 1
    _json_skip_ws
    char="${_JSON_TEXT:_JSON_POS:1}"
    case "$char" in
      ',') _JSON_POS=$((_JSON_POS + 1)); _json_skip_ws ;;
      ']') _JSON_POS=$((_JSON_POS + 1)); _JSON_LAST_TYPE="array"; return 0 ;;
      *) return 1 ;;
    esac
  done
}

_json_parse_object() {
  local depth="$1" context="$2" char key child_context
  _JSON_POS=$((_JSON_POS + 1))
  _json_skip_ws
  if [ "${_JSON_TEXT:_JSON_POS:1}" = '}' ]; then
    _JSON_POS=$((_JSON_POS + 1))
    _JSON_LAST_TYPE="object"
    return 0
  fi
  while true; do
    _json_parse_string || return 1
    key="$_JSON_LAST_STRING"
    _json_skip_ws
    [ "${_JSON_TEXT:_JSON_POS:1}" = ':' ] || return 1
    _JSON_POS=$((_JSON_POS + 1))
    child_context="other"
    if [ "$context" = "root" ] && [ "$key" = "tool_input" ]; then
      _TOOL_INPUT_COUNT=$((_TOOL_INPUT_COUNT + 1))
      child_context="tool_input"
    elif [ "$context" = "tool_input" ] || [ "$context" = "tool_input_nested" ]; then
      child_context="tool_input_nested"
    fi
    _json_parse_value "$((depth + 1))" "$child_context" || return 1
    if [ "$context" = "root" ] && [ "$key" = "tool_input" ] && [ "$_JSON_LAST_TYPE" != "object" ]; then
      _TOOL_PATH_AMBIGUOUS=1
    elif [ "$context" = "tool_input" ] && { [ "$key" = "file_path" ] || [ "$key" = "path" ]; }; then
      _TOOL_PATH_COUNT=$((_TOOL_PATH_COUNT + 1))
      if [ "$_JSON_LAST_TYPE" = "string" ] && [ "$_JSON_LAST_STRING_SIMPLE" -eq 1 ]; then
        _TOOL_PATH_VALUE="$_JSON_LAST_STRING"
      else
        _TOOL_PATH_AMBIGUOUS=1
      fi
    elif [ "$context" = "tool_input_nested" ] && { [ "$key" = "file_path" ] || [ "$key" = "path" ]; }; then
      _TOOL_PATH_AMBIGUOUS=1
    fi
    _json_skip_ws
    char="${_JSON_TEXT:_JSON_POS:1}"
    case "$char" in
      ',') _JSON_POS=$((_JSON_POS + 1)); _json_skip_ws ;;
      '}') _JSON_POS=$((_JSON_POS + 1)); _JSON_LAST_TYPE="object"; return 0 ;;
      *) return 1 ;;
    esac
  done
}

_json_parse_value() {
  local depth="$1" context="$2" char literal
  [ "$depth" -le 64 ] || return 1
  _json_skip_ws
  [ "$_JSON_POS" -lt "$_JSON_LEN" ] || return 1
  char="${_JSON_TEXT:_JSON_POS:1}"
  case "$char" in
    '"') _json_parse_string ;;
    '{') _json_parse_object "$depth" "$context" ;;
    '[') _json_parse_array "$depth" "$context" ;;
    t)
      literal="${_JSON_TEXT:_JSON_POS:4}"
      [ "$literal" = 'true' ] || return 1
      _JSON_POS=$((_JSON_POS + 4))
      _JSON_LAST_TYPE="literal"
      ;;
    f)
      literal="${_JSON_TEXT:_JSON_POS:5}"
      [ "$literal" = 'false' ] || return 1
      _JSON_POS=$((_JSON_POS + 5))
      _JSON_LAST_TYPE="literal"
      ;;
    n)
      literal="${_JSON_TEXT:_JSON_POS:4}"
      [ "$literal" = 'null' ] || return 1
      _JSON_POS=$((_JSON_POS + 4))
      _JSON_LAST_TYPE="literal"
      ;;
    -|[0-9]) _json_parse_number; _JSON_LAST_TYPE="number" ;;
    *) return 1 ;;
  esac
}

_json_validate() {
  _JSON_TEXT="$1"
  _JSON_POS=0
  _JSON_LEN=${#_JSON_TEXT}
  _TOOL_INPUT_COUNT=0
  _TOOL_PATH_COUNT=0
  _TOOL_PATH_AMBIGUOUS=0
  _TOOL_PATH_VALUE=""
  _JSON_LAST_TYPE=""
  _JSON_LAST_STRING=""
  _JSON_LAST_STRING_SIMPLE=0
  _json_parse_value 0 "root" || return 1
  _json_skip_ws
  [ "$_JSON_POS" -eq "$_JSON_LEN" ] && [ "$_JSON_LAST_TYPE" = "object" ]
}

IFS= read -r -d '' _INPUT || true
[ -n "${_INPUT:-}" ] || exit 0

# Full parsing uses Python so multiline JSON and CSS remain correct without jq.
# A missing parser may allow a clearly irrelevant path, but it must not report a
# relevant HTML/CSS payload as clean when the guard never inspected it.
if command -v python3 >/dev/null 2>&1; then
  _PYTHON=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
  _PYTHON=$(command -v python)
else
  if [ "${#_INPUT}" -gt 1048576 ]; then
    printf '[%s] CANNOT RUN: Python 3 is required to classify a hook payload larger than 1 MiB.\n' \
      "$_HOOK_NAME" >&2
    exit 3
  fi
  shopt -s nocasematch
  set +e
  _json_validate "$_INPUT"
  _JSON_STATUS=$?
  set -e
  if [ "$_JSON_STATUS" -ne 0 ] || [ "$_TOOL_INPUT_COUNT" -ne 1 ] || \
     [ "$_TOOL_PATH_COUNT" -ne 1 ] || [ "$_TOOL_PATH_AMBIGUOUS" -ne 0 ]; then
    printf '[%s] CANNOT RUN: Python 3 is required because the hook payload is malformed or unclassifiable.\n' \
      "$_HOOK_NAME" >&2
    exit 3
  fi
  if [[ "$_TOOL_PATH_VALUE" =~ \.(html?|xhtml|css)$ ]]; then
    printf '[%s] CANNOT RUN: Python 3 is required to inspect relevant HTML/CSS payload %s.\n' \
      "$_HOOK_NAME" "$_TOOL_PATH_VALUE" >&2
    exit 3
  fi
  exit 0
fi

set +e
printf '%s' "$_INPUT" | "$_PYTHON" -c '
import json
import os
import re
import sys

HOOK = "html-responsive-guard"
RULE = "catalog/rules/html/responsive-layout.md"
PATH_RE = re.compile(r"\.(?:html?|xhtml|css)$", re.IGNORECASE)
MAX_WIDTH_RE = re.compile(r"\bmax-width\s*:\s*([^;{}]+)", re.IGNORECASE)
FIXED_UNIT_RE = re.compile(r"-?(?:\d+(?:\.\d+)?|\.\d+)\s*(?:px|ch)\b", re.IGNORECASE)
CUSTOM_PROP_RE = re.compile(r"(--[a-z0-9_-]+)\s*:\s*([^;{}]+)", re.IGNORECASE)
VAR_START_RE = re.compile(r"\bvar\s*\(", re.IGNORECASE)
CUSTOM_NAME_RE = re.compile(r"--[a-z0-9_-]+", re.IGNORECASE)
IMPORTANT_RE = re.compile(r"\s*!\s*important\s*$", re.IGNORECASE)
CSS_WIDE_VALUES = {"inherit", "initial", "unset", "revert", "revert-layer"}
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
MAX_EDIT_BYTES = 5 * 1024 * 1024


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


def local_custom_property_declarations(source):
    selected = {}
    for match in CUSTOM_PROP_RE.finditer(source):
        name = match.group(1)
        raw_value = match.group(2).strip()
        important = bool(IMPORTANT_RE.search(raw_value))
        value = IMPORTANT_RE.sub("", raw_value).strip()
        current = selected.get(name)
        if current is None or important or not current["important"]:
            selected[name] = {"value": value, "important": important}
    return selected


def local_custom_properties(source):
    return {
        name: declaration["value"]
        for name, declaration in local_custom_property_declarations(source).items()
    }


def selector_key(selector):
    return re.sub(r"\s+", " ", selector.strip())


def selector_custom_property_declarations(source):
    bodies_by_selector = {}
    for match in RULE_RE.finditer(source):
        selector, body = match.groups()
        bodies_by_selector.setdefault(selector_key(selector), []).append(body)
    return {
        selector: local_custom_property_declarations(";".join(bodies))
        for selector, bodies in bodies_by_selector.items()
    }


def selector_custom_properties(source):
    return {
        selector: {
            name: declaration["value"]
            for name, declaration in declarations.items()
        }
        for selector, declarations in selector_custom_property_declarations(source).items()
    }


def root_selector(selector):
    return any(
        part.strip().lower() in {":root", "html"} for part in selector.split(",")
    )


def matching_terminal_target(selector, candidate_selector):
    current_targets = [terminal_target(part) for part in selector.split(",")]
    candidate_targets = [terminal_target(part) for part in candidate_selector.split(",")]
    for current in current_targets:
        current_tokens = set(target_tokens(current))
        current_tag = re.match(r"^([a-z][a-z0-9:-]*)", current, re.IGNORECASE)
        for candidate in candidate_targets:
            candidate_tokens = set(target_tokens(candidate))
            candidate_tag = re.match(
                r"^([a-z][a-z0-9:-]*)", candidate, re.IGNORECASE
            )
            if current_tokens & candidate_tokens:
                return True
            if (
                current_tag
                and candidate_tag
                and current_tag.group(1).lower() == candidate_tag.group(1).lower()
            ):
                return True
    return False


def add_candidate(
    candidates, name, value, guaranteed, selector=None, important=False
):
    entry = candidates.setdefault(
        name, {"values": [], "definitions": [], "guaranteed": False}
    )
    entry["values"].append(value)
    entry["definitions"].append(
        {"value": value, "selector": selector, "important": important}
    )
    entry["guaranteed"] = entry["guaranteed"] or guaranteed


def custom_property_candidates(css_source, html_source=""):
    candidates = {}
    selector_declarations = selector_custom_property_declarations(css_source)
    for selector, declarations in selector_declarations.items():
        guaranteed = root_selector(selector)
        for name, declaration in declarations.items():
            add_candidate(
                candidates,
                name,
                declaration["value"],
                guaranteed,
                selector,
                declaration["important"],
            )
    for match in STYLE_ATTR_RE.finditer(html_source):
        for name, declaration in local_custom_property_declarations(
            match.group(2)
        ).items():
            add_candidate(
                candidates,
                name,
                declaration["value"],
                False,
                None,
                declaration["important"],
            )
    if not selector_declarations and not html_source:
        for name, declaration in local_custom_property_declarations(
            css_source
        ).items():
            add_candidate(
                candidates,
                name,
                declaration["value"],
                False,
                None,
                declaration["important"],
            )
    return candidates


def top_level_var_calls(value):
    calls = []
    cursor = 0
    while True:
        match = VAR_START_RE.search(value, cursor)
        if not match:
            break
        open_index = value.find("(", match.start(), match.end())
        depth = 1
        quote = None
        escaped = False
        index = open_index + 1
        while index < len(value) and depth:
            char = value[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in {"\"", "\047"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth:
            calls.append((None, None, match.start(), len(value), False))
            break

        end = index
        content = value[open_index + 1 : end - 1]
        comma = None
        nested = 0
        quote = None
        escaped = False
        for offset, char in enumerate(content):
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in {"\"", "\047"}:
                quote = char
            elif char == "(":
                nested += 1
            elif char == ")":
                nested = max(0, nested - 1)
            elif char == "," and nested == 0:
                comma = offset
                break
        name_text = content if comma is None else content[:comma]
        fallback = None if comma is None else content[comma + 1 :].strip()
        name = name_text.strip()
        valid = bool(CUSTOM_NAME_RE.fullmatch(name))
        calls.append((name, fallback, match.start(), end, valid))
        cursor = end
    return calls


def value_fixed_state(
    value,
    candidates,
    local,
    local_priorities=None,
    selector="",
    seen=frozenset(),
    memo=None,
    depth=0,
):
    if value.strip().lower() in CSS_WIDE_VALUES:
        return False, True
    calls = top_level_var_calls(value)
    outside = []
    cursor = 0
    for _, _, start, end, valid in calls:
        outside.append(value[cursor:start])
        cursor = end
        if not valid:
            return True, True
    outside.append(value[cursor:])
    if FIXED_UNIT_RE.search("".join(outside)):
        return True, False
    if depth >= 32:
        return True, True
    if memo is None:
        memo = {}

    may_be_invalid = False
    for name, fallback, _, _, _ in calls:
        if name in seen:
            definition_state = (False, True)
        elif name in memo:
            definition_state = memo[name]
        else:
            if name in local:
                possible_values = [local[name]]
                may_be_absent = False
                local_important = bool(
                    local_priorities and local_priorities.get(name, False)
                )
                entry = candidates.get(name)
                if selector and entry:
                    for definition in entry["definitions"]:
                        candidate_selector = definition["selector"]
                        if (
                            candidate_selector
                            and selector_key(candidate_selector) != selector_key(selector)
                            and not root_selector(candidate_selector)
                            and matching_terminal_target(selector, candidate_selector)
                            and (definition["important"] or not local_important)
                        ):
                            possible_values.append(definition["value"])
            else:
                entry = candidates.get(name)
                possible_values = entry["values"] if entry else []
                may_be_absent = not entry or not entry["guaranteed"]
            if not possible_values:
                definition_state = (False, True)
            else:
                next_seen = seen | {name}
                states = [
                    value_fixed_state(
                        possible,
                        candidates,
                        local,
                        local_priorities,
                        selector,
                        next_seen,
                        memo,
                        depth + 1,
                    )
                    for possible in possible_values
                ]
                definition_state = (
                    any(state[0] for state in states),
                    may_be_absent or any(state[1] for state in states),
                )
            memo[name] = definition_state

        reaches_fixed, definition_invalid = definition_state
        if reaches_fixed:
            return True, may_be_invalid or definition_invalid
        if definition_invalid:
            if fallback is not None:
                fallback_fixed, fallback_invalid = value_fixed_state(
                    fallback,
                    candidates,
                    local,
                    local_priorities,
                    selector,
                    seen,
                    memo,
                    depth + 1,
                )
                if fallback_fixed:
                    return True, may_be_invalid or fallback_invalid
                may_be_invalid = may_be_invalid or fallback_invalid
            else:
                may_be_invalid = True
    return False, may_be_invalid


def fixed_width_declaration(
    source, candidates, local=None, local_priorities=None, selector=""
):
    if local is None:
        local = local_custom_properties(source)
    memo = {}
    for match in MAX_WIDTH_RE.finditer(source):
        if value_fixed_state(
            match.group(1),
            candidates,
            local,
            local_priorities,
            selector,
            memo=memo,
        )[0]:
            return match.group(0).strip()
    return None


def reconstruct_edit(path, old_string, new_string, replace_all):
    if not isinstance(old_string, str) or not old_string:
        return None
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "rb") as handle:
            raw = handle.read(MAX_EDIT_BYTES + 1)
        if len(raw) > MAX_EDIT_BYTES:
            return None
        source = raw.decode("utf-8-sig")
    except (OSError, UnicodeError):
        return None
    index = source.find(old_string)
    if index < 0:
        return None
    if replace_all:
        return source.replace(old_string, new_string)
    return source[:index] + new_string + source[index + len(old_string) :]


def unresolved_text_declaration(path, content):
    clean = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    css_blocks = []
    if path.lower().endswith(".css"):
        css_blocks.append(clean)
    else:
        css_blocks.extend(STYLE_RE.findall(clean))
        if not css_blocks and "{" in clean and MAX_WIDTH_RE.search(clean):
            css_blocks.append(clean)

    for css in css_blocks:
        for rule_match in RULE_RE.finditer(css):
            selector, body = rule_match.groups()
            if not text_selector(selector):
                continue
            for declaration in MAX_WIDTH_RE.finditer(body):
                if VAR_START_RE.search(declaration.group(1)):
                    return declaration.group(0).strip()

    if not path.lower().endswith(".css"):
        for tag_match in TAG_RE.finditer(clean):
            tag, attrs = tag_match.groups()
            style = STYLE_ATTR_RE.search(attrs)
            if not style or not inline_text(tag, attrs):
                continue
            for declaration in MAX_WIDTH_RE.finditer(style.group(2)):
                if VAR_START_RE.search(declaration.group(1)):
                    return declaration.group(0).strip()
    return None


def unsafe_custom_property_declaration(content):
    clean = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    for declaration in CUSTOM_PROP_RE.finditer(clean):
        value = declaration.group(2)
        if FIXED_UNIT_RE.search(value) or VAR_START_RE.search(value):
            return declaration.group(0).strip()
    return None


def find_declaration(path, content):
    clean = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    css_blocks = []
    if path.lower().endswith(".css"):
        css_blocks.append(clean)
    else:
        css_blocks.extend(STYLE_RE.findall(clean))
        if not css_blocks and "{" in clean and MAX_WIDTH_RE.search(clean):
            css_blocks.append(clean)

    css_source = "\n".join(css_blocks)
    candidates = custom_property_candidates(
        css_source, "" if path.lower().endswith(".css") else clean
    )
    scoped_declarations = selector_custom_property_declarations(css_source)
    for css in css_blocks:
        for rule_match in RULE_RE.finditer(css):
            selector, body = rule_match.groups()
            declarations = scoped_declarations.get(selector_key(selector), {})
            local = {
                name: declaration["value"]
                for name, declaration in declarations.items()
            }
            local_priorities = {
                name: declaration["important"]
                for name, declaration in declarations.items()
            }
            declaration = fixed_width_declaration(
                body, candidates, local, local_priorities, selector
            )
            if declaration and text_selector(selector):
                return declaration

    if not path.lower().endswith(".css"):
        for tag_match in TAG_RE.finditer(clean):
            tag, attrs = tag_match.groups()
            style = STYLE_ATTR_RE.search(attrs)
            if not style:
                continue
            declaration = fixed_width_declaration(style.group(2), candidates)
            if declaration and inline_text(tag, attrs):
                return declaration
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
new_string = tool_input.get("new_string")
old_string = tool_input.get("old_string")
replace_all = tool_input.get("replace_all") is True
reconstruction_failed = False
if not isinstance(path, str) or not PATH_RE.search(path):
    sys.exit(0)
if not isinstance(content, str):
    if not isinstance(new_string, str):
        sys.exit(0)
    reconstructed = reconstruct_edit(path, old_string, new_string, replace_all)
    if reconstructed is None:
        content = new_string
        reconstruction_failed = True
    else:
        content = reconstructed
if not content:
    sys.exit(0)

declaration = find_declaration(path, content)
if declaration:
    print(f"[{HOOK}] BLOCKED: {declaration} in {path} violates {RULE}.", file=sys.stderr)
    print("Fixed px/ch text caps must move to a responsive container.", file=sys.stderr)
    sys.exit(2)

if reconstruction_failed:
    unresolved = unresolved_text_declaration(path, new_string)
    unsafe_custom_property = unsafe_custom_property_declaration(new_string)
    risky_declaration = unresolved or unsafe_custom_property
    if risky_declaration:
        print(
            f"[{HOOK}] BLOCKED: could not reconstruct {path} before evaluating {risky_declaration}; "
            f"verify the target file and retry. Rule: {RULE}.",
            file=sys.stderr,
        )
        sys.exit(2)
sys.exit(0)
'
_STATUS=$?
set -e

if [ "$_STATUS" -eq 0 ]; then exit 0; fi
if [ "$_STATUS" -eq 2 ]; then exit 2; fi
printf '%s\n' "[html-responsive-guard] CANNOT RUN: internal parser failed with status $_STATUS; refusing to allow a potentially relevant HTML/CSS edit." >&2
exit 3
