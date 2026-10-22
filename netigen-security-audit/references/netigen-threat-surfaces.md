# Netigen threat surfaces

The repo-specific review for step 3. Each surface states the invariant, where it is enforced, and the concrete way it breaks. Read the repo's `CLAUDE.md` section for the surface first - it is the intended model, and a finding is a gap between it and the code. File paths are netigen-draft unless noted.

A surface that matches the model is a clean result; record it in one line and move on. Spend effort where input reaches a sink without passing a check.

## 1. Authorization and ownership

**Invariant:** A caller can only act on their own message, chat, workspace, notebook and documents. Draft takes no inbound user credential - it relies on network placement plus the ownership checks.

- `src/api/ownership.py` - refuses a forged or foreign id before the 202. Confirm the check runs **before** `bind_turn` and before the agent branch, not after a block is written.
- `DRAFT_OWNERSHIP_CHECKS` defaults off. Audit both states: off, every turn is accepted (intended only on a stack whose Convex lacks the scope routes). Flag any deployment doc that leaves it off against a Convex that has the routes.
- Fail-open vs fail-closed: a row with **no** `userId` passes and is logged; a **mismatched** `userId` is refused. Confirm the code does exactly that - a fail-open on a mismatch is a cross-user read (Critical).
- Service secrets: `CONVEX_API_KEY` (`convex-secret` header) and `x-schedule-secret` (`DRAFT_SCHEDULE_SECRET`). The Convex `/api/*` routes bypass user authorization - confirm they are never proxied to end users, and the secret is compared safely (constant-time where it matters) and never logged.
- `GET /api/messages/:id/scope`, `/notebook/:id/access`, `/workspace-context` - confirm each refusal is a 404 with nothing written, and that `resolve_query_documents` drops a document whose `userId` is another user's.

**Breaks when:** an id is trusted before the scope check; a mismatch fails open; a scope route is reachable with a user-supplied id; a secret is logged or compared non-safely.

## 2. Delegated-token handling

**Invariant:** The provider access token arrives with the request, is held for the request only, and is forwarded **only** to the tagged connector's own tools on `DRAFT_MCP_TOKEN_HEADER`. It is never stored, logged, put in block data, sent on a web search, or passed as a tool argument.

- `src/draft/tools/mcp_client.py`, `src/draft/tools/registry.py` - trace the token from `/query` to the tool call. Confirm it travels as a header keyed by the tool's `provider:` tag, never as a model-settable argument.
- `_GRAPH_FALLBACK` - confirm the Graph token is lent only to `microsoft`/`powerbi`/untagged, never widened to `google`, `zoho`, `databricks`.
- Grep for the token reaching a sink: log lines, `blocks.data`, `sources`, web-search args, exception messages. Any of these is token leakage (High/Critical).
- `expires_at` handling - an expired or missing token fails with a connector-named message, not a raw provider 401 and not a silent skip.

**Breaks when:** the token is read into a log/block/exception; one connector's token reaches another's tool; the model can set the token via an argument.

## 3. LLM-written SQL

**Invariant:** Model-written SQL runs on a read-only DuckDB connection with external access disabled and locked, and is checked to be one read-only query touching only the conversation's / caller's tables.

- `shared/db_utils.py` - `_disable_external_access` sets `enable_external_access=false` then `lock_configuration=true`, and `connect()` opens `read_only=True`. Confirm the **order**: external access is disabled before the connection is usable, and the temp-dir is set before hardening locks config. Note the file's own warning that `read_only` blocks writes but not `read_csv()` lifting a local file - so external access off is load-bearing.
- `src/agents/catalog.py:244` `check_sql` - runs the model SQL through DuckDB's parser on a probe connection with `enable_external_access=False`, held to the catalog's views. Confirm it rejects multiple statements, writes, and tables outside the allow-list.
- `query_table` (draft documents path) - confirm the same: one read-only query, only that conversation's tables.

**Breaks when:** hardening runs after the connection is usable; a second statement slips through; the allow-list is matched loosely (substring) so a sibling table is reachable; `read_csv`/`read_parquet` on a local path is not blocked.

## 4. Prompt-injection and destructive-command guards

**Invariant:** Request guards run once at the root before routing, so every agent is covered. The guard reads **both** `prompt` (app-root field) and `query` (sub-app field).

- `src/api/middleware.py`, `register_security(app)` in `main.py` - confirm rate limits, body/prompt caps, the destructive-command guard and the prompt-injection guard are wired at the root and read `prompt`. A guard that reads only `query` no-ops on the endpoint everything goes through (High).
- `CONTENT_MODERATION_ENABLED` defaults off - note it, and that its pattern whitelist is a bitten-phrase list, not general protection. Do not recommend turning it on blindly (it blocks ordinary analytics language).
- Confirm the guards cannot be bypassed by an alternate field name or content type.

