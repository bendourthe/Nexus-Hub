# Nexus Hub 0.5.0 Session Overrides

This record covers event-based effort, native Claude picker synchronization, Codex history and the extension rename developed on 2026-11-05. Read it when verifying installed behavior, distinguishing source tests from native controls, or reviewing the upgrade from Settings 0.4.2.

## Behavior

Changing the Nexus default updates supported open sessions once. Manual session choices remain until the next Nexus default change or explicit Apply to all sessions. New sessions use the saved default. The UI remembers application revisions. Ordinary polling leaves manual choices alone. The stdio bridge passes manual effort updates and turns through unchanged. Shared atomic effort-apply events reach every connected editor. Pending acknowledgments carry their revision, so an older result cannot suppress a newer reapply.

Claude Ultra maps to xhigh with Ultracode enabled. Claude uses the native update_state request and configuration signal to deliver an effort/revision pair to session models. Its existing applied-effort adoption method updates the picker without changing availability flags. The earlier raw-window-message tests did not cover the real transport and were replaced with configuration-path tests.

The display name and activity container are Nexus Hub; the view is Settings. Stable identifiers and configuration keys stay unchanged. The panel shows the installed Hub version and opens the existing interactive CLI upgrade flow without accepting an upgrade automatically.

Codex tabs have a History command. It reads local index metadata, validates IDs and opens a selected native local conversation route. Full and remote history remains available through the Codex sidebar.

## Verification

The final extension regression run passed 373 tests with one existing skip across 18 files. Statement coverage was 81.84%, branch coverage 80.62%, function coverage 84.77% and line coverage 86.45%. The final command-title check passed 10 manifest tests. TypeScript compilation passed after the Windows upgrade terminal was changed to retain its results. Settings CLI admission tests passed 19 tests with 11 platform-specific skips. Pipeline files were unchanged.

The private host visibly rendered Nexus Hub: Settings, Apply to all sessions, installed version 4.14.8 and Check for upgrades. Actual controls in the same open Claude and Codex drafts changed from High to Low. Manual Claude Medium and Codex High choices stayed in place while the Nexus default was Low. Clicking Apply to all sessions reset both controls to Low (displayed as Light in one Codex view).

Native history opened existing small test conversations without sending another prompt. Changing Nexus to Ultra changed the same existing Claude conversation to Opus 5.5 Extra high with Ultracode and the same existing Codex conversation to GPT-6.1 Sol Ultra. Restoring Medium changed both controls to Medium. After manually changing that Codex conversation to High, the native toolbar opened a separate new Codex tab at Medium. The earlier conversation remained a separate tab. These observations verify visible picker behavior; no new model inference request was sent during these checks.

The Codex History toolbar command opened a selected saved conversation in an editor tab. The upgrade command opened a persistent PowerShell terminal and reported Installed: 4.14.8, Latest: 4.14.8 and nothing to do. No core upgrade was accepted or performed.

One automatically opened private Codex tab timed out before its first renderer message. A subsequent tab opened through the native command rendered normally. Startup reliability is therefore not fully qualified; the successful effort checks do not erase that timeout. Working editor windows were neither closed nor reloaded. Manual overrides across a full editor reload were not qualified.

The persistent Claude compatibility warning was traced to an outdated maximum admitted CLI version. Only the seven Claude effort-write entries were extended from 2.1.283 to the locally verified 2.1.318. The installed catalog was backed up and updated. A fresh private view model reported needsAttention false, no native adapter errors and Medium. Native Copilot, Cursor and Antigravity agent effort remains manual; this is stated in the footer. Claude and Codex adapters are pinned to the qualified vendor builds.

## Artifacts

Qualification artifacts are under C:/Users/BEDOURTHE/Documents/nx-ui050-qualification. The VSIX SHA256 is e03b71582b9ef00463c3870c4cdabed292bd80b1a3a32d0bc5fb80fea6bb2470. The official editor CLIs registered nexus-hub.nexus-hub-settings@0.5.0 in VS Code, Cursor and Antigravity. All 27 package payload files matched each installed directory, allowing only installer metadata in package.json. See install-050.json and delivery-verified.json in that artifact directory.

The two Claude and three Codex native adapter files matched their installation receipts and original backups under ~/.nexus-hub/native-ui. The actual pinned-vendor qualifier passed parsing, repeat installation, independent-edit preservation, exact restoration and redirected-receipt rejection for both vendors. Catalog backup and installation receipts are catalog-before-050.json and catalog-install-050.json. Existing editor processes still require a reload to load the newly installed extension and adapters.

## Preferences

The user approved temporary live effort changes followed by restoration to Medium. The official diff showed only default_effort changing from xhigh to medium. The current Medium baseline was accepted under that genuine user agreement. The saved default was restored to Medium and independently checked after installation. No automatic baseline adoption was used for that preference.
