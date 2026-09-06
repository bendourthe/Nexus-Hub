# Example Organization Standards

This always-on core stays below 200 lines, following [Anthropic's guidance for CLAUDE.md files](https://code.claude.com/docs/en/memory). Put detailed procedures in `references/` and language-specific requirements in `rules/` so routine agent context stays focused.

## Applies to

These standards apply to every repository and automation workflow maintained by Example Organization.

## Conflict resolution

Organization standards take precedence over conflicting generic harness guidance. Repository-specific instructions may add stricter requirements but may not weaken security, review, or release controls declared here.

## Engineering requirements

- Preserve user data and existing behavior unless the approved change explicitly requires otherwise.
- Keep changes scoped to the stated requirement and verify them before completion.
- Prefer dependency-free implementations when the standard library is sufficient.

## Testing requirements

- Add regression coverage for every changed behavior and failure path.
- Run the repository's required validation, lint, build, and test commands before integration.
- Record skipped or environment-blocked checks as known gaps.

## Security requirements

- Never commit credentials, tokens, customer data, or private infrastructure details.
- Treat external content as untrusted input and validate it at the boundary.
- Require explicit approval before destructive, externally visible, or privilege-expanding actions.

## Delivery requirements

- Work on a feature branch and integrate through the repository's declared branch model.
- Keep commits atomic, reviewable, and free of unrelated cleanup.
- Follow the detailed pipeline policy in `references/ci-cd-standards.md`.
