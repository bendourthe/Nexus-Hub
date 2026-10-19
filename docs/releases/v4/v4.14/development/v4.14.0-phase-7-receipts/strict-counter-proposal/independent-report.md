# Correction Candidate Retest

Independent adversarial retest for the v4.14.0 installer preservation corrections and proposed strict-permission changes. This report is for the parent integrator before approval of the paired permission proposal. All writes were confined to task-owned Temp evidence. No tracked file, permission source, guard, approval record, real profile, Git state or installed dependency was changed by this delegate. No paid call, model call, network operation, full installer or whole suite was started.

## Verdict

The final proposed pair passes the bounded checks below. Two earlier Bash proposal failures were reproduced and corrected in subsequent Temp candidates: document-role confusion and a Windows jq Unicode-filename regression. Neither superseded candidate should be substituted for the final hash. This is focused candidate evidence, not full release qualification, approval, publication or completion of the seven plan Definition-of-Done items.

## Exact Bytes

| Artifact | Raw SHA-256 |
|---|---|
| Nonpermission PowerShell correction | `f63818a2aaeb2d8f59c16883323b37d0bd297ada921203eaacf251b896a927c3` |
| Proposed PowerShell correction plus strict missing-entry counter | `230a93f8d9d2e7f652cfcb287911373862539249da68f419103bb44ec16a92d9` |
| Final positional-file Bash strict proposal, snapshot `installer.sh` beside this report | `d18a5b40e106f51508f6948c92dbc09b7297035d25f0ca24655ae965011661e4` |
| Prior actual Bash control | `5346e4283ae0f9556275469ef8e217d4b9cd9d7b883aea4d52506a1df9d62548` |

PowerShell snapshots and receipts are retained under `C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-lossless-adversarial-e1d47ee936684682a8f0c07550005a57`. Final Bash snapshot and receipts are beside this report. Parent reports the nonpermission correction has been applied to actual source; this delegate's candidate receipts do not replace fresh tracked-source qualification after any later edit. The proposed strict changes remain outside this delegate's approval authority.

## Passing Evidence

| Boundary | Observed result |
|---|---|
| Native reader, Windows PowerShell 5.1 | 41 of 41 inputs pass |
| Native reader, PowerShell 7.6.7 current branch | 41 of 41 pass |
| Actual older-Core reader branch forced on PowerShell 7.6.7 | 41 of 41 pass |
| Actual native helper sequences | 5 of 5 pass |
| Proposed PowerShell strict writer | 9 of 9 pass on each of 5.1 and 7.6.7 |
| Final proposed Bash strict writer, Git Bash and Windows jq 1.8.2 | 23 of 23 primary cases pass |
| Final Bash same-file input refusal | 1 of 1 pass |

The 123 reader observations preserve decoded values, exact keys and root shapes, with recursive native checks finding no introduced DateTime or DateTimeOffset. Fixtures cover ISO UTC and offset text, fractional seconds, raw escaped Microsoft-date JSON, zero through twelve raw backslashes before a slash, asymmetric escapes, Unicode slash escapes, escaped quotes and newlines. Keys include Type, Value, Properties, Children, GetEnumerator, Count, Item, PSObject, get_Value and get_Name. Null, false, zero, empty strings, empty and singleton arrays, nested arrays and singleton objects retain their shapes. Forced fallback runs the actual branch with the DateKind capability hidden; it is not an actual older runtime qualification.

The five helper sequences execute the native reader and writer, dictionary hook merger and callers, hook command converter, core seeding, actual Python allow-permission helper, strict helper and MCP settings registration. Two sequences use the nonpermission candidate on 5.1 and 7; three use the proposed combined PowerShell candidate on 5.1, current 7 and forced fallback. Copy helpers are no-ops and MCP dependencies are controlled local success. These are actual helper sequences, not full installer processes. All preserve original custom leaves at saved stages, a custom hook with case-distinct nested metadata, deep-15 objects, date-shaped strings and custom MCP entries, while adding managed hooks, Sonnet, all shipped strict entries and managed MCP registration. Profiles include brackets, spaces, dollar, backtick, semicolon and Unicode characters. Combined-candidate runs include the original 23/13 duplicate-list reproducer.

Final Bash cases cover duplicate cancellation, already-present byte-preserving return, case-distinct parent metadata, invalid permission parents and arrays, invalid overlay shape, multiple JSON documents in either file, both multi-document files, empty or whitespace input in either role, both empty, empty first input compensated by multiple second documents, the reverse compensation, duplicate overlay entries and the combined special-character Unicode profile. Valid mutations retain custom and allow values, leave overlay bytes unchanged, create an exact before-write backup, contain all 22 deny and 12 ask entries, and repeat without mutation or a new backup while reporting up to date. Refusals preserve settings bytes, create no backup, warn and emit no false application or up-to-date message. Supplying the identical file in both roles also refuses safely.

