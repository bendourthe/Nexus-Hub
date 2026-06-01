# EDR Detection Query Examples

This reference holds EDR-native detection queries for the three highest-signal endpoint behaviors covered by the parent SKILL.md: process injection, suspicious process trees, and living-off-the-land binary (LOLBin) abuse. Each behavior is shown as a portable Sigma rule (the reviewable source of truth) plus two platform-native translations: Microsoft Defender for Endpoint advanced hunting (KQL over `DeviceProcessEvents` and `DeviceEvents`) and Splunk SPL over Sysmon. Re-author the field values and allow-lists for your own environment; the placeholders here are meant to be adapted, not shipped verbatim. Detect on behavior and parent-child context, not a static hash, and measure precision before deployment.

## Behavior 1: Suspicious process tree (office app spawns a shell)

A document-handling application spawning a command shell is rare-when-benign and common-when-malicious, which is exactly the property a usable rule needs. Parent-child lineage is the primary feature here, not the command line alone.

### Sigma

```yaml
title: Shell Spawned By Office Application
id: a18c4b22-7f3e-4d61-bc09-3e7a1f0d9c52
status: experimental
description: A command shell launched as a child of an office document handler.
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
            - '\powerpnt.exe'
            - '\outlook.exe'
        Image|endswith:
            - '\cmd.exe'
            - '\powershell.exe'
            - '\wscript.exe'
            - '\cscript.exe'
    filter_known_addin:
        CommandLine|contains: '\Program Files\ApprovedAddin\'
    condition: selection and not filter_known_addin
level: high
tags:
    - attack.execution
    - attack.t1059
falsepositives:
    - Signed office add-ins that legitimately shell out; allow-list the specific add-in path.
```

### Microsoft Defender for Endpoint (advanced hunting, KQL)

```kql
DeviceProcessEvents
| where InitiatingProcessFileName in~ ("winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe")
| where FileName in~ ("cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe")
| where not(ProcessCommandLine has @"\Program Files\ApprovedAddin\")
| project Timestamp, DeviceName, AccountName, InitiatingProcessFileName, FileName, ProcessCommandLine
| sort by Timestamp desc
```

### Splunk SPL (Sysmon)

```sql
index=endpoint sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1
    (ParentImage="*\\winword.exe" OR ParentImage="*\\excel.exe" OR ParentImage="*\\powerpnt.exe" OR ParentImage="*\\outlook.exe")
    (Image="*\\cmd.exe" OR Image="*\\powershell.exe" OR Image="*\\wscript.exe" OR Image="*\\cscript.exe")
    NOT (CommandLine="*\\Program Files\\ApprovedAddin\\*")
| table _time host User ParentImage Image CommandLine
| sort - _time
```

## Behavior 2: Process injection (remote thread into another process)

Injection is best keyed on the cross-process action itself (a remote thread created into a target process) rather than on any single process name. The source process being unusual for that target raises the signal.

### Sigma

```yaml
title: Remote Thread Created Into Sensitive Process
id: c92e1d07-4b88-49af-a5d3-6f2b8e1c0a47
status: experimental
description: A process creates a remote thread inside another process, an injection indicator.
references:
    - https://attack.mitre.org/techniques/T1055/
author: detection-engineering
date: 2026/05/29
logsource:
    category: create_remote_thread
    product: windows
detection:
    selection:
        TargetImage|endswith:
            - '\lsass.exe'
            - '\explorer.exe'
            - '\svchost.exe'
    filter_self:
        SourceImage|endswith: '\MsMpEng.exe'
    condition: selection and not filter_self
level: high
tags:
    - attack.defense_evasion
    - attack.t1055
falsepositives:
    - Endpoint security agents that legitimately inject; allow-list the specific signed agent image.
```

### Microsoft Defender for Endpoint (advanced hunting, KQL)

```kql
DeviceEvents
| where ActionType == "CreateRemoteThreadApiCall"
| where FileName in~ ("lsass.exe", "explorer.exe", "svchost.exe")
| where not(InitiatingProcessFileName =~ "MsMpEng.exe")
| project Timestamp, DeviceName, InitiatingProcessFileName, InitiatingProcessCommandLine, FileName
| sort by Timestamp desc
```

### Splunk SPL (Sysmon)

```sql
index=endpoint sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=8
    (TargetImage="*\\lsass.exe" OR TargetImage="*\\explorer.exe" OR TargetImage="*\\svchost.exe")
    NOT (SourceImage="*\\MsMpEng.exe")
| table _time host SourceImage TargetImage StartFunction
| sort - _time
```

## Behavior 3: LOLBin abuse (trusted binary proxies execution)

A LOLBin cannot be blocked by hash because it is a trusted OS component, so the detection keys on the abusive invocation pattern (a download or remote-execution flag) and on an unexpected parent. Signing and System32 path do not clear this technique.

### Sigma

```yaml
title: LOLBin Remote Payload Execution
id: e07b3a9f-2d56-4c18-9e44-1a8f0b7d3c61
status: experimental
description: A trusted system binary invoked with flags that download or proxy remote payload execution.
references:
    - https://attack.mitre.org/techniques/T1218/
author: detection-engineering
date: 2026/05/29
logsource:
    category: process_creation
    product: windows
detection:
    selection_mshta:
        Image|endswith: '\mshta.exe'
        CommandLine|contains:
            - 'http://'
            - 'https://'
    selection_regsvr:
        Image|endswith: '\regsvr32.exe'
        CommandLine|contains:
            - '/i:http'
            - 'scrobj.dll'
    filter_patch_parent:
        ParentImage|endswith: '\TrustedPatcher.exe'
    condition: (selection_mshta or selection_regsvr) and not filter_patch_parent
level: high
tags:
    - attack.defense_evasion
    - attack.t1218
falsepositives:
    - Approved deployment tooling that uses these binaries; allow-list the specific parent process.
```

### Microsoft Defender for Endpoint (advanced hunting, KQL)

```kql
DeviceProcessEvents
| where (FileName =~ "mshta.exe" and ProcessCommandLine has_any ("http://", "https://"))
     or (FileName =~ "regsvr32.exe" and ProcessCommandLine has_any ("/i:http", "scrobj.dll"))
| where not(InitiatingProcessFileName =~ "TrustedPatcher.exe")
| project Timestamp, DeviceName, AccountName, InitiatingProcessFileName, FileName, ProcessCommandLine
| sort by Timestamp desc
```

### Splunk SPL (Sysmon)

```sql
index=endpoint sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1
    ((Image="*\\mshta.exe" AND (CommandLine="*http://*" OR CommandLine="*https://*"))
     OR (Image="*\\regsvr32.exe" AND (CommandLine="*/i:http*" OR CommandLine="*scrobj.dll*")))
    NOT (ParentImage="*\\TrustedPatcher.exe")
| table _time host User ParentImage Image CommandLine
| sort - _time
```

## Adapting these examples

- Change the Sigma rule first, then regenerate the KQL and SPL translations. Hand-editing a platform query so it diverges from the Sigma source defeats portability and peer review.
- Replace each `filter` allow-list with the real signed agents, add-in paths, and deployment tooling in your environment; add every new false positive as a narrow entry rather than loosening the core selection.
- Validate against benign samples (to measure false positives) and contained malicious samples (to confirm true positives), record precision and recall, and re-test after every condition change before deployment.
