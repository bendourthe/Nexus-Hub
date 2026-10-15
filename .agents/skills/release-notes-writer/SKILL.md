---
name: release-notes-writer
description: Generates professional release notes from git history, pull requests, and issues with conventional commit parsing and audience-specific formatting. Use when preparing release notes, changelogs, or version summaries for any audience.
summary_l0: "Generate release notes from git history with conventional commit parsing and formatting"
overview_l1: "This skill generates clear, well-structured release notes from repository history by parsing conventional commits, categorizing pull requests, highlighting breaking changes, and formatting output for different audiences (end users, developers, internal stakeholders). Use it when preparing release notes, changelogs, or version summaries, automating release documentation in CI/CD pipelines, or communicating changes to specific audiences. Key capabilities include conventional commit parsing, pull request categorization, breaking change highlighting, audience-specific formatting (user-facing, developer, internal), machine-parseable changelog generation, and CI/CD automation scripts for fully automated release documentation. The expected output is professionally formatted release notes with categorized changes, breaking change callouts, and audience-appropriate language. Trigger phrases: release notes, changelog, version summary, what changed, breaking changes, release documentation, conventional commits, version release."
---

# Release Notes Writer

Specialized skill for generating clear, well-structured release notes from repository history. This skill parses conventional commits, categorizes pull requests, highlights breaking changes, and formats the output for different audiences (end users, developers, internal stakeholders). It produces both human-readable release notes and machine-parseable changelogs, and includes automation scripts that can be integrated into CI/CD pipelines for fully automated release documentation.

## When to Use This Skill

Use this skill for:

- Generating release notes for a new version from git history and merged PRs
- Creating changelogs that follow the Keep a Changelog format
- Parsing conventional commits to automatically categorize changes
- Highlighting breaking changes and migration instructions for consumers
- Producing audience-specific release notes (user-facing versus internal/developer)
- Automating release note generation as part of a CI/CD pipeline
- Summarizing changes across multiple repositories for a platform release
- Formatting release notes for GitHub Releases, GitLab Releases, or documentation sites

**Trigger phrases**: "release notes", "changelog", "version notes", "what changed", "write release notes", "generate changelog", "release summary", "breaking changes", "version history", "release documentation"

## What This Skill Does

This skill follows a structured methodology to produce release notes:

1. **History Collection**: Gathers all commits, merged pull requests, and linked issues between two git references (tags, branches, or SHAs).

2. **Conventional Commit Parsing**: Parses commit messages following the Conventional Commits specification to extract type (feat, fix, chore, etc.), scope, description, breaking change markers, and issue references.

3. **PR Categorization**: Groups pull requests by label, conventional commit type, or directory path into user-meaningful categories (Features, Bug Fixes, Performance, Documentation, Internal).

4. **Breaking Change Detection**: Identifies breaking changes from commit footers (`BREAKING CHANGE:`), PR labels (`breaking-change`), and major version bumps in dependency updates.

5. **Audience Filtering**: Separates user-facing changes from internal changes. End users see features and bug fixes; developers see API changes and deprecations; internal stakeholders see all changes with contributor attribution.

6. **Output Generation**: Produces formatted release notes in Markdown (for GitHub/GitLab Releases), plain text (for email), or structured data (JSON/YAML for further processing).

## Instructions

### Step 1: Collect Change History

Full walkthrough: [step-1-collect-change-history.md](references/step-1-collect-change-history.md) (load this step when you reach it).

### Step 2: Parse Conventional Commits

Full walkthrough: [step-2-parse-conventional-commits.md](references/step-2-parse-conventional-commits.md) (load this step when you reach it).

### Step 3: Categorize Pull Requests

Full walkthrough: [step-3-categorize-pull-requests.md](references/step-3-categorize-pull-requests.md) (load this step when you reach it).

### Step 4: Generate Formatted Release Notes

Full walkthrough: [step-4-generate-formatted-release-notes.md](references/step-4-generate-formatted-release-notes.md) (load this step when you reach it).

### Step 5: Automate Release Note Generation in CI/CD

Full walkthrough: [step-5-automate-release-note-generation-in-ci-cd.md](references/step-5-automate-release-note-generation-in-ci-cd.md) (load this step when you reach it).

### Step 6: Handle Audience-Specific Formatting

Full walkthrough: [step-6-handle-audience-specific-formatting.md](references/step-6-handle-audience-specific-formatting.md) (load this step when you reach it).

### Step 7: End-to-End Automation Script

Full walkthrough: [step-7-end-to-end-automation-script.md](references/step-7-end-to-end-automation-script.md) (load this step when you reach it).

## Best Practices

- **Enforce conventional commits**: Use a commit-msg hook (commitlint, commitizen) to ensure all commits follow the conventional format. This makes automated release note generation reliable rather than a best-effort guess.