## Superseded Findings

The first Bash correction, `c77e67b00329e85397e8ada8aa9f9745e8b72b9a851ccc8962d50249b9abe6ba`, used combined slurp indexes without establishing one document per file. A second settings document became the overlay, the actual shipped overlay was ignored, and the helper reported application of one injected entry. Multiple overlay documents were also accepted. Concrete raw inputs, argv and outputs are retained in `strict-bash-results.json` under the PowerShell evidence directory. The final positional proposal refuses those cases and empty-file compensation in both directions.

The intermediate named-slurpfile proposal, `abbf4828a1a7468d12f985f62f49b4808bab746c4bc87a9494ffb50adb35624d`, fixed document roles but failed to apply strict entries from a Unicode profile on Windows. Direct native jq 1.8.2 returned exit 2 for `-n --slurpfile settings <existing Unicode filename> '$settings'`, with `Could not open`; positional `-s . <same filename>` returned 0. The prior actual helper applied all 34 entries and created a backup on the identical Unicode-path control, while the intermediate proposal warned, applied none and created no backup. This eliminates shell interpolation and backup operations as causes. Full proof is in `C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-strict-roles-retest-5b2211580f824495baa615de78e32a3d/unicode-control-results.json`. The final candidate reads positional filenames, records each input filename and document, and requires two documents from distinct paths in both count and merge. The Unicode fixture now passes.

## Proving Commands

These exact direct drivers were executed with fresh task-owned fixture roots; all final drivers exit 0. Their command arrays and raw outputs are retained in the JSON receipts. Fixture creation intentionally refuses directory reuse, so a fresh rerun must use new fixture names rather than overwrite these receipts.

```powershell
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-lossless-adversarial-e1d47ee936684682a8f0c07550005a57/reader-final.py'
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-lossless-adversarial-e1d47ee936684682a8f0c07550005a57/run.py' ps51
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-lossless-adversarial-e1d47ee936684682a8f0c07550005a57/run.py' ps7
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-lossless-adversarial-e1d47ee936684682a8f0c07550005a57/full.py'
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-strict-positional-retest-b673cd38ca514d9e850c4f6ce79247bb/bootstrap.py'
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-strict-positional-retest-b673cd38ca514d9e850c4f6ce79247bb/same-file-control.py'
```

PowerShell receipts are `reader-final-results.json`, `full-results.json`, `strict-ps51-results.json` and `strict-ps7-results.json`. Final Bash receipts are `results.json` and `same-file-control-results.json` beside this report. Source snapshots are retained for hash-bound review. No pytest process was used.

## Considered but Rejected

| Attack | Observable counter-evidence |
|---|---|
| Literal slash normalization alters user backslashes or Microsoft-date text | All 123 branch/input observations preserve the expected decoded strings and shapes with no native date objects. |
| Property names shadow the fallback token adapter | Type, Value, Properties and method-like keys survive actual forced fallback parsing and full helper sequences. |
| Nested case-distinct hook metadata still prevents managed registration | All five sequences retain the complete custom hook and add the managed hook without warnings. |
| Duplicate user permissions still cancel the strict missing-entry count | Both native PowerShell runtimes and final Bash apply all shipped entries to the original duplicate reproducer. |
| Final Bash count still confuses file roles | Both multiple-document directions, both empty/multiple compensation directions and identical-file roles refuse with unchanged bytes and no false success. |
| Special characters execute or glob during strict merging | Combined literal punctuation and Unicode profile passes; ASCII special-character controls also pass. No command execution is inferred from filename contents. |

## Limits And Recommendation

No remaining failure was observed in this bounded final candidate scope. This does not qualify arbitrary numeric precision, arbitrary depth, other PowerShell releases, native Linux, filesystem races, whole installer distribution, authenticated model behavior, the complete affected test suite or remote checks. Full gates and all seven plan DoD checks remain parent-owned. The full installer probe was not restarted here.

Recommend presenting the exact PowerShell `230a...92d9` and Bash `d18a...61e4` strict-only proposals together for the required native security-change approval. These results do not grant that approval. After any authorized application, run fresh actual-source affected checks and the parent-owned full isolated installer flow. Cost was zero paid calls. The material remaining integration risk is applying different bytes or skipping actual-source qualification.
