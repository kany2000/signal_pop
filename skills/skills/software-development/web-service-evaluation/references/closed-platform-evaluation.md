# Closed-Platform Evaluation

Not all web services claim to be open. Some are legitimately closed-source Web UI only — no API, no SDK, no developer program. This reference covers how to conclusively determine "no programmatic access exists", with exemplars.

## Target Profile

| Attribute | Signal |
|-----------|--------|
| No `/docs`, `/api`, `/developer` routes | 404 or redirect to homepage |
| `robots.txt` has `Disallow: /api/` | Explicit API block |
| All `api/graphql`, `api/trpc`, `api/v*` routes → 403 | Server-side rejection |
| No OpenAPI spec at `/openapi.json`, `/api/openapi.json`, `/.well-known/openapi.json` | No public spec |
| No GitHub org / no public repos | No OSS backend |
| Cloudflare Managed Challenge on deep navigation | Enterprise bot protection |

## Exemplar: arena.ai

| Property | Finding |
|----------|---------|
| Type | AI Model Arena (LMSYS-style leaderboard + comparison) |
| Tech | Next.js App Router, tRPC, React, reCAPTCHA Enterprise, Cloudflare |
| Public API | **None** — all `/api/*` return 403 |
| OpenAPI | Not found at any standard path |
| GitHub | `github.com/arena-ai` org exists but 0 public repos |
| Playwright homepage | ✅ Loads (shows model leaderboard rankings) |
| Playwright /leaderboard | ❌ Cloudflare Managed Challenge blocks |
| curl API | All `POST /api/graphql`, `POST /api/trpc` → 403 |
| Programmatic | **Impossible** — browser-only human-facing UI |

## Investigation Sequence

```
1. curl landing page    → 200 ok, get meta tags
2. curl /api/* routes   → if 403 → server blocks, not missing
3. curl /openapi.json   → 404 confirms no public spec
4. robots.txt           → Disallow: /api/ confirms intentional
5. Playwright homepage  → loads? check title + body text
6. Playwright deep nav  → blocked by CF? if yes → enterprise-grade
7. GitHub org search    → 0 repos = closed source
```

## Verdict: When to Stop Trying

| Signal Set | Verdict | Action |
|------------|---------|--------|
| 403 on all /api/* + no OpenAPI + CF Managed Challenge | **Closed platform** | Tell user, move on |
| 404 on /api/* + JS bundles have no fetch patterns | **Dead end** | Abandon |
| Some endpoints work but gated by CAPTCHA/ad | **Partial** | Document working subset |