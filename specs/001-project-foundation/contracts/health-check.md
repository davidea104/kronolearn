# Health Check Contract

Canonical contract for the baseline health endpoint used across documentation and CI.

- Route: `/healthz`
- Method: `GET`
- Success Response: HTTP 200
- Body: JSON `{ "status": "ok" }`
- Content-Type: `application/json`
- Acceptance: health checks that validate critical subsystems (DB connectivity, required env vars) should return 200; if any critical subsystem fails, return 503 and `{ "status": "degraded" }`.

Location canonical: `specs/001-project-foundation/contracts/health-check.md` (referenciar desde docs y tests).
