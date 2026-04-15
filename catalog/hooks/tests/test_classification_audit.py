"""Comprehensive audit of command classification edge cases.

Run with: python catalog/hooks/tests/test_classification_audit.py

Loads patterns from both installed settings (~/.claude/settings.json)
and the source permissions file (configs/permissions/claude-permissions.json)
so the audit works before re-running the installer.
"""
import json
import re
import sys
import importlib.util
import pathlib

# Load the hook module by path
spec = importlib.util.spec_from_file_location(
    "hook", "catalog/hooks/format-bash-description.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _load_source_patterns() -> list[str]:
    """Load patterns from the source permissions JSON (pre-install)."""
    source = pathlib.Path("configs/permissions/claude-permissions.json")
    if not source.is_file():
        return []
    data = json.loads(source.read_text(encoding="utf-8"))
    patterns: list[str] = []
    for entry in data.get("permissions", {}).get("allow", []):
        if isinstance(entry, str) and entry.startswith("Bash(") and entry.endswith(")"):
            inner = entry[5:-1]
            inner = re.sub(r"^([^:*\s]+):\*$", r"\1 *", inner)
            patterns.append(inner)
    return patterns


def main() -> None:
    # Merge installed patterns with source patterns (deduped)
    installed = mod.load_allow_patterns()
    source = _load_source_patterns()
    patterns = list(dict.fromkeys(installed + source))
    print(f"Loaded {len(patterns)} patterns ({len(installed)} installed + {len(source)} source, {len(patterns)} unique)\n")

    # Format: (command, expected_auto_approve, category, description)
    cases = [
        # ── User-reported mislabeled commands ──
        ("cd /c/Users/bdour/Downloads/installer && find . -type f -o -type d | head -100", True, "REPORTED", "compound: cd + find + head via && and |"),
        ("head -50 /c/Users/bdour/Documents/Work/Coding/Github/Gemma-Code/src/tools/ToolCatalog.ts", True, "REPORTED", "simple head with long path"),
        ("git -C /c/Users/bdour/Documents/Work/Coding/Github/Gemma-Code tag", True, "REPORTED", "git with -C global option before subcommand"),

        # ── Git global options before subcommand ──
        ("git -C /some/repo log --oneline -5", True, "GIT-GLOBAL", "git -C before log"),
        ("git -C /some/repo status", True, "GIT-GLOBAL", "git -C before status"),
        ("git -C /some/repo diff HEAD~1", True, "GIT-GLOBAL", "git -C before diff"),
        ("git -C /some/repo branch -a", True, "GIT-GLOBAL", "git -C before branch"),
        ("git -C /some/repo remote -v", True, "GIT-GLOBAL", "git -C before remote"),
        ("git -C /some/repo tag", True, "GIT-GLOBAL", "git -C before tag (no args)"),
        ("git -C /some/repo tag -l", True, "GIT-GLOBAL", "git -C before tag -l"),
        ("git --git-dir=/some/.git log -3", True, "GIT-GLOBAL", "git --git-dir before log"),
        ("git --work-tree=/some/dir status", True, "GIT-GLOBAL", "git --work-tree before status"),
        ("git --no-pager log -5", True, "GIT-GLOBAL", "git --no-pager before log"),
        ("git --no-pager diff", True, "GIT-GLOBAL", "git --no-pager before diff"),
        ("git --no-pager blame file.ts", True, "GIT-GLOBAL", "git --no-pager before blame"),
        ("git -c color.ui=always log -5", True, "GIT-GLOBAL", "git -c key=val before log"),
        ("git -C /repo -c core.pager=cat log", True, "GIT-GLOBAL", "git -C and -c stacked before log"),
        ("git --no-pager -C /repo diff --stat", True, "GIT-GLOBAL", "stacked --no-pager -C before diff"),
        ("git -C /some/repo push origin main", False, "GIT-GLOBAL", "git -C before push (SHOULD block)"),
        ("git -C /some/repo reset --hard", False, "GIT-GLOBAL", "git -C before reset --hard (SHOULD block)"),
        ("git --no-pager commit -m 'test'", False, "GIT-GLOBAL", "git --no-pager before commit (SHOULD block)"),

        # ── Full-path binary invocations ──
        ("/usr/bin/head -20 file.txt", True, "FULLPATH", "absolute path to head"),
        ("/usr/bin/git log -5", True, "FULLPATH", "absolute path to git log"),
        ("/usr/local/bin/rg pattern .", True, "FULLPATH", "absolute path to rg"),
        ("/bin/cat /etc/hosts", True, "FULLPATH", "absolute path to cat"),
        ("/usr/bin/find . -name '*.py'", True, "FULLPATH", "absolute path to find"),
        ("/usr/bin/wc -l file.txt", True, "FULLPATH", "absolute path to wc"),
        ("/usr/bin/diff file1.txt file2.txt", True, "FULLPATH", "absolute path to diff"),

        # ── env/command/exec wrappers ──
        ("env git log -5", True, "WRAPPER", "env prefix before git"),
        ("env TERM=dumb git diff", True, "WRAPPER", "env with VAR=val before git"),
        ("env -i PATH=/usr/bin head file.txt", True, "WRAPPER", "env -i before head"),
        ("command git status", True, "WRAPPER", "command prefix before git"),

        # ── Compound commands ──
        ("git log --oneline | head -20", True, "COMPOUND", "git log piped to head"),
        ("git diff --stat | grep changed", True, "COMPOUND", "git diff piped to grep"),
        ("cd /tmp && ls -la", True, "COMPOUND", "cd && ls"),
        ("find . -name '*.ts' | sort | uniq", True, "COMPOUND", "find | sort | uniq triple pipe"),
        ("git branch -a | grep feature | wc -l", True, "COMPOUND", "triple pipe all read-only git"),
        ("git status; git diff --stat", True, "COMPOUND", "semicolon-separated read-only"),
        ("ls -la || echo none", True, "COMPOUND", "ls with fallback echo"),
        ("cat file1.txt && cat file2.txt | head -10", True, "COMPOUND", "cat && cat | head"),
        ("cd /project && git log --oneline -5 && git status", True, "COMPOUND", "cd && git log && git status"),
        ("ls -la && wc -l *.py && echo done", True, "COMPOUND", "three safe commands chained"),
        ("git log --oneline | grep fix | sort | uniq -c | sort -rn | head -5", True, "COMPOUND", "long pipeline all read-only"),

        # ── Stderr redirections ──
        ("git describe --tags 2>/dev/null", True, "REDIRECT", "stderr to /dev/null"),
        ("git log -1 2>&1", True, "REDIRECT", "stderr merged to stdout"),
        ("find . -name '*.py' 2>/dev/null | head", True, "REDIRECT", "find with stderr suppressed"),
        ("cat file.txt > output.txt", False, "REDIRECT", "stdout redirect to file (WRITE!)"),
        ("echo test >> log.txt", False, "REDIRECT", "stdout append to file (WRITE!)"),

        # ── Agent-internal writes (safe — agent's own workspace) ──
        ("cat > /home/user/.claude/plans/plan.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude plan file (Linux)"),
        ("cat > /Users/user/.claude/plans/plan.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude plan file (macOS)"),
        ("cat > /c/Users/user/.claude/plans/plan.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude plan file (Windows Git Bash)"),
        ("cat > /home/user/.claude/memory/note.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude memory file (Linux)"),
        ("cat > /home/user/.claude/projects/abc123/memory/mem.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude project memory (Linux)"),
        ("cat > .claude/plans/plan.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude plan file (relative path)"),
        ("cat > .claude/memory/note.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Claude memory file (relative)"),
        ("cat > /home/user/.gemini/memory/note.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Gemini memory file"),
        ("cat > /home/user/.codex/memory/note.md << 'EOF'\ncontent\nEOF", True, "AGENT-WRITE", "Codex memory file"),
        ("cat > /home/user/.claude/settings.json << 'EOF'\n{}\nEOF", False, "AGENT-WRITE", "Claude settings (NOT safe)"),
        ("cat > /home/user/.claude/hooks/hook.sh << 'EOF'\n#!/bin/bash\nEOF", False, "AGENT-WRITE", "Claude hooks (NOT safe)"),
        ("echo secret > /tmp/output.txt", False, "AGENT-WRITE", "regular file write (NOT safe)"),

        # ── macOS read-only commands ──
        ("sw_vers", True, "MACOS", "macOS version info"),
        ("sw_vers -productVersion", True, "MACOS", "macOS product version"),
        ("xcode-select -p", True, "MACOS", "Xcode path"),
        ("xcrun --find clang", True, "MACOS", "xcrun find tool"),
        ("mdfind -name README.md", True, "MACOS", "Spotlight file search"),
        ("defaults read com.apple.Terminal", True, "MACOS", "defaults read (read-only)"),
        ("system_profiler SPHardwareDataType", True, "MACOS", "system profiler"),
        ("sysctl -n machdep.cpu.brand_string", True, "MACOS", "sysctl read CPU info"),
        ("pbpaste", True, "MACOS", "read clipboard"),
        ("plutil -p Info.plist", True, "MACOS", "plist reader"),
        ("mdls file.pdf", True, "MACOS", "Spotlight metadata"),
        ("otool -L /usr/bin/git", True, "MACOS", "dynamic lib dependencies"),
        ("open https://github.com", False, "MACOS", "open launches external app"),
        ("defaults write com.apple.Finder AppleShowAllFiles true", False, "MACOS", "defaults write MUTATES"),
        ("launchctl load /Library/LaunchDaemons/foo.plist", False, "MACOS", "launchctl load MUTATES"),
        ("pkill -f myprocess", False, "MACOS", "pkill is MUTATING"),
        ("brew install jq", False, "MACOS", "brew install MUTATES"),

        # ── Linux read-only commands ──
        ("lsb_release -a", True, "LINUX", "distro info"),
        ("cat /etc/os-release", True, "LINUX", "OS release via cat"),
        ("free -h", True, "LINUX", "memory info"),
        ("lscpu", True, "LINUX", "CPU info"),
        ("ip addr show", True, "LINUX", "network interfaces"),
        ("ss -tlnp", True, "LINUX", "listening ports"),
        ("systemctl status nginx", True, "LINUX", "service status read-only"),
        ("journalctl -n 50 --no-pager", True, "LINUX", "journal entries"),
        ("dpkg -l | grep python", True, "LINUX", "dpkg list piped to grep"),
        ("rpm -qa | grep python", True, "LINUX", "rpm list piped to grep"),
        ("apt list --installed 2>/dev/null | head", True, "LINUX", "apt list read-only"),
        ("getent passwd", True, "LINUX", "passwd database read"),
        ("nproc", True, "LINUX", "number of processors"),
        ("lsblk", True, "LINUX", "block device list"),
        ("lsof -i :8080", True, "LINUX", "list open files on port"),
        ("systemctl restart nginx", False, "LINUX", "restart service MUTATES"),
        ("apt install python3", False, "LINUX", "apt install MUTATES"),
        ("iptables -L", False, "LINUX", "iptables requires root and is sensitive"),
        ("useradd testuser", False, "LINUX", "add user MUTATES"),

        # ── Package manager read-only ──
        ("npm list --depth=0", True, "PKG-RO", "npm list"),
        ("npm ls --all", True, "PKG-RO", "npm ls"),
        ("npm outdated", True, "PKG-RO", "npm outdated"),
        ("npm view react version", True, "PKG-RO", "npm view"),
        ("npm --version", True, "PKG-RO", "npm version check"),
        ("npm pack --dry-run", True, "PKG-RO", "npm dry-run"),
        ("yarn list --depth=0", True, "PKG-RO", "yarn list"),
        ("pnpm list", True, "PKG-RO", "pnpm list"),
        ("pip list", True, "PKG-RO", "pip list"),
        ("pip show requests", True, "PKG-RO", "pip show"),
        ("pip freeze", True, "PKG-RO", "pip freeze"),
        ("python --version", True, "PKG-RO", "python version"),
        ("python3 --version", True, "PKG-RO", "python3 version"),
        ("node --version", True, "PKG-RO", "node version"),
        ("go version", True, "PKG-RO", "go version"),
        ("go env", True, "PKG-RO", "go env"),
        ("rustc --version", True, "PKG-RO", "rustc version"),
        ("cargo --version", True, "PKG-RO", "cargo version"),
        ("dotnet --version", True, "PKG-RO", "dotnet version"),
        ("dotnet --list-sdks", True, "PKG-RO", "dotnet list SDKs"),
        ("java -version", True, "PKG-RO", "java version"),
        ("mvn --version", True, "PKG-RO", "maven version"),
        ("gradle --version", True, "PKG-RO", "gradle version"),

        # ── Docker/container read-only ──
        ("docker ps", True, "DOCKER", "list running containers"),
        ("docker ps -a", True, "DOCKER", "list all containers"),
        ("docker images", True, "DOCKER", "list images"),
        ("docker logs mycontainer", True, "DOCKER", "view container logs"),
        ("docker inspect mycontainer", True, "DOCKER", "inspect container"),
        ("docker version", True, "DOCKER", "docker version"),
        ("docker compose config", True, "DOCKER", "validate compose file"),
        ("docker network ls", True, "DOCKER", "list networks"),
        ("docker volume ls", True, "DOCKER", "list volumes"),
        ("docker run --rm alpine echo hello", False, "DOCKER", "run container (side effect)"),
        ("docker rm mycontainer", False, "DOCKER", "remove container MUTATES"),
        ("docker build .", False, "DOCKER", "build image MUTATES"),

        # ── GitHub CLI read-only ──
        ("gh pr list", True, "GH-CLI", "list PRs"),
        ("gh pr view 123", True, "GH-CLI", "view single PR"),
        ("gh pr checks 123", True, "GH-CLI", "view PR checks"),
        ("gh issue list", True, "GH-CLI", "list issues"),
        ("gh issue view 456", True, "GH-CLI", "view single issue"),
        ("gh repo view", True, "GH-CLI", "view repo info"),
        ("gh api repos/owner/repo", True, "GH-CLI", "read-only API call"),
        ("gh run list", True, "GH-CLI", "list workflow runs"),
        ("gh run view 789", True, "GH-CLI", "view workflow run"),
        ("gh release list", True, "GH-CLI", "list releases"),
        ("gh pr create --title test", False, "GH-CLI", "create PR MUTATES"),
        ("gh issue create --title bug", False, "GH-CLI", "create issue MUTATES"),

        # ── Windows/Git Bash paths ──
        ("cat /c/Users/bdour/.gitconfig", True, "WINDOWS", "cat with /c/ path"),
        ("ls /c/Users/bdour/Documents", True, "WINDOWS", "ls with /c/ path"),
        ("find /c/Users/bdour -name '*.md' -maxdepth 2", True, "WINDOWS", "find with /c/ root"),
        ("wc -l /c/Users/bdour/Documents/file.txt", True, "WINDOWS", "wc with /c/ path"),
        ("head -100 /c/Users/bdour/file.log", True, "WINDOWS", "head with /c/ path"),

        # ── Prefix commands ──
        ("time git log --oneline -10", True, "PREFIX", "time prefix on git log"),
        ("nice -n 19 find . -name '*.py'", True, "PREFIX", "nice prefix on find"),
        ("timeout 30 curl -s http://example.com", False, "PREFIX", "timeout + curl (network)"),

        # ── Subshells and grouping ──
        ("(cd /tmp && ls)", True, "SUBSHELL", "subshell cd + ls"),
        ("(git log -5; git status)", True, "SUBSHELL", "subshell read-only git"),

        # ── Commands NOT in allowlist (should require approval) ──
        ("npm install", False, "MUTATING", "npm install"),
        ("pip install requests", False, "MUTATING", "pip install"),
        ("rm -rf node_modules", False, "MUTATING", "rm -rf"),
        ("curl -X POST http://api.example.com", False, "MUTATING", "curl POST"),
        ("chmod 755 script.sh", False, "MUTATING", "chmod"),
        ("chown user:group file.txt", False, "MUTATING", "chown"),
        ("kill -9 1234", False, "MUTATING", "kill process"),
        ("git push origin main", False, "MUTATING", "git push"),
        ("git commit -m 'test'", False, "MUTATING", "git commit"),
        ("git checkout -b new-branch", False, "MUTATING", "git checkout -b"),
        ("mv file1.txt file2.txt", False, "MUTATING", "mv renames"),
        ("cp -r src dest", False, "MUTATING", "cp is a write op"),
        ("mkdir -p new_dir", False, "MUTATING", "mkdir creates directories"),
        ("touch new_file.txt", False, "MUTATING", "touch creates/modifies files"),
        ("wget http://example.com/file.zip", False, "MUTATING", "wget downloads"),
        ("curl -o file.zip http://example.com/file.zip", False, "MUTATING", "curl download"),
        ("ssh user@host", False, "MUTATING", "ssh remote access"),
        ("scp file.txt user@host:/tmp/", False, "MUTATING", "scp remote copy"),
        ("eval 'rm -rf /'", False, "MUTATING", "eval is dangerous"),
    ]

    # Run all tests
    pass_count = 0
    fail_count = 0
    false_rejects = []
    false_accepts = []

    for cmd, expected, category, desc in cases:
        actual = mod.command_is_allowed(cmd, patterns)
        if actual == expected:
            pass_count += 1
        else:
            fail_count += 1
            entry = (category, cmd, desc)
            if actual and not expected:
                false_accepts.append(entry)
            else:
                false_rejects.append(entry)

    print(f"RESULTS: {pass_count} pass, {fail_count} fail out of {len(cases)} total\n")

    if false_rejects:
        print(f"--- FALSE REJECTS: should auto-approve but BLOCKED ({len(false_rejects)}) ---")
        for cat, cmd, desc in false_rejects:
            print(f"  [{cat:12s}] {desc}")
            print(f"               cmd: {cmd}")
        print()

    if false_accepts:
        print(f"--- FALSE ACCEPTS: should block but AUTO-APPROVED ({len(false_accepts)}) ---")
        for cat, cmd, desc in false_accepts:
            print(f"  [{cat:12s}] {desc}")
            print(f"               cmd: {cmd}")
        print()

    if not false_rejects and not false_accepts:
        print("All tests passed!")

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
