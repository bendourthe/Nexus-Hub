# Per-Language Version Checklists and a Worked Example

The files each language ecosystem carries a version in, and one end-to-end worked run. Kept out of the skill body because both are looked up for a specific project once, not needed on every trigger; the RULES they serve live in `SKILL.md`.

## Language-Specific Checklists

### Python Checklist
- [ ] pyproject.toml version updated
- [ ] __version__.py or __init__.py updated
- [ ] setup.py version updated (if exists)
- [ ] requirements.txt reviewed
- [ ] docs/conf.py version updated (Sphinx)

### JavaScript/TypeScript Checklist
- [ ] package.json version updated
- [ ] package-lock.json regenerated
- [ ] yarn.lock regenerated (if using Yarn)
- [ ] docs version updated

### Java Checklist
- [ ] pom.xml version updated
- [ ] build.gradle version updated (if Gradle)
- [ ] META-INF/MANIFEST.MF updated

### C# Checklist
- [ ] *.csproj Version updated
- [ ] AssemblyInfo.cs updated
- [ ] NuGet package version updated

### Go Checklist
- [ ] version.go constant updated
- [ ] go.mod reviewed
- [ ] Git tag created

## Example Workflow

```
User: Upgrade version to 0.2.7

Claude:
1. Found current version: 0.2.6 (from pyproject.toml)
2. Found last tag: v0.2.6
3. Analyzing commits since v0.2.6...
   - Found 5 commits with changes to 12 files
4. Auto-generated CHANGELOG entries:
   ### Added
   - New FigureSettings class for configuration management
   - ModernDateEdit widget for date selection
   ### Changed
   - Improved Matplotlib theming
   ### Fixed
   - Color picker initialization bug
5. User confirms CHANGELOG is accurate
6. Updating files:
   - pyproject.toml: 0.2.6 → 0.2.7 ✓
   - README.md: Updated title and "What's New" ✓
   - src/__init__.py: __version__ = "0.2.7" ✓
   - CHANGELOG.md: Added [0.2.7] entry ✓
7. Deep scan found no additional version references
8. Validation: No "0.2.6" references remain ✓
9. Generated commit message:

v0.2.7: Add figure settings management and improve theming

Changes:
- Add FigureSettings class for configuration management
- Add ModernDateEdit widget for date selection
- Improve Matplotlib theming
- Fix color picker initialization bug

Version upgrade complete! Copy the commit message above when ready.
```
