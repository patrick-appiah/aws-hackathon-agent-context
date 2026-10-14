---
date: 2026-10-14
status: done
tags: [decision, status/done, area/repo, area/frontend]
---
# Two apps in one repo: Python at the root, Angular in `web/` (D-020)
## Decision
Option A. Nothing moves: the Python back end stays at the root and the Angular front end (Mildred, PR #12) lives in `web/` with its own `package.json`, `yarn.lock` and README. Node 22 is pinned (`web/.nvmrc`, `engines`, Jenkins `node:22`). `web/.npmrc` maps the private `@amalitechnpm` scope with no token; developers keep the read-only token in their home `~/.npmrc` (two lines: npmjs and yarnpkg), and Jenkins uses `cloud9-npm-token`.
## Why
Keeps every open branch and PR valid mid-hackathon; the apps meet only at the HTTP API. A clean clone couldn't install the front end (404 on the private package) and Node wasn't pinned.
## Rejected
`backend/` + `web/` (revisit after the event); Nx/Turborepo; a separate front-end repo; a root Makefile; `${NPM_TOKEN}` lines in a committed `.npmrc`; layout guard tests (the lead ruled them out).
## Verified
With the lead's token in the WSL home `~/.npmrc`: a clean clone runs `yarn install --frozen-lockfile` (12 s), `yarn build` (427.54 kB initial) and `yarn test` (25 files, 69 tests) green; Python suite 140 passed. `engines` widened to Angular's range (`^22.22.3 || ^24.15.0`) after review.

Related: [[Decisions]], [[Repo]], [[Dev loop]]