- **Write user-meaningful PR titles**: The PR title is often the primary source for release note entries. Write titles as complete sentences describing the user-visible change, not as internal shorthand. "Add real-time activity feed to dashboard" is useful; "JIRA-1234 dashboard work" is not.

- **Label PRs consistently**: Define a clear set of labels (feature, bug, breaking-change, internal) and require at least one category label on every PR. This enables accurate categorization even without conventional commits.

- **Separate user-facing from internal changes**: Not every merged PR belongs in user-facing release notes. Internal refactoring, CI changes, and test improvements are valuable to track but should not appear in product announcements.

- **Highlight breaking changes prominently**: Breaking changes should always appear first in release notes, with clear migration instructions. Users who scan release notes need to see breaking changes immediately, not buried in a list of features.

- **Include contributor attribution**: Crediting authors in release notes encourages community contribution and helps users know who to contact about specific changes.

- **Version your release notes tooling**: The scripts that generate release notes are as important as the application code. Keep them in version control, test them against historical releases, and update them when your commit conventions evolve.

- **Generate notes before publishing**: Generate a draft of the release notes before tagging the release. This gives you a chance to review, edit, and add context that automated tools cannot provide (such as "why" a feature was built).

## Common Pitfalls

- **Relying solely on commit messages**: Commit messages often lack context. If your team writes terse commits ("fix bug", "wip", "address review"), the generated release notes will be useless. Supplement commit data with PR titles and descriptions.

- **Including merge commit noise**: Merge commits ("Merge branch 'main' into feature-x") add clutter. Filter them out unless they carry meaningful information (such as "Merge pull request #123: Add search feature").

- **Forgetting to handle non-conventional commits**: Even teams that use conventional commits will have occasional non-conforming commits. Your parser must handle these gracefully (categorize as "Other") rather than crashing or producing garbled output.

- **Generating notes for the wrong range**: The most common error is comparing against the wrong base reference. Always verify that the "previous version" tag is correct before generating notes. An incorrect range produces either too many or too few entries.

- **Not escaping special characters**: Commit messages and PR titles may contain Markdown special characters (backticks, brackets, asterisks). Ensure your generator escapes these properly to avoid broken formatting in the rendered output.

- **Publishing unedited automated notes**: Automated generation is a starting point, not a finished product. Always review generated notes for accuracy, clarity, and completeness before publishing. Add context, reword unclear entries, and remove irrelevant items.

- **Mixing audience concerns**: A single release note document that includes both "Added export to PDF" and "Refactored internal caching layer" confuses every audience. Either produce separate documents per audience or clearly section them with headings.

- **Ignoring dependency updates**: Dependabot and Renovate PRs can flood release notes with noise. Group dependency updates into a single "Dependencies" section with a summary count rather than listing each individual bump.

- **Not linking to issues and PRs**: Release notes without links to the underlying PRs or issues force readers to search for context manually. Always include references that allow drilling down into details.

- **Inconsistent formatting across releases**: Each release should follow the same structure. If v2.4.0 used one format and v2.5.0 uses another, consumers cannot reliably parse your changelog. Use the same tooling and templates for every release.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just paste the raw git log, it's all there" | A raw log of "wip", "fix", and merge commits is unreadable to users and buries the one breaking change that matters; parsing and categorizing is what turns history into release notes someone can act on. |
| "Breaking changes are in the commits, readers will find them" | A breaking change hidden in a commit body is the change that breaks consumers on upgrade with no warning; it must be promoted to an explicit, prominent callout with migration steps. |
| "One document for everyone is simpler" | Mixing "Added PDF export" with "Refactored the caching layer" confuses every audience at once; user-facing and developer notes need separate sections or documents. |
| "The automated output is good enough to publish as-is" | Generation is a draft: it cannot supply the why behind a feature, fix garbled non-conventional commits, or drop irrelevant items; publishing unedited ships inaccuracies. |

## Verification

- [ ] Notes are generated against the correct previous-version reference (the commit range was verified before generation).
- [ ] Changes are categorized (Features, Fixes, Performance, Docs, Internal), not a flat commit dump.
- [ ] Breaking changes have a dedicated, prominent callout with migration guidance.
- [ ] The output matches the intended audience (user-facing vs developer notes are separated or clearly sectioned).
- [ ] Entries link back to the underlying PRs or issues, and Markdown special characters are escaped.

## Related Skills

- [[devlog-generation]] -- produces the internal development log that complements user-facing release notes
- [[version-upgrade]] -- coordinates the version bump and cross-file changes the release notes describe
- [[technical-writer]] -- refines the audience-appropriate language and structure of the notes
- [[cicd-architect]] -- automates release-note generation as a step in the release pipeline
