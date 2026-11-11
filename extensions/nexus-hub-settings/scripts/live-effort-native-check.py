"""Exercise live effort through the compiled relay without sending a model prompt."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from nexus_process import install_no_window_default

install_no_window_default()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--claude", type=Path, required=True)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--models-cache", type=Path, required=True)
    parser.add_argument("--windows-launcher", action="store_true")
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    proxy = Path(__file__).resolve().parents[1] / "out/liveEffortProxy.js"
    node = shutil.which("node")
    assert node and proxy.is_file()
    models_snapshot = work / "models-cache.json"
    models_snapshot.write_bytes(args.models_cache.read_bytes())
    json.loads(models_snapshot.read_text(encoding="utf-8"))
    launcher = None
    if args.windows_launcher:
        assert os.name == "nt"
        launcher = work / "launcher.exe"
        compiler = Path(os.environ.get("SystemRoot", "C:/Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        subprocess.run([str(compiler), "/nologo", "/target:exe", "/optimize+", "/r:System.Web.Extensions.dll", f"/out:{launcher}", str(proxy.parents[1] / "media/effort-launcher.cs")], capture_output=True, check=True, creationflags=0x08000000)
    report: dict = {"model_turns": 0, "clients": {}}
    for provider, binary in (("claude", args.claude), ("codex", args.codex)):
        root = work / provider
        (root / ".claude").mkdir(parents=True)
        (root / ".codex").mkdir()
        (root / ".claude/settings.json").write_text(json.dumps({"model": "opus", "env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}}), encoding="utf-8")
        preference = root / "preferences.json"
        preference.write_text('{"default_effort":"medium"}', encoding="utf-8")
        config = root / "bridge.json"
        config.write_text(json.dumps({"provider": provider, "target": str(binary.resolve()), "preferences": str(preference), "statusDirectory": str(root / "status"), "modelsCache": str(models_snapshot), "runtime": node, "script": str(proxy)}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items() if not key.upper().startswith(("CLAUDE", "ANTHROPIC", "CODEX", "NEXUS", "OPENAI", "ELECTRON"))}
        env.update(HOME=str(root), USERPROFILE=str(root), CLAUDE_CONFIG_DIR=str(root / ".claude"), CODEX_HOME=str(root / ".codex"), ANTHROPIC_API_KEY="local-test-not-a-credential", ANTHROPIC_BASE_URL="http://127.0.0.1:9", OPENAI_API_KEY="local-test-not-a-credential", OPENAI_BASE_URL="http://127.0.0.1:9", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
        native_args = [str(binary), "--print", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--setting-sources", "user"] if provider == "claude" else ["app-server", "-c", 'openai_base_url="http://127.0.0.1:9"']
        if launcher:
            shutil.copyfile(launcher, root / "bridge.exe")
        command = [str(root / "bridge.exe"), *native_args] if launcher else [node, str(proxy), str(config), *native_args]
        process = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", creationflags=0x08000000 if os.name == "nt" else 0)
        incoming: queue.Queue = queue.Queue()
        observed: list = []
        errors: list = []

        def read_output() -> None:
            assert process.stdout
            for line in process.stdout:
                try:
                    packet = json.loads(line)
                except ValueError:
                    continue
                if packet.get("method") == "thread/settings/updated":
                    observed.append({key: packet["params"]["threadSettings"].get(key) for key in ("effort", "model")})
                incoming.put(packet)

        def read_errors() -> None:
            assert process.stderr
            for line in process.stderr:
                if len(errors) < 12:
                    errors.append(line[:200])

        threading.Thread(target=read_output, daemon=True).start()
        threading.Thread(target=read_errors, daemon=True).start()

        def request(identifier: int, method: str, params: dict) -> dict:
            packet = {"type": "control_request", "request_id": str(identifier), "request": {"subtype": method, **params}} if provider == "claude" else {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
            assert process.stdin
            process.stdin.write(json.dumps(packet) + "\n")
            process.stdin.flush()
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    result = incoming.get(timeout=.25)
                except queue.Empty:
                    assert process.poll() is None, errors
                    continue
                matched = result.get("response", {}).get("request_id") == str(identifier) if provider == "claude" else result.get("id") == identifier
                if matched:
                    assert not result.get("error"), result
                    assert result.get("response", {}).get("subtype") != "error", result
                    return result
            raise AssertionError(f"{provider}: timeout on {method}: {errors}")

        results: list = []
        state: dict = {}
        try:
            if provider == "claude":
                request(1, "initialize", {"hooks": {}, "sdkMcpServers": []})
            else:
                request(1, "initialize", {"clientInfo": {"name": "nexus-live-effort-proof", "version": "1"}, "capabilities": {"experimentalApi": True}})
                assert process.stdin
                process.stdin.write('{"jsonrpc":"2.0","method":"initialized","params":{}}\n')
                process.stdin.flush()
                started = request(2, "thread/start", {"model": "gpt-6.1-sol", "cwd": str(root), "ephemeral": False, "approvalPolicy": "never", "sandbox": "read-only", "config": {"model_reasoning_effort": "low"}})
                assert started["result"]["reasoningEffort"] == "medium", started
            for index, level in enumerate(("low", "medium", "high", "xhigh", "max", "ultra"), 10):
                preference.write_text(json.dumps({"default_effort": level}), encoding="utf-8")
                deadline = time.monotonic() + 10
                state = {}
                while time.monotonic() < deadline:
                    for status in (root / "status").glob("*.json"):
                        try:
                            state = json.loads(status.read_text(encoding="utf-8"))
                        except ValueError:
                            continue
                    if state.get("requested") == level and state.get("applied"):
                        break
                    time.sleep(.05)
                if not (state.get("requested") == level and state.get("applied")):
                    actual = request(index, "get_settings", {})["response"]["response"]["applied"] if provider == "claude" else {}
                    raise AssertionError((provider, level, state, {key: actual.get(key) for key in ("effort", "ultracode")}, observed, errors))
                if provider == "claude":
                    applied = request(index, "get_settings", {})["response"]["response"]["applied"]
                    expected = "xhigh" if level == "ultra" else level
                    assert applied["effort"] == expected and applied["ultracode"] is (level == "ultra"), applied
                    results.append({"requested": level, "effort": applied["effort"], "ultracode": applied["ultracode"]})
                else:
                    assert observed[-1]["effort"] == level, observed
                    results.append({"requested": level, "notification": observed[-1], "mapped": state.get("mapped")})
            report["clients"][provider] = results
        finally:
            assert process.stdin
            process.stdin.close()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
            (root / "diagnostic.json").write_text(json.dumps({"results": results, "state": state if "state" in locals() else {}, "stderr": errors}, indent=2), encoding="utf-8")
    (work / "native-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": "pass", "clients": len(report["clients"]), "live_changes": sum(len(value) for value in report["clients"].values()), "model_turns": 0, "report": str(work / "native-report.json")}))


if __name__ == "__main__":
    main()
