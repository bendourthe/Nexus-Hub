---
title: Choose the primary datastore
status: accepted
---

# Choose the primary datastore

## Context

We need a primary datastore for the API service.

## Decision

We will use PostgreSQL over MySQL for its JSONB support and mature tooling.

## Consequences

Operations must run a managed PostgreSQL cluster.
