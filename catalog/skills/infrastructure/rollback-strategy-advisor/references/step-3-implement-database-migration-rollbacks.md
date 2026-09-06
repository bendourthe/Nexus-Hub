### Step 3: Implement Database Migration Rollbacks

Database rollbacks are the most complex rollback type because schema changes may be irreversible and data transformations may lose information.

**Expand-Contract Pattern**:

The safest approach for database changes is the expand-contract (also called parallel change) pattern. It separates schema migration into phases that are individually rollback-safe:

```
Phase 1 (Expand): Add new column/table alongside old one
  -> Rollback: Drop the new column/table (no data loss)

Phase 2 (Migrate): Copy/transform data from old to new
  -> Rollback: Truncate new column/table and revert to Phase 1

Phase 3 (Transition): Update application to use new schema
  -> Rollback: Redeploy previous application version

Phase 4 (Contract): Remove old column/table
  -> Rollback: NOT POSSIBLE without backup restoration
```

**Migration Rollback Script** (`scripts/rollback-migration.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

DB_URL="${1:?Usage: rollback-migration.sh <db_url> <migration_tool> [target_version]}"
MIGRATION_TOOL="${2:?Missing migration tool (flyway|alembic|knex|prisma)}"
TARGET_VERSION="${3:-}"

echo "=== Database Migration Rollback ==="
echo "Tool: $MIGRATION_TOOL"
echo ""

# Step 1: Create backup before rollback
BACKUP_FILE="backup_pre_rollback_$(date +%Y%m%d_%H%M%S).sql"
echo "Creating backup: $BACKUP_FILE"
pg_dump "$DB_URL" > "$BACKUP_FILE"
echo "Backup created: $(du -h "$BACKUP_FILE" | cut -f1)"

# Step 2: Check current migration state
case "$MIGRATION_TOOL" in
  flyway)
    echo "Current migration state:"
    flyway -url="$DB_URL" info

    if [ -n "$TARGET_VERSION" ]; then
      echo "Rolling back to version: $TARGET_VERSION"
      flyway -url="$DB_URL" undo -target="$TARGET_VERSION"
    else
      echo "Rolling back last migration"
      flyway -url="$DB_URL" undo
    fi
    ;;

  alembic)
    echo "Current migration state:"
    alembic current

    if [ -n "$TARGET_VERSION" ]; then
      echo "Rolling back to revision: $TARGET_VERSION"
      alembic downgrade "$TARGET_VERSION"
    else
      echo "Rolling back one revision"
      alembic downgrade -1
    fi
    ;;

  knex)
    echo "Rolling back last migration batch"
    npx knex migrate:rollback
    echo "Current migration state:"
    npx knex migrate:status
    ;;

  prisma)
    echo "WARNING: Prisma Migrate does not support automatic rollback"
    echo "You must manually create a new migration that reverses the changes"
    echo "or restore from the backup created above"
    echo ""
    echo "To restore from backup:"
    echo "  psql $DB_URL < $BACKUP_FILE"
    exit 1
    ;;

  *)
    echo "Unsupported migration tool: $MIGRATION_TOOL"
    exit 1
    ;;
esac

# Step 3: Verify migration state
echo ""
echo "=== Post-Rollback Verification ==="
echo "Running schema validation..."

# Basic table existence check (customize per project)
psql "$DB_URL" -c "\dt" | head -20
echo ""
echo "Migration rollback complete. Backup available at: $BACKUP_FILE"
```

**Alembic Rollback-Safe Migration Example**:

```python
"""Add user_preferences table (rollback-safe, expand phase).

Revision ID: abc123
Revises: def456
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa

revision = "abc123"
down_revision = "def456"


def upgrade():
    # Expand phase: add new table alongside existing user settings
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)

    # DO NOT drop the old user_settings column yet
    # That happens in the contract phase (separate migration)


def downgrade():
    # Safe rollback: just drop the new table
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
```
