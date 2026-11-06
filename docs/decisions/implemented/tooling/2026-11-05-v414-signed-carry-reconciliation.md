# Decision: v4.14 Signed Carry Reconciliation

Status: implemented - Repository source recognizes only the reviewed published carry pairs; integration and installed adoption retain their separate gates.

This decision covers the bounded v4.14 completion-reader recovery for maintainers qualifying the original minor controller after all nine releases were published. It defines the signed authorities, publication oracle, unchanged migration boundary, and required native replay; it grants no authority to edit run records.

## Problem

The original minor authority freezes seven plans and their migration bounds. Two later plans released independently, and the last plan's genuine signed carry approval covers thirteen existing migrations that the original minor reader cannot recognize. Rewriting the original authority or accepting matching mutable ledger copies would lose the original approval boundary. A separate provenance mismatch affects twenty-four exact frozen recording-task opportunities; replacing their patch labels would break the existing one-plan reader.

## Decision

Retain the original classes, bounds, member list, hashes, budgets, and record identities. A read-only compatibility path recognizes only thirteen fixed source/destination pairs already published in v4.14.8. It requires the exact original minor and last-plan record identities, nonces and approval-page hashes, original start commit, last-plan branch/repository/plan identity, native HMAC validation, genuine carry approval, all seven unchanged frozen members, and matching Git ownership. Missing ownership or publication observations never establish completion.

Authenticate the raw auxiliary record before interpreting its metadata or paths, then retain the complete native plan validation and ownership checks. Compare both current ledger entries against the immutable published commit after only the stock archive path repairs and CRLF conversion. Disable Git object replacement for pinned publication reads and keep those blobs in a separate cache namespace. Require the matching local tag and existing published-release check. Both copies must remain nonsensitive, uniquely present, and semantically unchanged; the destination remains open. The ordinary migration writer and its frozen-bound preflight are unchanged.

The native signature authenticates its declared approval fields. The unsigned owner root is independently bound by the pinned record key, with malformed path or encoding failures refused. Mutable blockers must be a list of dictionaries with no open entry before the native loader runs. These checks preserve the existing approval payload and record schema.

The separate recording-task reader accepts the exact source patch already proved by the frozen task and anchored Source phase, preserving existing labels and canonical-copy restrictions. The inherited AR-77 repair changes only paragraph order, preserving every line and proving both transfers.

## Alternatives considered

- Change the original migration bound, re-sign its record, or replace its authority: rejected because that changes what the user originally approved.
- Rewrite existing patch-qualified provenance to minor-only labels: rejected because the one-plan carry reader requires the original patch identity.
- Accept any signed carry approval or any pair of matching mutable copies: rejected because replacement records or jointly edited bodies could bypass the reviewed disposition.
- Treat the earlier one-plan archive as proof that the original minor completed: rejected because it did not re-freeze the original seven-member authority.
- Generalize cross-run carry recognition for every project: deferred because this recovery proves one published incident and does not establish a general authorization policy.

## Consequences

The helper contains a deliberate incident-specific compatibility boundary. Other runs retain their existing behavior. Native archive apply remains the sole writer of archived member identities; installed delivery is restricted to the reviewed merged helper after protected integration. Genuine native completion and worktree cleanup still require their own observed gates. The last-plan owner must remain present until reconciliation and completion checks finish.

Regression coverage includes real isolated signed authorities, record and plan mutations, missing publication, jointly altered bodies, a Git replacement attack, independent Git ownership, sensitive reclassification, unchanged native-record bytes, and archived/CRLF input. Release evidence records actual qualification and review results without treating local checks as integration or completion.
