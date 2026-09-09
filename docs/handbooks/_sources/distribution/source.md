# How installation preserves ownership

## From installer to adapter

Both installer entry points prepare the bundle and invoke platform integration logic. The Python integration runner selects the requested platform and scope. A shared adapter translates the catalog into that platform's native file shape.

## Three delivery shapes

flatten_skills drops the catalog category level for hosts that read skills/name/SKILL.md. commands_to_skills creates skill-shaped command wrappers. commands_to_slash emits command files in the selected native style. The catalog stays organized for maintainers.

## Names remain unambiguous

The catalog adapter collects only directories that contain SKILL.md. A leftover empty directory therefore does not reserve a skill name and suppress a legitimate command wrapper. A real skill name takes precedence over a same-name synthesized wrapper.

## Generated and user-owned files differ

Owned-file writing consults the installation manifest. It can repair an artifact created by Nexus-Hub while preserving a file authored by the user. Some derived catalog materialization paths synchronize on byte difference and track their output; do not assume every copy path has identical overwrite behavior.

## Inspect outcomes, then test behavior

Adapters return file actions and track managed paths. Unchanged bytes can remain unchanged on a second run. Inspect reported actions and actual installed files, then exercise the capability in its host. A successful file copy alone is not proof of discovery or runtime behavior.
