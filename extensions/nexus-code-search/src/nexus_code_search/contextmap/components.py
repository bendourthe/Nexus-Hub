"""UI component extraction.

Detects React function / const components in `.tsx` / `.jsx` files and their
props (names only). Scoping to JSX files makes an exported PascalCase
function/const a reliable component signal, so a plain helper is not misreported.
Props come from a destructured parameter, or from the named props type resolved
to its `interface` / `type` declaration in the same file. Vue and Svelte are
deferred - each needs its own detector and fixture.
"""

from __future__ import annotations

import re
from pathlib import Path

from nexus_code_search.contextmap.model import ComponentInfo

_COMPONENT_EXTS = (".tsx", ".jsx")

# export function Foo(<params>)   /   export default function Foo(<params>)
# Group 2 = params (may carry a `}: Props` type annotation).
_FUNC_COMPONENT = re.compile(
    r"export\s+(?:default\s+)?function\s+([A-Z]\w*)\s*\(([^)]*)\)"
)
# export const Foo = (<params>) =>   /   export const Foo: React.FC<Props> = (<params>) =>
# Group 2 = the const type annotation (e.g. React.FC<Props>); group 3 = params.
_CONST_COMPONENT = re.compile(
    r"export\s+const\s+([A-Z]\w*)\s*(?::\s*([^=]+?))?=\s*\(([^)]*)\)\s*=>"
)


def extract_components(
    root: Path, code_files: list[tuple[str, str]]
) -> list[ComponentInfo]:
    """Detect React components across the `.tsx` / `.jsx` files in ``code_files``."""
    components: list[ComponentInfo] = []
    for rel_path, _language in sorted(code_files):
        if not rel_path.endswith(_COMPONENT_EXTS):
            continue
        text = _read(root / rel_path)
        if not text:
            continue
        seen: set[str] = set()
        for match in _FUNC_COMPONENT.finditer(text):
            _add_component(
                components, match.group(1), match.group(2), None, text, rel_path, seen
            )
        for match in _CONST_COMPONENT.finditer(text):
            _add_component(
                components,
                match.group(1),
                match.group(3),
                match.group(2),
                text,
                rel_path,
                seen,
            )
    components.sort(key=lambda c: (c.source_file, c.name))
    return components


def _add_component(
    components: list[ComponentInfo],
    name: str,
    param: str,
    annotation: str | None,
    text: str,
    rel_path: str,
    seen: set[str],
) -> None:
    if name in seen:
        return
    seen.add(name)
    components.append(
        ComponentInfo(
            name=name,
            framework="react",
            props=_extract_props(param, annotation, text),
            source_file=rel_path,
        )
    )


def _extract_props(param: str, annotation: str | None, text: str) -> tuple[str, ...]:
    """Prop names, unioning the destructured parameter with the declared prop
    type (a `}: Props` param annotation or a `React.FC<Props>` const generic)."""
    names: list[str] = []
    param = param.strip()
    if param.startswith("{"):
        names.extend(_destructured_names(param))
    # A named type reference on the param (`props: T` or `{...}: T`) or the const.
    type_name = None
    param_type = re.search(
        r"}\s*:\s*([A-Za-z_]\w*)|^\s*\w+\s*:\s*([A-Za-z_]\w*)", param
    )
    if param_type:
        type_name = param_type.group(1) or param_type.group(2)
    elif annotation:
        generic = re.search(r"<\s*([A-Za-z_]\w*)", annotation)
        if generic:
            type_name = generic.group(1)
    if type_name:
        for prop in _resolve_type_props(type_name, text):
            if prop not in names:
                names.append(prop)
    return tuple(names)


def _destructured_names(param: str) -> tuple[str, ...]:
    inner = param[1 : param.rfind("}")] if "}" in param else param[1:]
    names: list[str] = []
    for chunk in inner.split(","):
        token = chunk.split(":")[0].split("=")[0].strip().lstrip(".")
        if re.fullmatch(r"[A-Za-z_]\w*", token):
            names.append(token)
    return tuple(names)


def _resolve_type_props(type_name: str, text: str) -> tuple[str, ...]:
    block = re.search(
        rf"(?:interface\s+{re.escape(type_name)}\s*|type\s+{re.escape(type_name)}\s*=\s*)\{{([^}}]*)\}}",
        text,
    )
    if not block:
        return ()
    names: list[str] = []
    # Members are separated by ';', ',', or newlines (types may be one-liners).
    for piece in re.split(r"[;,\n]", block.group(1)):
        member = re.match(r"\s*([A-Za-z_]\w*)\s*[?:]", piece)
        if member and member.group(1) not in names:
            names.append(member.group(1))
    return tuple(names)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
