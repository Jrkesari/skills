# Product map: what can be filmed, and how to say it

Verified in October 2026. UI copy drifts between films, so run `scripts/capture/explore.py` on each screen before writing a flow. The model picker showed retired Claude names, and that ended up in the film.

## Naming and brand

- **Netision** is the company (LinkedIn page `netision-technology`). **Netigen** is the platform and brand, at netigen.ai. Every app's browser title is "Netigen". netision.com does not mention the products.
- Brand: violet `#7C3AED`. Fonts: Inter, Instrument Serif italic (accent words) and JetBrains Mono (kickers). The mark is the 3 paths from the netigen repo's `packages/ui/src/components/logo.tsx`, already extracted to `scripts/shared/netigen-mark.svg`. Extract it from source; never redraw it.

## The four layers (website labels, website order nexus, naper, nimbus, neuron; the film used Naper, Nexus, Neuron, Nimbus)

| Layer | Label | Film-safe description | Source in the film |
|---|---|---|---|
| Naper | Enterprise context | The admin console: who gets which agents, apps and models; groups, members and seats, spend (cost) limits, connector apps, identity, guests, feature access. Business processes are rolling out, so never claim them. | Live (group dialog). Website scene for seats and limits. |
| Nexus | AI workspace | Ask in plain words, live web search with cited sources, a slide deck from the answer, scheduled tasks, connectors (Outlook, Gmail, Zoho...), notebook, workspaces, assets. | Live |
| Neuron | Enterprise intelligence | Answers from your business: enterprise knowledge (vocabulary, metric rules and tables as a semantic layer, plus indexed documents), reasoning (questions compile into checked, read-only queries; the model never writes the figure), AI agents (sales, root-cause, social, PulseWatch market watch). AI Service Packs and Memory are "rolling out" or "soon": never claim them. | Website `/platform` Neuron scene, as stepped stills |
| Nimbus | Trust & observability | What every answer cost, how fast it came back, how people rated it. Agent and LLM performance, token usage, trust, feedback, logs. Admin only. | Website `NimbusLayerScene` (the live one holds real data) |

## Nexus (localhost:3000)

- Routes: `/` (home: "Where should we start today?"), `/agents`, `/apps`, `/assets`, `/chats/<id>`, `/notebook`, `/scheduled`, `/scheduled/<id>`, `/workspaces/<slug>`. Every route needs a session.
- Composer: a textarea, `Add assets` (+), Chat / Agent buttons (use exact=True), and a model button matching `^LLM: ` (default GPT-5.4; opening an existing chat brings the default back). Picker providers: Anthropic, Google, NVIDIA, OpenAI, Sarvam AI, TII, xAI. Never name a model in the VO that the picker does not show.
- The sidebar user chip shows the name and department: blur it, or keep it out of frame.
- Answer footer: Copy, Add to notebook, Good / Bad response, Share, `<N> sources` (matches `^\d+ sources$`, use `.last`), `<N> tools used`, Turn details.
- Citations: chips are `a.not-typeset`, and one HoverCard moves between chips. Hover each for about 2.6-3.5 s and keep the most legible card (chip 0 opened over the prompt and cut it).
- Deck: the answer shows a file with a `Preview` button. Wait **15 s or more** after clicking it. Scroll the slides with `mouse.wheel(0,700)` over x=1550 (land) or x=540,y=1300 (port). Close with Escape ×3 plus `Close`. A deck answer can include "The slides were not rendered ... LibreOffice was unavailable": frame it out, or record on a stack with LibreOffice.
- Scheduled: placeholder "Describe a task and when it should run". The templates are Morning sales brief, Weekly root-cause digest, Morning inbox summary, Power BI KPI snapshot and Industry news watch. A specific prompt returns a TaskConfirm card with `Create task` in about 8-30 s. Hover `Create task`; never click it. The prompt that worked: "Every weekday at 8 AM, search the web for the five most important GCC retail news stories of the last 24 hours and summarise each one with its source."
- Connectors: Add assets > menuitem `Apps` (hover) > `Outlook` (exact, `.last`). The connector needs a fresh sign-in.
- Turn times at GPT-5.6: research about 26-48 s, deck alone about 80 s, research plus deck in one turn 2-4 min (wait timeout 900 s), mail draft about 5 s.
- Prompts that worked: "What are the three biggest shifts in GCC retail this quarter? One line each, with sources." and "Research the three biggest shifts in GCC retail this quarter and turn them into a 5-slide deck for our leadership team, with sources."

