# Repos, services and health checks

Find each repo's local clone at run time (`git remote get-url origin` in the user's projects folder). Ask for its location if you cannot find it. Never hard-code a local path.

## Repos

| Repo | URL | Notes |
|---|---|---|
| netigen (monorepo) | https://github.com/netisionhq/netigen | Next.js apps under `apps/`: nexus, auth, naper, nimbus, api (Hono + Prisma + Better Auth). Convex backend. Needs Node 24+ and pnpm 11. Brand sources: `packages/ui/src/components/logo.tsx` (the mark: 3 paths, viewBox 0 0 234 233), `packages/ui/src/styles/shadcn.css` (light tokens), `packages/ui` fonts, `packages/assets`, `DESIGN.md`. Chat citations: `packages/chat-renderer/src/citation.tsx`. |
| netigen-draft | https://github.com/netisionhq/netigen-draft | FastAPI agent backend that every Nexus turn runs through. |
| netigen-mcp | https://github.com/netisionhq/netigen-mcp | MCP tool server: web_search, web_fetch, create_presentation, create_pdf, and more. |
| netigen-backend-core | https://github.com/netisionhq/netigen-backend-core | Shared LLM library. `models.yaml` holds the model names the Nexus picker shows. |
| netision-website | https://github.com/netisionhq/netision-website | netigen.ai site (TanStack Start + Vite + nitro; the branch used was `redesign/tanstack-start`). Product scenes live in `src/components/scenes/*Scene.tsx`, the dev gallery at `/dev/scenes?only=<Scene>`, layer pages at `/platform` and `/platform#neuron`. Layer copy and "soon" flags are in `src/content.ts` and `public/llms.txt`. The site only has dark tokens (`src/styles/app.css`). |
| hyperframes | https://github.com/heygen-com/hyperframes | Apache-2.0 video framework, pinned at `hyperframes@0.8.134`. Its skills are installed into the film project. |

Reference skills read while choosing the framework (references only): https://github.com/memex-lab/product-launch-video-skill, https://github.com/Vincentwei1021/video-shotcraft, https://github.com/ahmdd4vd/MotionCraft, https://github.com/remotion-dev/skills. Remotion needs a paid company licence for Netision, which is why HyperFrames is the default.

## Local stack (ports)

| Service | Port | Start (ask the user first) | Health check |
|---|---|---|---|
| Nexus | 3000 | netigen: `pnpm dev --filter=nexus --filter=auth --filter=naper --filter=nimbus --filter=api` (background) | `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/` |
| auth (sign-in) | 3001 | same | An unauthenticated Nexus request returns 307 to `localhost:3001/?to=nexus` |
| Naper | 3002 | same | HTTP 200 |
| Nimbus | 3003 | same | HTTP 200 (admin only) |
| api (Better Auth) | 3100 | same | `/api/auth/get-session` with the cookie returns `{session,user}` |
| Convex | 3210 / 3211 | netigen: `pnpm nexus:db` (background) | `http://127.0.0.1:3210/version` |
| netigen-draft | 8001 | netigen-draft: `.venv/Scripts/python.exe main.py` (background) | `http://127.0.0.1:8001/health` returns 200. An open port does **not** prove health: draft once hung with the port open. |
| netigen-mcp | 8004 | netigen-mcp: `.venv/Scripts/python.exe main.py --http` (the README's `server.py` does not exist). Browser tools need `uv run playwright install chromium`. | `http://127.0.0.1:8004/health` |
| netision-website | **3107** | netision-website: `npx vite dev --port 3107 --strictPort` (background; first load takes about 10 s while the Vite optimizer runs) | `http://localhost:3107/` |

Five-port readiness loop (run in the background):

```bash
for i in $(seq 1 240); do ok=0; for p in 3000 3001 3002 3003 3100; do curl -s -o /dev/null -m 2 http://localhost:$p/ && ok=$((ok+1)); done; [ $ok -eq 5 ] && exit 0; sleep 2; done
```

## Known failure modes

- **Port clash on 3100.** The website's Vite on `[::1]:3100` (IPv6) next to netigen's api on `0.0.0.0:3100`. Node's fetch resolves `localhost` to `::1` first, so the server-side calls reached Vite and got HTML: every page redirected to sign-in, with "fetch failed", "Unexpected token '<'" and "Session has expired". curl over IPv4 still looked healthy. Check with `netstat -ano | grep ':3100 .*LISTEN'`: two PIDs on one port means a clash. See what each is with `Get-CimInstance Win32_Process -Filter "ProcessId=<pid>"`. Reproduce with `node -e "fetch('http://localhost:3100/...')"`, not curl.
- **Backends die mid-batch.** Convex or mcp stopped and Nexus flows timed out at 30 s (`Locator.click`). Health-check all ports before every capture batch.
- **Draft hung.** Nexus showed "Couldn't generate a response" while the port stayed open. Kill it with `Stop-Process -Id <pid> -Force`, restart it from its own venv, and poll `/health` (about 33 s to come back). Healthy log lines: "Application startup complete", "[warehouse] ... ready", "netigen-draft agent ready".
- **Orphaned capture processes.** TaskStop on a background bash job does not kill the Python children it started. Run `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'flow_|stills' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -Confirm:$false }`.
- **Never run `next build`** while the dev servers run: it wipes their output. Never `uv sync` a venv that a running service uses.
- **Expired connectors.** A Microsoft refresh failure (`FAILED_TO_REFRESH_ACCESS_TOKEN`, `AADSTS7000222` invalid_client) means no mail card. Pages still load. Cut the scene.
- Harmless log noise: google refresh failed, azure_databricks refused, zoho-token missing consent.
- Memory is tight (about 2-4 GB free of 24 GB). Use `--workers 2` for renders.
