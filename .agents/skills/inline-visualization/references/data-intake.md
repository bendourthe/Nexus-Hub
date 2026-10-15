# Data intake rules and limits

How `inline-visualization` takes data in before anything is drawn (SKILL.md, step 2). The limits are defaults: each can be tuned here for a project, and the skill states whichever value is in force when a limit changes the output.

## Limits

| Limit | Default | When exceeded |
|---|---|---|
| Bytes read from one file | 5 MiB | Stop reading at the cap; state that only the first 5 MiB was used |
| Rows | 50,000 | Aggregate (for example by time bucket or category) or take a stated sample |
| Columns | 50 | Use only the columns the question names; list the ones ignored |
| Characters per line | 10,000 | Treat the line as malformed and skip it; count and state the skipped lines |
| Categories (bars, series, groups) or nodes | 200 | Keep the top categories by the measure and group the rest as "other", or ask which to show |

## Intake rules

1. **Resolve before reading.** Resolve the path the user named, including every symlink. Accept only a regular file whose resolved location is inside that path. Refuse a directory, a device, a socket, a FIFO, and any symlink that resolves outside the named path.
2. **Refuse secret stores.** Refuse `.env` and `.env.*`, anything under `.ssh`, `.aws/credentials`, `.netrc`, `*.pem`, `*.key`, `id_*`, `credentials*`, `*token*`, and `*secret*` files, unless the user confirms that exact file by name. Confirming one file does not open its directory.
3. **Read with a cap.** Open the file and read at most the byte cap, rather than checking its size and then reading it. A file that changes between those two steps cannot slip past the cap.
4. **Parse strictly.** An unparseable CSV or JSON, a measure column with non-numeric values, or zero data rows stops with a named error and no chart. Do not coerce or invent values.
5. **One source at a time.** If two inputs disagree (a file and a pasted table), ask which to use. Never merge them silently.
6. **State what changed.** Any sampling, aggregation, truncation, skipped line, or ignored column is stated in the answer, alongside the tier line.
