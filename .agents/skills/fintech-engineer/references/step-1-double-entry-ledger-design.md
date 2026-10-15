### Step 1: Double-Entry Ledger Design

A double-entry ledger is the foundation of every financial system. Every transaction records equal debits and credits, ensuring the accounting equation (Assets = Liabilities + Equity) always holds.

**Account Types and Normal Balances**:

| Account Type | Normal Balance | Debit Effect | Credit Effect | Examples |
|-------------|---------------|-------------|--------------|---------|
| Asset | Debit | Increase | Decrease | Cash, Receivables, User Wallets |
| Liability | Credit | Decrease | Increase | Payables, User Deposits, Loans |
| Equity | Credit | Decrease | Increase | Retained Earnings, Capital |
| Revenue | Credit | Decrease | Increase | Transaction Fees, Interest Income |
| Expense | Debit | Increase | Decrease | Processing Fees, Refunds |

**PostgreSQL Schema for a General Ledger**:

```sql
-- Chart of accounts: defines all account types in the system
CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(20) UNIQUE NOT NULL,       -- e.g., "1001" for cash
    name            VARCHAR(255) NOT NULL,
    account_type    VARCHAR(20) NOT NULL CHECK (
        account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')
    ),
    currency        CHAR(3) NOT NULL DEFAULT 'USD',    -- ISO 4217
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);

-- Journal entries: the atomic unit of accounting
CREATE TABLE journal_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,      -- prevents duplicate postings
    description     TEXT NOT NULL,
    posted_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(255) NOT NULL,
    metadata        JSONB DEFAULT '{}',                 -- source system, reference IDs
    -- Journal entries are immutable: no UPDATE or DELETE allowed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Line items: individual debit/credit entries within a journal entry
CREATE TABLE journal_lines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id),
    account_id      UUID NOT NULL REFERENCES accounts(id),
    amount          NUMERIC(19, 4) NOT NULL CHECK (amount > 0),
    entry_type      VARCHAR(6) NOT NULL CHECK (entry_type IN ('debit', 'credit')),
    currency        CHAR(3) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enforce double-entry invariant: debits must equal credits per journal entry
CREATE OR REPLACE FUNCTION check_balanced_entry()
RETURNS TRIGGER AS $$
DECLARE
    debit_sum  NUMERIC(19, 4);
    credit_sum NUMERIC(19, 4);
BEGIN
    SELECT
        COALESCE(SUM(CASE WHEN entry_type = 'debit'  THEN amount END), 0),
        COALESCE(SUM(CASE WHEN entry_type = 'credit' THEN amount END), 0)
    INTO debit_sum, credit_sum
    FROM journal_lines
    WHERE journal_entry_id = NEW.journal_entry_id;

    IF debit_sum <> credit_sum THEN
        RAISE EXCEPTION 'Unbalanced journal entry: debits=% credits=%',
            debit_sum, credit_sum;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Balance computation: derive account balances from journal lines
CREATE VIEW account_balances AS
SELECT
    a.id AS account_id,
    a.code,
    a.name,
    a.account_type,
    a.currency,
    SUM(CASE WHEN jl.entry_type = 'debit'  THEN jl.amount ELSE 0 END) AS total_debits,
    SUM(CASE WHEN jl.entry_type = 'credit' THEN jl.amount ELSE 0 END) AS total_credits,
    CASE
        WHEN a.account_type IN ('asset', 'expense')
            THEN SUM(CASE WHEN jl.entry_type = 'debit' THEN jl.amount ELSE -jl.amount END)
        ELSE
            SUM(CASE WHEN jl.entry_type = 'credit' THEN jl.amount ELSE -jl.amount END)
    END AS balance
FROM accounts a
LEFT JOIN journal_lines jl ON jl.account_id = a.id
GROUP BY a.id, a.code, a.name, a.account_type, a.currency;

-- Index for fast balance queries and idempotency lookups
CREATE INDEX idx_journal_lines_account ON journal_lines(account_id, created_at);
CREATE INDEX idx_journal_entries_idempotency ON journal_entries(idempotency_key);
```

**Idempotent Journal Entry Creation** (Python):

```python
from decimal import Decimal
from uuid import uuid4
import psycopg

def post_journal_entry(
    conn: psycopg.Connection,
    idempotency_key: str,
    description: str,
    lines: list[dict],
    created_by: str,
) -> str:
    """Post a balanced journal entry with idempotency protection.

    Each line: {"account_id": str, "amount": Decimal, "entry_type": "debit"|"credit", "currency": str}
    """
    # Validate balance before hitting the database
    debits = sum(l["amount"] for l in lines if l["entry_type"] == "debit")
    credits = sum(l["amount"] for l in lines if l["entry_type"] == "credit")
    if debits != credits:
        raise ValueError(f"Unbalanced entry: debits={debits} credits={credits}")

    with conn.transaction():
        # Idempotency: return existing entry if key already used
        row = conn.execute(
            "SELECT id FROM journal_entries WHERE idempotency_key = %s",
            (idempotency_key,),
        ).fetchone()
        if row:
            return row[0]

        entry_id = str(uuid4())
        conn.execute(
            "INSERT INTO journal_entries (id, idempotency_key, description, created_by) "
            "VALUES (%s, %s, %s, %s)",
            (entry_id, idempotency_key, description, created_by),
        )
        for line in lines:
            conn.execute(
                "INSERT INTO journal_lines (journal_entry_id, account_id, amount, entry_type, currency) "
                "VALUES (%s, %s, %s, %s, %s)",
                (entry_id, line["account_id"], line["amount"],
                 line["entry_type"], line["currency"]),
            )
        return entry_id
```

**Key Ledger Design Principles**:

- Journal entries are append-only. Never update or delete a posted entry. To correct an error, post a reversing entry
- Every journal entry must balance (total debits = total credits) within the same currency
- Use idempotency keys on every write path to prevent duplicate postings from retries
- Store amounts as `NUMERIC(19, 4)` in PostgreSQL, never as `FLOAT` or `DOUBLE PRECISION`
- Derive balances by aggregating journal lines, not by storing a mutable balance field
- Include metadata (source system, external reference IDs) on every entry for auditability
