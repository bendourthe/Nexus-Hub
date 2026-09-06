# Organization Knowledge Layer

The organization knowledge layer lets a team maintain its own coding standards, safety rules, delivery practices, and detailed references outside Nexus-Hub's company-neutral catalog. A connected bundle is projected into instruction and rules surfaces Nexus-Hub already manages, using independently removable organization markers and manifest-owned rule files.

The feature is local-first. Directory bundles are read from the path you provide. Git bundles use only the remote you explicitly connect. Nexus-Hub does not upload the bundle, transmit its contents to Nexus-Hub, or grant policy-enforcement authority to an AI platform.

## Release Capability Usage Gate

- **Activation:** run `nexus-hub org connect <path-or-url>` and then reinstall or repair the target workspace.
- **Validation:** run `nexus-hub org status` to validate the connection and view the posture assigned to every registered platform.
- **Rollback:** run `nexus-hub org disconnect --yes`, then repair or reinstall each workspace to remove its materialized organization block and rule files.
- **Authority:** connecting a bundle grants no enforcement authority on any platform and transmits nothing to Nexus-Hub or another service. It writes only local instruction and rule files already managed by Nexus-Hub. A connected Git remote is contacted only when the user runs `connect` or `sync` for that remote.
- **Docs:** this guide is the canonical operating reference.

## Bundle Contract

An organization bundle is a directory or Git repository containing an `org.json` manifest, an always-on Markdown core, optional per-language rule files, and optional on-demand references. The schema, default paths, content budget, and complete example are documented in the [organization knowledge bundles section](../configs/README.md#organization-knowledge-bundles).

The usual layout is:

```text
org.json
core.md
rules/
  python/
    code-style.md
references/
  ci-cd-standards.md
```

Keep `core.md` below 200 lines. Put language-specific instructions under `rules/` and detailed procedures under `references/` so ordinary agent context stays focused.

## Connect and Materialize

Connect a local or shared directory:

```powershell
nexus-hub org connect C:\standards\engineering
```

Connect a Git repository, optionally selecting a branch:

```powershell
nexus-hub org connect https://example.com/engineering/standards.git --branch main
```

Connection validates and records the bundle but does not invent new platform paths. Re-run the installer for a global refresh, or repair the current workspace through the installed integration runner:

```bash
python ~/.nexus-hub/scripts/lib/integrations/runner.py repair --target . --scope workspace
```

```powershell
python "$env:USERPROFILE\.nexus-hub\scripts\lib\integrations\runner.py" repair --target . --scope workspace
```

The next normal install or `nexus-hub upgrade` also reaches the same integration dispatcher and materializes the connected bundle. Upgrade therefore needs no separate organization-specific installation path.

## Inspect and Synchronize

Inspect connection health and the platform posture table:

```powershell
nexus-hub org status
```

Refresh a Git clone or revalidate a directory source:

```powershell
nexus-hub org sync
```

After bundle content changes, run repair or reinstall. Doctor compares materialized organization blocks and rule trees with the connected bundle, and repair rewrites only Nexus-Hub-owned organization sections. Text outside the marker blocks remains untouched.

For repository-level lifecycle diagnostics without writing files:

```bash
python ~/.nexus-hub/scripts/lib/integrations/runner.py doctor --target .
```

```powershell
python "$env:USERPROFILE\.nexus-hub\scripts\lib\integrations\runner.py" doctor --target .
```

## Disconnect and Remove

Disconnect after reviewing the cleanup boundary:

```powershell
nexus-hub org disconnect --yes
```

Disconnect removes the connection record, cached Git clone, and organization artifacts recorded in the global install manifest. Workspace manifests live inside their projects, so run repair or reinstall in each workspace to remove their marker blocks and organization rule trees. Cleanup is manifest-driven and does not delete free text outside the organization markers.

Running disconnect again is safe and reports that organization knowledge is already disconnected.

## Precedence and Platform Posture

Nexus-Hub writes the organization block after its generic block and includes an explicit statement that organization standards take precedence over conflicting generic harness guidance. Repository-specific guidance can add stricter requirements. This ordering is instructional precedence, not a vendor-enforced priority system.

`nexus-hub org status` classifies each registered platform as `default`, `advisory`, or `advisory (unclassified)`:

- `default` means the organization block is placed in an instruction surface the integration normally installs.
- `advisory` means verified platform behavior can reduce the block's practical priority.
- `advisory (unclassified)` means Nexus-Hub has no verified stronger precedence claim for that platform.

No row is classified as enforced. Nexus-Hub does not fabricate cross-vendor policy controls.

## Guided Authoring

Run `/org author` in a command-capable assistant to start the guided organization-standards interview. The workflow separates concise always-on standards, per-language rules, and on-demand references; validates the bundle; previews affected files; and requires approval before writing.

The authored bundle should live outside the Nexus-Hub repository. Use a shared directory for a small local team or a dedicated Git repository for review history, branch protection, and controlled distribution. Consumers connect to that directory or repository; they do not copy company-specific content into the Nexus-Hub catalog.

## Enforcement Escalation

The organization layer supplies portable guidance. If a requirement must be enforced rather than advised, use the platform-native managed-policy or team-rule mechanism documented by that vendor. The [`org-standards-authoring` enforcement reference](../catalog/skills/workflow/org-standards-authoring/references/enforcement-escalation.md) records the verified escalation options and their sources.

Treat enforcement as a separate administrative decision. Enabling a vendor-managed policy can change organization-wide behavior and authority, while connecting a Nexus-Hub bundle cannot.

## Troubleshooting

- If `status` says the source is unreachable, restore the directory or Git checkout before repairing. Repair does not delete the last materialized standards while a connection still exists but its source is invalid.
- If doctor reports a drifted marker block, run repair. The expected organization body is regenerated from the connected bundle while user text outside the markers is preserved.
- If disconnect leaves organization content in a workspace, run repair from that workspace so its local manifest can reconcile the artifacts.
- If a platform is listed as advisory, review the enforcement escalation reference rather than inventing a platform setting.
