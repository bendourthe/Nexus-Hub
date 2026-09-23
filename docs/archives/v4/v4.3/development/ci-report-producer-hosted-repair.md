# CI report producer hosted dependency repair

PR #243's first hosted run, 35823076193, failed its Linux `tests` job 107058944900. The `repo-tests-ci` profile command exited 4 because pytest rejected `--cov=scripts.ci` and `--cov-report=xml:reports/coverage-ci.xml`: pytest-cov was pinned in the universal CI lock but absent from the Linux tests job's separate install command. The failure does not establish a coverage result and remains the original failed-run evidence.

The job now installs pytest-cov with its existing test dependencies. A workflow contract test ties that install to the profile's coverage flags. The focused workflow and CI-engine tests pass, 77/77. Hosted coverage XML and aggregate artifact inspection remain pending before DF-3 can close.
