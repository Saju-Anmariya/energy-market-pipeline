# Security test: Energy Market API

## Scope
Automated test of the read-only API in this repository with OWASP ZAP (API scan). The API ran in Docker on a GitHub Actions runner. Only my own API was tested.

## Method
The workflow `.github/workflows/security-scan.yml` builds the image, starts the API, and lets ZAP read `openapi.json` and test every endpoint. The workflow is started manually. The full reports are in the `security/` folder.

## Results

| Scan | Failures | Warnings | Passed checks | Report |
|---|---|---|---|---|
| Before the fix | 0 | 2 | 118 | `security/report-before.md` |
| After the fix | 0 | 0 | 120 | `security/report-after.md` |

## Findings and fixes

| Finding | Risk | Fix |
|---|---|---|
| X-Content-Type-Options header missing (10021) | Low | Added `X-Content-Type-Options: nosniff` to all responses |
| Cross-Origin-Resource-Policy header missing or invalid (90004) | Low | Added `Cross-Origin-Resource-Policy: same-origin` |

I also added `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer` as general hardening. A test in `tests/test_api.py` checks that the headers are present.

## What passed
Among others: server-side code injection, remote OS command injection (including the time-based variant), XML external entity attacks, server-side template injection, and application error disclosure.

## Limitations
- This is an automated baseline scan, not a full penetration test
- The API has no login and no rate limiting, because it serves public data only
- No Content-Security-Policy is set, because the interactive docs page (`/docs`) loads scripts from an external server. In production I would disable `/docs` and add a strict policy
- HTTPS and HSTS must be provided by the hosting platform

## Lessons learned
- A workflow that is started manually does not run on new commits. My first re-scan tested the old code, which I found by comparing the run list with the commit history. The workflow now prints the tested commit and the response headers, so this is visible in the log.