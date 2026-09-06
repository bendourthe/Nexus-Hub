# OS Sandboxing Runbook

Kernel and container controls for [[agent-execution-isolation]]. This file is the layer-1 runbook. The skill body is the decision procedure; this page is the Linux baseline operators can copy and then adapt.

## Goal

Give each agent session a throwaway execution environment whose filesystem, syscalls, and network are narrower than the host, and whose lifetime ends with the session.

## Per-session ephemeral container

1. Start from a minimal image that contains only the agent runtime and the tools the task needs.
2. Create one container (or one nested sandbox) per session. Do not keep a shared "agent VM" that accumulates mounts, credentials, and leftover files.
3. At session end, stop and remove the container. Persist only artifacts the operator explicitly copied out.
4. Pass `--read-only` (or equivalent) on the root filesystem and give the agent a `tmpfs` or named volume for scratch.
5. Drop capabilities (`cap_drop=ALL`, then add back only what the runtime proves it needs). Set `no-new-privileges`.
6. Do not mount the host Docker/containerd socket. That socket is host privilege.
7. Do not use host networking. The agent should see a private network namespace whose default route is the egress proxy.

### Mount allowlist (default deny)

Mount only what the task names. Typical shape:

| Path class | Default | Exception rule |
|---|---|---|
| Task workspace | Read-write, bind-mount of that tree only | None |
| Agent runtime image | Read-only | None |
| `$HOME`, `.ssh`, `.aws`, `.config/gcloud`, `.azure` | Unmounted | Written exception, time-bounded, logged |
| Host credential files and browser profiles | Unmounted | Never for a general coding agent |
| Docker/containerd socket | Unmounted | Never; that is escape-to-host |
| Scratch | tmpfs | None |

An exception that is not written down is not an exception. It is a missed mount.

## Landlock (filesystem confinement)

Landlock is a Linux LSM that lets an unprivileged process restrict its own filesystem access after it has opened the paths it needs. Use it **inside** the container so a breakout from the agent process still cannot read unmounted-but-still-visible paths (proc overlays, leftover bind mounts, runtime sockets).

Baseline:

1. Identify the path set the agent must read and write (workspace + scratch).
2. Apply an ABI-compatible Landlock ruleset that allows read/write only on those trees and read-only on required system paths (`/usr`, `/lib`, `/etc/ssl`).
3. Deny everything else, including `/proc/sys`, host-like credential paths if they exist in the image, and the container runtime socket if it was accidentally mounted.
4. Probe: from inside the confined process, `open()` on an SSH private key path and on `/` outside the allowlist must fail.

If the host kernel is too old for Landlock, record that as accepted risk and tighten bind-mounts plus a read-only root. Do not silently skip filesystem confinement.

## seccomp (syscall filtering)

seccomp-bpf limits the syscall surface of the agent process.

Baseline:

1. Start from a known Docker/OCI default profile, then remove syscalls the agent runtime does not need (`mount`, `pivot_root`, `bpf`, `perf_event_open`, `userfaultfd`, unneeded socket families, `ptrace` unless a debugger is in scope).
2. Keep the profile in version control next to the container spec.
3. Fail closed: an unknown syscall is `SCMP_ACT_ERRNO` or kill, not allow.
4. Probe: a process inside the sandbox that calls a denied syscall must receive an error, not succeed.

seccomp is not a filesystem policy and not a network policy. It reduces the kernel attack surface after a payload is already running.

## Network namespace

Put the agent in a network namespace that does not share the host's interfaces.

1. The namespace has no path to the host LAN except through the egress proxy veth/bridge.
2. Default DNS inside the namespace points at a resolver the proxy or the operator controls, not at an agent-chosen server.
3. Block protocols other than the proxy's inbound port. Raw sockets stay denied (seccomp plus capabilities).
4. Probe: from the agent namespace, a direct connect to an RFC-1918 address and to a public IP on 443 both fail unless they go through the proxy.

## Combining the three

Order of application:

1. Create the ephemeral container with mount allowlist, read-only root, dropped caps, no host net, no runtime socket.
2. Enter the network namespace and point default egress at the proxy.
3. Start the agent process under seccomp.
4. In the agent process (or its launcher), apply Landlock last so the process cannot reopen denied paths.

A setup that does step 1 and skips 2-4 is a container, not the isolation this skill requires. Name the missing steps in the residual-risk section.

## Windows and macOS notes

- Linux kernel features (Landlock, seccomp, netns) are Linux-only. On Docker Desktop / WSL2 / a remote Linux builder, apply them in the Linux VM that actually runs the container.
- On a host that cannot provide those features, still use per-session containers, mount deny-by-default, no Docker socket, and the out-of-process egress proxy. Record the missing kernel filters as accepted risk rather than claiming equivalent isolation.

## Probes (binary)

- [ ] A new session produces a new container ID; destroying the session removes it.
- [ ] `ls` of an unmounted SSH directory from inside the agent fails.
- [ ] Opening a Landlock-denied path fails.
- [ ] A denied syscall fails.
- [ ] A direct (non-proxy) TCP connect from the agent namespace fails.
- [ ] The Docker socket is not present in the container.
