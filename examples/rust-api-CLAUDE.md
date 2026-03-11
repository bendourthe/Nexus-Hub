# Rust REST API

A Rust REST API using Axum, Tokio async runtime, SQLx for database access (PostgreSQL), and serde for serialization. Built as a single binary for deployment.

## Tech Stack
- **Language**: Rust (stable, edition 2021)
- **Package Manager**: Cargo
- **Build**: `cargo build --release`
- **Test**: `cargo test` (built-in), `cargo nextest` (faster runner)
- **Lint/Format**: `clippy`, `rustfmt`

## Project Layout
```
src/
  main.rs             # Entry point; sets up Axum router and binds
  config.rs           # Config from environment variables
  db.rs               # SQLx pool setup
  error.rs            # Unified error type (thiserror)
  routes/
    mod.rs
    <resource>.rs     # Handler functions per resource
  models/
    mod.rs
    <resource>.rs     # Domain types + sqlx::FromRow derives
  services/           # Business logic (no DB/HTTP concerns)
  middleware/         # Auth, tracing, rate limiting
migrations/           # SQL migration files (sqlx-cli)
tests/
  integration/        # Full HTTP integration tests
Cargo.toml
Cargo.lock
.env.example
```

## Key Commands
```bash
# Build (debug)
cargo build

# Build (release)
cargo build --release

# Run tests
cargo nextest run

# Lint
cargo clippy -- -D warnings

# Format
cargo fmt

# Run migrations
sqlx migrate run

# Run dev server
cargo run
```

## Non-Obvious Tooling
- Use `cargo-watch` for hot reload: `cargo watch -x run`
- `sqlx` compile-time query checking requires `DATABASE_URL` set in `.env` and `cargo sqlx prepare` to be run before commits (generates `sqlx-data.json` for offline mode)
- `cargo nextest` is significantly faster than `cargo test` for large test suites
- `tower-http` provides `TraceLayer` for request tracing — add it to all routers
- Use `color-eyre` for user-facing error reporting in binaries; `thiserror` for library error types

## Rust Conventions
- Every public function must have doc comments (`///`)
- Use `#[must_use]` on functions returning `Result` or `Option`
- Prefer `?` over `unwrap()` or `expect()` in library and handler code; `expect()` is acceptable only in startup/init code with a descriptive message
- Avoid `clone()` on large types in hot paths — use references or `Arc`
- Use `tracing` macros (`tracing::info!`, `tracing::error!`) not `println!` or `eprintln!`
- All handler functions should return `Result<impl IntoResponse, AppError>` using the unified error type
- Database queries belong in repository functions in `routes/` or a dedicated `db/` module, never inline in handlers
- `Serialize` / `Deserialize` derives are the standard; manual impls require a comment justifying them

## Communication Style
- Place punctuation outside quotation marks (logical punctuation)
- No em-dashes; use parentheses, commas, or separate sentences
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Critical Rules
- Verify work before marking complete
- Find root causes; no temporary fixes
- Destructive git commands require user confirmation
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- **MANDATORY: Every Bash/shell command approval MUST be preceded by a one-sentence plain-language explanation** of what the command does and what its impact will be. This applies to ALL commands regardless of complexity. No exceptions.
- Ask clarifying questions before coding if requirements are ambiguous

## Output Minimization
- Prefer `cargo nextest run --no-fail-fast -q`; report only failures and counts
- Suppress `cargo build` output unless there are warnings or errors

## Context References
- Skills: `.claude/skills/` (auto-activated by task context)
- Architecture: `.claude/context/architecture.md`
- Decisions: `.claude/memory/decisions.md`
- Agents: `.claude/agents/` (specialized subagents for code review, TDD, security)
