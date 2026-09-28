# v4.9 Private Harness Residue Disposition

This frozen record closes v4.9.0 WN-1's local workstation cleanup. It does not certify the v4.9 model-profile claims or any distributed security-audit behavior.

On 2026-09-24, the ignored synthetic test-workspace residue was distinguished from the retained audit answer archive and other `.nexus` report directories. The exact target contained 180 files in 250 items, no Git-tracked file and no reparse point. Its contents were fixture/runtime copies and synthetic audit records. Only that target was sent to the Windows Recycle Bin through the operating system's recoverable delete operation.

A fresh path check returned absent for the synthetic residue and present for `.nexus/security-audit-answers`. This is a workstation-only result; it neither alters published assets nor retroactively changes the original policy-blocked cleanup record in [v4.9 known gaps](../../../../releases/v4/v4.9/known-gaps.md).
