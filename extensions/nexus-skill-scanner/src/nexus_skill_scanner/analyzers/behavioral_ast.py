"""Behavioral AST analyzer for Python skill scripts.

Covers class 12 (behavioral AST: dynamic code execution, dynamic imports,
subprocess, reflective loading, getattr manipulation), the executable portion
of class 2 (credential exfiltration: an environment-variable read combined
with a network egress call), and class 13 (taint tracking: a tainted source
flowing into a dangerous sink).

The analyzer parses real ``.py`` files with the standard library ``ast``
module -- it never executes them and never inspects fenced examples in
Markdown (those are illustrative, not executable). Import aliases and
from-imports are resolved so ``import subprocess as sp; sp.run(...)`` and
``from subprocess import run`` are both recognized, and ``re.compile`` is
correctly distinguished from the ``compile`` builtin.

Severity discipline: only the genuine dynamic-code-execution builtins
(``exec`` / ``eval`` / ``compile``) and credential exfiltration are
HIGH/CRITICAL; process execution, dynamic import, reflective loading, and
reflection are MEDIUM or LOW so legitimate tooling (e.g. a ``subprocess.run``
with a literal argument list) does not trip the catalog gate.
"""

from __future__ import annotations

import ast
import re

from ..types import Finding, Severity
from .base import FileUnit, make_finding

# --- Class-2 refinement: self-authenticating API client vs. exfiltration ------
# "env read + network egress" is only credential exfiltration when the credential
# could leave to a host that is NOT its own service. A legitimate API client
# reads its OWN key (e.g. PEXELS_API_KEY) and calls THAT service (api.pexels.com):
# the credential's service token appears in an egress host it calls. We detect
# that positive signal and emit the class-2 finding at MEDIUM (still reported and
# visible to review, just below the HIGH gate) instead of HIGH. With no such
# correlation - the classic "read a credential, send it to an unrelated host" -
# the finding stays HIGH. Downgrading to MEDIUM (not suppressing) keeps the
# construct on the radar for the skill-security-scan adjudication skill.
_URL_HOST_RE = re.compile(r"https?://([A-Za-z0-9.\-]+)")

# Tokens carried by many credential names AND hostnames that do NOT identify a
# specific service, so they must never create a spurious credential<->host match.
_GENERIC_SERVICE_TOKENS = frozenset({
    "api", "key", "keys", "token", "tokens", "secret", "secrets", "auth",
    "access", "id", "client", "app", "apikey", "www", "com", "org", "net",
    "io", "co", "dev", "cloud", "http", "https", "gov", "edu", "backend",
    "service", "services", "user", "pass", "password", "url", "endpoint",
})


def _service_tokens(raw: str) -> set[str]:
    """Distinctive lowercase service tokens from a credential name or a hostname.

    Splits on non-alphanumeric boundaries, drops generic/structural tokens and
    very short or purely-numeric fragments, so e.g. ``PEXELS_API_KEY`` ->
    ``{"pexels"}`` and ``api.pexels.com`` -> ``{"pexels"}`` (they correlate),
    while ``AWS_SECRET_ACCESS_KEY`` -> ``{"aws"}`` and ``evil.com`` -> ``set()``
    (they do not).
    """
    parts = re.split(r"[^A-Za-z0-9]+", raw.lower())
    return {
        p for p in parts
        if len(p) >= 3 and not p.isdigit() and p not in _GENERIC_SERVICE_TOKENS
    }

# Bare builtin calls that execute dynamically-constructed code. These are the
# strongest static signal of malicious behavior in a skill script.
CODE_EXEC_BUILTINS = frozenset({"exec", "eval", "compile"})

