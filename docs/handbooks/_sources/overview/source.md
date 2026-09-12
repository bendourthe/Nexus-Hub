# Nexus-Hub: from catalog to assistant

## One catalog, several hosts

Nexus-Hub stores reusable skills, commands, hooks and rules. Installers deliver those files into the local bundle and each supported assistant's configuration. The catalog is the upstream source; generated platform files are delivery artifacts.

## Start with the skill source

Each skill lives under catalog/skills/category/name/SKILL.md. Its frontmatter identifies and describes the capability; its body supplies the procedure. References, scripts and assets remain beside the skill so supporting material can be loaded when needed.

## Check before distribution

scripts/validate_skills.py validates required frontmatter, strict YAML parsing, directory/name agreement and body conventions. The registry checker compares catalog entries with source metadata. Passing these checks establishes structure, not that an assistant selected or followed the skill.

## Adapt the shape at the boundary

The platform adapters can flatten category folders, synthesize commands as skills, or emit native slash-command files. A synthesized command retains its body and declares disable-model-invocation: true. The host decides whether it honors that field.

## Test the delivered capability

A source-file test cannot prove installation. Exercise the installed artifact through the intended host, retaining the observed result. This handbook's build receipt proves its current source and output hashes; its browser record covers the reading and presentation views.
