---
date: 2026-10-13
tags: [learning, area/testing]
---
# Test each adapter with the same suite
A parametrised pytest fixture runs one behaviour suite against every adapter of a port (here: InMemoryLedger and DynamoLedger via `moto.mock_aws`). It proves the DynamoDB conditional writes match the reference behaviour without touching AWS.

**Why:** The DynamoDB ledger's security fixes were untested until moto ran them.
**How to apply:** For each new adapter (e.g. AthenaRepository), add it to the existing suite's fixture params instead of writing a separate test file.

Related: [[Learnings]]
