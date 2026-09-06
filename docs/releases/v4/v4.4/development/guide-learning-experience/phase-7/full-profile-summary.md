# CI Report - profile `full` - FAIL

**Platform**: windows (Windows 11)
**Python**: 3.12.10
**Duration**: 5590.2s

| Result | Count |
|---|---|
| Passed | 40 |
| Failed | 4 |
| Skipped | 0 |
| Advisory failures | 0 |

**Change scope**: unrecognized path(s), running everything: ['guides/website/README.md', 'guides/website/example/training-scenes.json', 'guides/website/nexus-hub-guide.html']

## Groups

| Group | Status | Commands | Duration |
|---|---|---|---|
| catalog-parse | PASS | 4 command(s) | 0.5s |
| hygiene | FAIL | 5 command(s) | 6.4s |
| interpreters | FAIL | 1 command(s) | 0.6s |
| catalog | PASS | 6 command(s) | 7.1s |
| security | PASS | 3 command(s) | 4.2s |
| workflows | PASS | 2 command(s) | 0.7s |
| platform-contracts | PASS | 6 command(s) | 1.6s |
| docs | PASS | 7 command(s) | 1.3s |
| version | PASS | 1 command(s) | 0.2s |
| tests | FAIL | 2 command(s) | 5489.7s |
| extension-tests | PASS | 7 command(s) | 77.9s |

## Failures

### FAIL `hygiene` / validate_unicode_safety

Exit code: `2`. exit 2

```text
docs\releases\v4\v4.4\development\guide-learning-experience\phase-6\ADVERSARIAL-REPORT.md:1:1: unsafe Unicode U+FEFF (ZERO WIDTH NO-BREAK SPACE / BOM)
docs\releases\v4\v4.4\development\guide-learning-experience\phase-6\focus-retest.txt: IO: not valid UTF-8: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte

validate_unicode_safety: 1 file(s) could not be read or decoded; 1 error(s) and 0 warning(s) in the 2368 file(s) scanned.
```

### FAIL `hygiene` / validate_no_personal_paths

Exit code: `1`. exit 1

```text
docs\releases\v4\v4.9\analysis\interactive-handbooks-source-analysis.md:18:27: personal path leak: '<user-home>' (username='BEDOURTHE')
docs\releases\v4\v4.9\analysis\interactive-handbooks-source-analysis.md:18:25: personal path leak: '<user-home>' (username='BEDOURTHE')

validate_no_personal_paths: 2 finding(s) in 2273 scanned file(s).
```

### FAIL `interpreters` / check_interpreter_resolution

Exit code: `1`. exit 1

```text
[interpreters] FAIL bash: PATH bash is unusable (exited 127: /bin/bash: C:UsersBEDOUR~1AppDataLocalTemptmpmaf2o5gknexus-probe.sh: No such file or directory); a working Git Bash exists at C:\Program Files\Git\bin\bash.exe. Put its directory ahead of System32 on PATH so hooks the host launches as `bash <script>` can run.
[interpreters] A hook registered as `bash <script>` would not run on this host. Hooks would be silently inert rather than reporting an error.
```

### TIMEOUT `tests` / repo-tests

Exit code: `None`. exceeded 4500s

```text
(no output captured)
```

## Artifacts

- `summary.md`
- `summary.json`
- `junit/<group>.xml`
- `environment.json`
