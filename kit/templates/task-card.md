---
id: AUTH-1
title: Login API
epic: Authentication
role: developer
toolset: backend
playbooks: [backend]
wave: 1
risk: high            # high: gets a reviewer under review: risky. normal: no reviewer.
needs: [AUTH-0]
owns: [app/api/auth/*, app/db/migrations/002_users.sql]
---

## Goal
Users can log in with email and password and get a session.

## Context
Read only these, plus the files you own:
- app/contracts/auth.ts: AuthRequest / AuthResponse (don't change them)
- app/contracts/errors.ts: error format
- mad/SPEC.md → "Login"

## Done when
- POST /login returns a session for valid credentials
- Wrong password returns 401 in the format of app/contracts/errors.ts
- Tests for both cases pass (paste output)