**Breaks when:** a guard reads only one of the two body fields; a new route is added that skips `register_security`; a cap is absent so an oversized body or prompt reaches the model.

## 5. Connector gating

**Invariant:** The request's `connectors` list is the whole gate. `[]` offers none; absence is never "all". It gates **dispatch** as well as the offer.

- Confirm a model naming an off connector's tool is refused ("{label} is not connected"), not run on a Graph token another connector brought.
- Confirm switching a connector off removes both the tool offer and the ability to dispatch it.

**Breaks when:** the gate is applied to the offer only, so a model that names the tool anyway reaches it; absence is treated as "all".

## 6. Approval cards

**Invariant:** A tool tagged `requires_approval` or `write` is never called from the tool loop. It parks a card; only the card's Send click runs it, through nexus to `POST /actions`, which re-checks the block is the caller's, re-checks the tag, and claims the card `sending` so a second click is a no-op.

- `src/draft/documents/query_pipeline.py` (`_APPROVAL_ELEMENTS`, `_execute`) and mcp's `/actions` (`run_action`) - confirm nothing the model writes reaches `/actions`, so the model cannot approve its own call.
- Confirm an unattended (scheduled) run is never offered an approval tool, and no `write`/`requires_approval` tool is dispatched there.
- Confirm the `sending` claim is atomic so a double-click sends once.
- Connector routing on the card: `connector` is set from the tool's own tag and is in `_CARD_PROPS` (never reaches the tool); `run_action` refuses (409) a card whose `connector` is not its tool's. Confirm a model-invented argument cannot route one account's token to the other's tool.

**Breaks when:** a write/approval tool is callable from the loop; `/actions` trusts a model-supplied field; the sending claim is not atomic; a scheduled run can reach an approval tool.

## 7. SSRF and external fetch

**Invariant:** Any fetch of a user- or model-influenced URL re-resolves every redirect hop against private IP ranges, and localhost / internal hosts are refused.

- `web_fetch`, drive ingest (`src/draft/documents/drive_ingest.py`), and nexus's `/api/link-preview` + `/api/link-icon` (note these live in nexus, not these repos - flag for the nexus review, don't audit here).
- Confirm `web_fetch` while a foreign skill is loaded opens only an address in the prompt or a this-turn search result (`registry._foreign_skill`).
- Confirm no fetch follows redirects into the private network unchecked.

**Breaks when:** a redirect is followed with `redirect: "follow"` and no per-hop re-resolution; an internal host (metadata endpoint, localhost, RFC1918) is reachable.

## 8. File and URL handling

**Invariant:** A generated file is fetched by id, never by a public storage link. The storage URL never reaches `blocks.data`; bytes are re-hosted via Convex and the block carries `{documentId, filename, contentType, size}`.

- `_persist_files` / `_persist_preview` - confirm the storage URL goes no further than the fetch, and a file that cannot be filed renders as a `File` block with `status: "error"`, not a fallback link.
- Confirm a tool result returns a URL/id, never the file bytes (bytes in tool output get re-sent every round).
- Convex `/api/files/<documentId>` re-checks the session on every hit - confirm no unauthenticated, non-expiring link ends up in message history.

**Breaks when:** a storage URL lands in block data or a tool result; a generated file is served by a link with no auth/expiry.

## 9. Secrets and config

**Invariant:** No credential is hardcoded; every secret comes from env; `.env.example` documents them without values.

- gitleaks / detect-secrets over tree and history (step 2). Triage each hit - report file:line and "secret", never the value.
- Confirm no default `localhost` or secret is baked into code where a missing env should fail loudly instead.
- `LLM_WARMUP_ENABLED`, `SALES_RLS_ENABLED`, `DRAFT_OWNERSHIP_CHECKS` and other security-relevant defaults - confirm each default is the safe one or is documented as intentional.

**Breaks when:** a key is committed; a secret has a code default; history holds a secret even if the tree does not.

## 10. Core security wrappers (netigen-backend-core)

**Invariant:** The confidentiality line is appended to the **first** system message only, not every one. The LLM proxy ends `_request_kwargs` with `kwargs.update(extra)` so a per-call value overrides the model entry - confirm nothing lets a caller override a security-relevant setting.

- `netigen_backend_core.llm.security` - confirm one copy of the confidentiality line (three copies read as a prompt-extraction jailbreak and get blocked). This is pinned by core's `tests/test_llm_security_wrappers.py`.
- Confirm the usage/attribution path sets the user context at the boundary so no spend is logged against a literal `"draft"` with no user (correctness + abuse-tracing).
- A flaw here is a flaw in every repo that pins core - weight accordingly.

**Breaks when:** the confidentiality line stacks per system message; a per-call override can turn off a guard; attribution is unset so actions are untraceable.