# Dotted call targets, resolved through import aliases/from-imports.
DYNAMIC_IMPORT = frozenset(
    {"__import__", "importlib.import_module", "importlib.__import__", "importlib.reload"}
)
PROCESS_EXEC = frozenset(
    {
        "os.system", "os.popen", "os.execv", "os.execve", "os.execl",
        "os.execlp", "os.execvp", "os.execvpe", "os.spawnl", "os.spawnv",
        "subprocess.run", "subprocess.call", "subprocess.Popen",
        "subprocess.check_output", "subprocess.check_call",
        "subprocess.getoutput", "subprocess.getstatusoutput",
        "pty.spawn", "commands.getoutput",
    }
)
REFLECTIVE_LOAD = frozenset(
    {"pickle.loads", "pickle.load", "marshal.loads", "marshal.load", "dill.loads"}
)
NETWORK_EGRESS = frozenset(
    {
        "requests.get", "requests.post", "requests.put", "requests.patch",
        "requests.delete", "requests.request", "requests.head",
        "urllib.request.urlopen", "urllib.request.Request",
        "urllib.request.urlretrieve",
        "httpx.get", "httpx.post", "httpx.put", "httpx.request", "httpx.Client",
        "socket.socket", "socket.create_connection",
        "http.client.HTTPConnection", "http.client.HTTPSConnection",
        "smtplib.SMTP", "ftplib.FTP", "aiohttp.ClientSession",
    }
)
REFLECTION_BUILTINS = frozenset({"getattr", "setattr", "delattr"})

# Environment / credential read expressions (the exfiltration source).
ENV_READ_ATTRS = frozenset({"os.environ", "os.getenv", "os.getenvb"})

# Tainted-source call targets for the taint pass.
TAINT_SOURCES = frozenset(
    {"input", "os.getenv", "sys.stdin.read", "os.environ.get"}
)


