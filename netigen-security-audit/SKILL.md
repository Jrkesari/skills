---
name: netigen-security-audit
description: White-box security audit of the netigen backend repos (netigen-draft, netigen-mcp, netigen-backend-core). Reads the source read-only, runs static scanners (bandit, pip-audit, gitleaks, semgrep), then reviews the repo-specific threat surfaces - authorization and ownership checks, delegated-token handling, LLM-written SQL, the prompt-injection and command guards, connector gating, approval cards, SSRF and file handling - grades findings by user impact, and reports the full list before any fix. Use when the user asks to security-audit, pentest, threat-model or find vulnerabilities in draft, mcp or core. Not for attacking a live or third-party system, writing exploits, or a plain code-quality pass (use deep-code-review) or dependency-only scan (use sca-audit).
---

# Netigen security audit

**Audience:** The owner of netigen-draft, netigen-mcp and netigen-backend-core, auditing their own code before a release or after a security-relevant change.

**Goal:** Find security weaknesses in these three repos and report them ranked by real user impact, with the file and line behind each, so the owner can decide what to fix.

## Hard rules

1. **Authorized, own-code only.** This audits repos the user owns. It never targets a live deployment, a third party, or anyone else's data.
2. **Read-only and defensive.** Read source, run static scanners, reason about weaknesses. Do not run exploits, craft attack payloads, send traffic at a running service, or write offensive tooling. This is white-box review, not a black-box attack.
3. **Report before fix.** Produce the complete findings list first and let the user see it. Fix or file issues only after that, and only for what the user approves. Follow the user's "report the full list first" rule from `sca-audit`/`deep-code-review`.
4. **No secrets in output.** If a scanner surfaces a real credential, report the file and line and that it is a secret - never paste the secret value into chat, a report, or an issue.
5. **Evidence, not assertion.** Every finding names a file and line and states a concrete failure path. A weakness you cannot point at in the source does not go in the report.

## When to use this skill

- "Security-audit / pentest / threat-model draft (or mcp, or core)."
- "Find vulnerabilities / security bugs in these repos."
- Before a release, or after changing auth, tokens, tools, SQL, guards, connectors or approval flow.

## Do NOT use when

- Attacking a running or third-party system, or writing exploit code - decline; this skill is white-box only.
- The user wants a general code-quality / dead-code pass - use `deep-code-review`.
- The user wants only a dependency CVE scan - use `sca-audit` (this skill calls it as one step).
- The user wants to verify metering/attribution - use `token-audit`.

## Repos

Audit all three unless the user names a subset. Paths below assume this layout.

| Repo | Role | Security weight |
|---|---|---|
| netigen-draft | The FastAPI app: `/query`, `/ingest`, agents, tools, skills | Highest - holds auth, tokens, LLM-SQL, guards, approvals |
| netigen-mcp | The shared tool server: web, file generation, connectors, `/files`, `/actions` | High - runs tool calls, serves files, holds connector tokens in-flight |
| netigen-backend-core | Shared library: LLM proxy, Convex I/O, security wrappers, usage, vectorstore | High - a flaw here is a flaw in every repo that pins it |

Resolve each repo path from the session's working directories, or ask. Read `CLAUDE.md` in each repo first - it documents the intended security model, and a finding is a gap between that model and the code.

## Workflow

Run the stages in order. Stages 1-2 are mechanical; stage 3 is where the repo-specific findings come from.

### Step 1: Map the attack surface

For each repo, before any scanner:

1. Read `CLAUDE.md` - it states the intended security model (what each check is for, what fails open vs closed, what must never be logged or forwarded). This is the spec you audit against.
2. List the HTTP routes (`main.py`, `src/api/`, any router) and mark which ones take untrusted input, which bypass user authorization, and which forward a credential.
3. Note the trust boundaries: frontend -> draft, draft -> mcp, draft/mcp -> core, service -> Convex, model-written content -> any sink.

Write this map down; it tells you where in stage 3 to look hardest.

### Step 2: Static scanners

Run with `uvx` so nothing is installed into the repos. Full commands and how to read each tool's output are in [references/static-analysis.md](references/static-analysis.md). In short, per repo:

- **bandit** - Python security linter (eval, subprocess, weak crypto, SQL build-up, bind-all, asserts).
- **pip-audit** (or call the `sca-audit` skill) - known-vulnerable dependencies in the uv lockfile.
- **gitleaks** / **detect-secrets** - secrets committed to the tree or history.
- **semgrep** (optional, `--config auto`) - taint patterns bandit misses (SSRF, injection, path traversal).

Static output is **leads, not findings**. Every hit is triaged in stage 3: confirmed against the code and the threat model, or dropped as a false positive with a one-line reason.

### Step 3: Repo-specific threat-surface review

This is the core of the audit and is mostly manual. Work through [references/netigen-threat-surfaces.md](references/netigen-threat-surfaces.md), which lists each surface, the file to read, the invariant that must hold, and the concrete way it breaks. The surfaces:

1. Authorization and ownership (`src/api/ownership.py`, scope checks, the service secrets, fail-open/closed).
2. Delegated-token handling (never stored, logged, in block data, or a tool argument; forwarded only to the tagged connector).
3. LLM-written SQL (DuckDB read-only + locked, statement allow-listing, scope to the conversation's tables).
4. Prompt-injection and destructive-command guards (`src/api/middleware.py`; reads `prompt` and `query`; what is off by default).
5. Connector gating (the request's `connectors` list is the whole gate, for dispatch as well as the offer).
6. Approval cards (`write`/`requires_approval` tools never run from the tool loop; the Send click re-checks ownership and tag).
7. SSRF and external fetch (`web_fetch`, drive ingest, link-preview redirect re-resolution).
8. File and URL handling (file by id not public link; storage URL never in block data; generated bytes re-hosted).
9. Secrets and config (hardcoded credentials, env handling, what `.env.example` implies).
10. Core security wrappers (the confidentiality line added once vs per message; the prompt-shield interaction).

For each surface: state the invariant, point at where it is enforced, then try to find an input or path that reaches the sink without passing the check. Where the code matches the model, say so briefly and move on - a clean surface is a result, not a gap to pad.

### Step 4: Grade and report

Grade every confirmed finding by **user impact**, not by scanner severity:

| Severity | Meaning |
|---|---|
| Critical | Cross-user data access, credential disclosure, or unauthenticated action on another user's data |
| High | Authz bypass needing a non-default config, token leakage into a store/log, model-driven write with no approval |
| Medium | SSRF/injection bounded by an existing guard, info leak with limited blast radius |
| Low | Hardening gap, defence-in-depth missing, risky default |

Report with the structure in [references/report-template.md](references/report-template.md): the full ranked list first, each finding with repo, file:line, the invariant it breaks, and the concrete failure path. State which surfaces were clean. Do not file issues or change code yet.

### Step 5: Fixes and issues (only after the user sees the list)

- The user picks what to act on. Nothing before that.
- A fix ships in the repo that owns the flaw (a core flaw ships in core, per that repo's release rules). Respect each repo's branch/PR rules.
- When filing GitHub issues, file them on the repo that ships the fix, title by impact, and never include a secret value.

## Dependencies

- `uvx` (bundled with `uv`) to run scanners with nothing installed into the repos.
- `gh` CLI for filing issues, when the user asks for that.
- Related skills: `sca-audit` (dependency CVEs, called in step 2), `deep-code-review` (quality pass), `bug-rca` (hand it a filed issue number for the root cause and fix PR), `token-audit` (metering).
- Reference docs: each repo's `CLAUDE.md` is the security model this audit measures against.