## Naper (localhost:3002)

- Routes: `/`, `/members`, `/groups`, `/platform/organizations`, `/platform/personal-users`, `/platform/plans`, `/platform/limits`, `/settings/features`, `/settings/limits` (Cost Limits), `/settings/connector-apps`, `/settings/identity`, `/settings/guests`, `/power-agent/*`. A single-tenant stack shows only Overview, Members, Groups, Features and Power Agent.
- Group dialog (`/groups` > `Add`): name placeholder "Finance", description placeholder "Who is in it and what they work on", then an inherit switch (`[role=switch], [data-slot=switch]`). Turning the switch off reveals "What this group gets": agents (Aggregator IQ, Location Feasibility, Geo Analyst, Social Analyst, RCA, Sales, PulseWatch), connectors (Microsoft, Google, Zoho, Databricks), features and models. Take events: overview, groups, dialog, named, inherit-off, agents-picked, connectors-picked, scrolled, save-hover. Hover `Save Group`, then click `Cancel`. The film chip read "Finance gets 3 of 7 agents".
- Add Organization dialog: it has no ARIA dialog role, so use page-level `get_by_placeholder(..., exact=True)` with 'Acme', '25' and 'it@example.com' (never acme.com). Fill it, take the still, then Cancel.
- Real data risk: Members, Guests (invite links are live credentials), Identity (tenant and client IDs) and the overview greeting. Use the website's Naper scene for members, seats and limits.

## Nimbus (localhost:3003)

- Routes: `/`, `/agent/performance-v2`, `/cost/efficiency`, `/llm/performance`, `/trust/overview`, `/user/feedback-overview`, `/user/logs`, `/user/token-usage`. A non-admin sees "Access denied / Only admins can open Nimbus." On a multi-org stack, an org admin gets Agent Performance, LLM Performance, Cost Overview and Token Usage. A super admin also gets Trust Overview, User Feedback, User Logs, Per Query and an Organization selector. The site description reads "AI observability for the Netigen agent platform". The home subtitle reads "A live snapshot of trust, cost, and usage across your AI agents."
- Live Nimbus reads a remote ClickHouse holding **real** data. Even blurred, the charts gave away the model mix and success rates. Always use the website's `NimbusLayerScene` (console home, Cost Overview, Agent Performance, User Logs trace).

## netigen.ai website scenes (localhost:3107)

- Gallery: `/dev/scenes?only=<Scene>`. Scenes: NimbusLayerScene (console home, Cost Overview, Agent Performance matrix, User Logs trace), NaperLayerScene (overview, members with seats badge and inline group select, the org's offer of agents, connectors and models, spend limits), NexusLayerScene, ObservabilityScene (the Nimbus Token Usage page: tiles, cost and tokens per person, then Per Model), GovernanceScene, PlatformScene. Each `.tsx` has a `TIMELINE` of step times in ms and a `description=` prop saying what the scene shows.
- The stage box at a 1920×1080 viewport is x=366, y=106, w=796, h=440 CSS (find it by walking up from the Pause button until its height is 300 or more). Wait for `[aria-label^='Pause'], [aria-label^='Play']`.
- Neuron: `/platform`. Locate it with `document.querySelector('[aria-label$="Neuron demo"]')` and walk up the parents. Scroll to target-2000 and then to target so it replays from step 0. Step stills at [0.25, 1.6, 3.6, 6.4, 8.6, 11.4] s.
- Scenes show demo data (Maya Chen, example.com, demo dollar figures), which is fine to show unblurred. The site's own pause button must be patched out.
- Website pages are desktop-shaped. In portrait, give them a page-shaped window rather than cropping through columns.