def _attr_chain(node: ast.AST) -> str | None:
    """Return the dotted name for an attribute chain (``a.b.c``) or a name."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


class _Collector(ast.NodeVisitor):
    """Walk a module collecting import aliases and resolving call targets."""

    def __init__(self) -> None:
        self.aliases: dict[str, str] = {}
        self.from_imports: dict[str, str] = {}
        # (canonical_name, node) for every Call.
        self.calls: list[tuple[str, ast.Call]] = []
        self.env_reads: list[ast.AST] = []
        # Literal names of the env vars read (e.g. "PEXELS_API_KEY"), used to
        # decide whether a credential is a self-authenticating API key. Empty
        # when a read uses a non-literal / dynamic key (kept conservative: an
        # unresolved credential name cannot be shown to be self-authenticating).
        self.env_names: list[str] = []
        self.shell_true: list[ast.Call] = []
        # name -> kind for tainted assignments (module-scoped heuristic).
        self.tainted: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            target = alias.name if alias.asname else alias.name.split(".")[0]
            self.aliases[local] = target
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            local = alias.asname or alias.name
            self.from_imports[local] = f"{module}.{alias.name}" if module else alias.name
        self.generic_visit(node)

    def _resolve(self, func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            if func.id in self.from_imports:
                return self.from_imports[func.id]
            return func.id
        if isinstance(func, ast.Attribute):
            chain = _attr_chain(func)
            if not chain:
                return None
            root, _, rest = chain.partition(".")
            mapped = self.aliases.get(root)
            if mapped and rest:
                return f"{mapped}.{rest}"
            return chain
        return None

    def visit_Call(self, node: ast.Call) -> None:
        name = self._resolve(node.func)
        if name:
            self.calls.append((name, node))
            # Capture the literal env-var name for os.getenv("X") / os.environ.get("X").
            if name in {"os.getenv", "os.getenvb", "os.environ.get"} and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    self.env_names.append(first.value)
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                self.shell_true.append(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        chain = _attr_chain(node)
        if chain in ENV_READ_ATTRS:
            self.env_reads.append(node)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        chain = _attr_chain(node.value)
        if chain == "os.environ":
            self.env_reads.append(node)
            # Capture the literal key for os.environ["X"].
            key = node.slice
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                self.env_names.append(key.value)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._rhs_is_tainted(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted[target.id] = "external-input"
        self.generic_visit(node)

    def _rhs_is_tainted(self, value: ast.AST) -> bool:
        for sub in ast.walk(value):
            if isinstance(sub, ast.Call):
                name = self._resolve(sub.func)
                if name in TAINT_SOURCES:
                    return True
            if isinstance(sub, ast.Subscript):
                if _attr_chain(sub.value) == "os.environ":
                    return True
            if isinstance(sub, ast.Attribute):
                if _attr_chain(sub) in ENV_READ_ATTRS:
                    return True
        return False


def _call_uses_tainted(node: ast.Call, tainted: dict[str, str]) -> bool:
    for arg in list(node.args) + [kw.value for kw in node.keywords]:
        for sub in ast.walk(arg):
            if isinstance(sub, ast.Name) and sub.id in tainted:
                return True
    return False


class BehavioralASTAnalyzer:
    """Parses Python scripts and emits behavioral/taint/exfiltration findings."""

    name = "behavioral-ast"

    def analyze(self, unit: FileUnit) -> list[Finding]:
        if unit.suffix != ".py":
            return []
        try:
            tree = ast.parse(unit.text)
        except SyntaxError:
            # A skill script that does not parse cannot be statically analyzed
            # here; the text analyzers still cover it. Not an error.
            return []

        lines = unit.text.splitlines()
        collector = _Collector()
        collector.visit(tree)
        findings: list[Finding] = []

        def snippet_for(node: ast.AST) -> str:
            lineno = getattr(node, "lineno", 0)
            return lines[lineno - 1] if 0 < lineno <= len(lines) else ""

        has_network = False

        for name, node in collector.calls:
            line = getattr(node, "lineno", 0)
            snip = snippet_for(node)
            bare = name.rsplit(".", 1)[-1]

            if name in CODE_EXEC_BUILTINS:
                findings.append(make_finding(
                    detection_class=12, severity=Severity.CRITICAL,
                    title=f"Dynamic code execution: {name}()",
                    message=f"{name}() executes dynamically-constructed code -- the strongest behavioral signal of a malicious skill script.",
                    unit=unit, line=line, snippet=snip, analyzer=self.name,
                ))
            elif name in DYNAMIC_IMPORT:
                findings.append(make_finding(
                    detection_class=12, severity=Severity.MEDIUM,
                    title=f"Dynamic import: {name}",
                    message=f"{name} loads a module chosen at runtime -- can hide which code actually runs.",
                    unit=unit, line=line, snippet=snip, analyzer=self.name,
                ))
            elif name in PROCESS_EXEC:
                findings.append(make_finding(
                    detection_class=12, severity=Severity.MEDIUM,
                    title=f"Process execution: {name}",
                    message=f"{name} spawns an external process. Verify the command is a fixed argument list, not built from untrusted input.",
                    unit=unit, line=line, snippet=snip, analyzer=self.name,
                ))
            elif name in REFLECTIVE_LOAD:
                findings.append(make_finding(
                    detection_class=12, severity=Severity.MEDIUM,
                    title=f"Reflective code loading: {name}",
                    message=f"{name} deserializes/loads data into executable objects -- reflective code loading (T1620).",
                    unit=unit, line=line, snippet=snip, analyzer=self.name,
                ))
            elif name in NETWORK_EGRESS:
                has_network = True
                findings.append(make_finding(
                    detection_class=2, severity=Severity.MEDIUM,
                    title=f"Network egress: {name}",
                    message=f"{name} makes an outbound network call. Confirm what data leaves the machine and to where.",
                    unit=unit, line=line, snippet=snip, analyzer=self.name,
                ))
            elif bare in REFLECTION_BUILTINS and name in REFLECTION_BUILTINS:
                # getattr/setattr/delattr with a non-constant attribute name is
                # reflective manipulation; a constant name is ordinary access.
                if len(node.args) >= 2 and not isinstance(node.args[1], ast.Constant):
                    findings.append(make_finding(
                        detection_class=12, severity=Severity.LOW,
                        title=f"Reflective attribute access: {name}",
                        message=f"{name} resolves an attribute name at runtime -- reflection that can reach unexpected callables.",
                        unit=unit, line=line, snippet=snip, analyzer=self.name,
                    ))

        for node in collector.shell_true:
            line = getattr(node, "lineno", 0)
            findings.append(make_finding(
                detection_class=12, severity=Severity.MEDIUM,
                title="Subprocess with shell=True",
                message="shell=True runs the command through a shell, enabling injection if any argument is attacker-influenced.",
                unit=unit, line=line, snippet=snippet_for(node), analyzer=self.name,
            ))

        # Class 2 (executable): credential exfiltration = environment/credential
        # read + a network egress call in the same script. HIGH by default -- the
        # classic credential-harvesting-and-exfiltration signal. Refinement: a
        # legitimate API client reads its OWN key and calls THAT service, so when
        # every read credential's service token matches an egress host the script
        # calls, this is a self-authenticating API client, not exfiltration to an
        # unrelated host -- report it at MEDIUM (still visible, below the HIGH
        # gate) rather than HIGH. Any unmatched (or non-literal) credential keeps
        # the finding at HIGH.
        if has_network and collector.env_reads:
            env_node = collector.env_reads[0]
            line = getattr(env_node, "lineno", 0)
            host_tokens: set[str] = set()
            for host in _URL_HOST_RE.findall(unit.text):
                host_tokens |= _service_tokens(host)
            cred_token_sets = [_service_tokens(n) for n in collector.env_names]
            self_authenticating = (
                bool(cred_token_sets)
                and all(bool(ts & host_tokens) for ts in cred_token_sets)
            )
            if self_authenticating:
                matched = sorted({t for ts in cred_token_sets for t in (ts & host_tokens)})
                findings.append(make_finding(
                    detection_class=2, severity=Severity.MEDIUM,
                    title="Credential read + network egress (self-authenticating API client)",
                    message=(
                        "The script reads an environment credential and makes a network call, but the "
                        f"credential's service ({', '.join(matched)}) matches an egress host the script "
                        "calls -- it looks like an API client sending its own key to its own service, "
                        "not credential exfiltration to an unrelated host. Verify the key is used only "
                        "as authentication to that service."
                    ),
                    unit=unit, line=line, snippet=snippet_for(env_node), analyzer=self.name,
                ))
            else:
                findings.append(make_finding(
                    detection_class=2, severity=Severity.HIGH,
                    title="Credential exfiltration (env read + network egress)",
                    message="The script reads environment variables / credentials and also makes an outbound network call -- the classic credential-harvesting-and-exfiltration pattern.",
                    unit=unit, line=line, snippet=snippet_for(env_node), analyzer=self.name,
                ))

        # Class 13 (taint): a tainted source flowing into a dangerous sink.
        if collector.tainted:
            for name, node in collector.calls:
                if name in CODE_EXEC_BUILTINS and _call_uses_tainted(node, collector.tainted):
                    findings.append(make_finding(
                        detection_class=13, severity=Severity.HIGH,
                        title=f"Tainted input reaches {name}()",
                        message="External input flows into a dynamic code-execution sink -- a code-injection dataflow.",
                        unit=unit, line=getattr(node, "lineno", 0),
                        snippet=snippet_for(node), analyzer=self.name,
                    ))
                elif name in PROCESS_EXEC and _call_uses_tainted(node, collector.tainted):
                    findings.append(make_finding(
                        detection_class=13, severity=Severity.MEDIUM,
                        title=f"Tainted input reaches {name}",
                        message="External input flows into a process-execution sink -- verify the command cannot be hijacked.",
                        unit=unit, line=getattr(node, "lineno", 0),
                        snippet=snippet_for(node), analyzer=self.name,
                    ))

        return findings
