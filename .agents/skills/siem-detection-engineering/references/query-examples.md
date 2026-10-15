# SIEM Detection Query Examples

This reference shows one behavior expressed across platforms so the portable Sigma rule stays the source of truth and each platform-native query is a faithful translation of it. The worked behavior is the same one used in the parent SKILL.md: a scripting interpreter spawned by a document-handling process executes an encoded command line (an instance of command and scripting interpreter activity, ATT&CK T1059). Re-author these snippets for your own field schema and allow-lists before shipping; the values shown are placeholders an analyst can adapt.

All four representations below describe the same selection logic:

- Parent process is a document handler (Word or Excel).
- Child process is the PowerShell interpreter.
- The command line carries an encoded-command flag.
- A narrow allow-list subtracts a known signed service account rather than widening the rule.

## Sigma (portable source of truth)

Sigma is the canonical version. Author here first, then regenerate the platform queries below from it. Keep the `filter` block as a narrow allow-list, never a broad wildcard exclusion.

```yaml
title: Encoded Interpreter Command From Document Handler
id: 5d3a2f10-1c44-4e2b-9b7a-0f9c2a1e7b40
status: experimental
description: Scripting interpreter launched by an office document process running an encoded command line.
references:
    - https://attack.mitre.org/techniques/T1059/
author: detection-engineering
date: 2026/05/29
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        ParentImage|endswith:
            - '\winword.exe'
            - '\excel.exe'
        Image|endswith: '\powershell.exe'
        CommandLine|contains:
            - ' -enc '
            - ' -EncodedCommand '
    filter_known_admin:
        User|startswith: 'SVC_'
    condition: selection and not filter_known_admin
fields:
    - User
    - ParentImage
    - Image
    - CommandLine
level: high
tags:
    - attack.execution
    - attack.t1059
falsepositives:
    - Signed administrative automation; track in the allow-list, do not widen the rule.
```

## Splunk SPL

Map the Sigma field names to your process-creation source type (Sysmon EventCode 1 or the Endpoint data model). Keep the allow-list as an explicit `NOT` on a narrow field, mirroring `filter_known_admin`.

```sql
index=endpoint sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1
    (ParentImage="*\\winword.exe" OR ParentImage="*\\excel.exe")
    Image="*\\powershell.exe"
    (CommandLine="* -enc *" OR CommandLine="* -EncodedCommand *")
    NOT (User="SVC_*")
| table _time host User ParentImage Image CommandLine
| sort - _time
```

## Microsoft Sentinel (KQL)

Translate against the `DeviceProcessEvents` table. Use `has_any` for the encoded-command flags and an explicit `where` exclusion for the allow-listed account.

```kql
DeviceProcessEvents
| where InitiatingProcessFileName in~ ("winword.exe", "excel.exe")
| where FileName =~ "powershell.exe"
| where ProcessCommandLine has_any ("-enc", "-EncodedCommand")
| where not(InitiatingProcessAccountName startswith "SVC_")
| project Timestamp, DeviceName, InitiatingProcessAccountName, InitiatingProcessFileName, FileName, ProcessCommandLine
| sort by Timestamp desc
```

## Elastic (EQL)

Express the same logic as an EQL process sequence on the Elastic Common Schema (ECS) process fields. The `where` clause carries both the selection and the allow-list exclusion.

```sql
process where event.type == "start"
  and process.parent.name in ("winword.exe", "excel.exe")
  and process.name == "powershell.exe"
  and (process.command_line like "* -enc *" or process.command_line like "* -EncodedCommand *")
  and not user.name like "SVC_*"
```

## Adapting these examples

- Change the Sigma rule first, then regenerate the platform queries. Hand-editing a platform query so it drifts from the Sigma source defeats portability.
- Replace the `SVC_` allow-list prefix with the real signed automation principals in your environment, and add each new false positive as a narrow entry rather than loosening the `selection`.
- Confirm the named fields (`ParentImage`, `CommandLine`, `InitiatingProcessAccountName`, `process.parent.name`) are actually populated in your data before trusting the rule, then seed a benign matching event and prove the query returns it.
