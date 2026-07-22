# vibe-app — URL Health Board

Reference vibe-coded app for the GTM hands-on enablement exercise (issue #284).
Matches the #284 reference stack exactly: **cloudflared · web · workers · PostgreSQL · Redis**.

**What it does:** submit a URL on the web page → the request is queued to Redis →
a background worker fetches the URL and records its HTTP status + latency in
PostgreSQL → the web page lists the results.

## Layer → service map

| #284 layer      | Compose service | Image / build            |
|-----------------|-----------------|--------------------------|
| application     | `web`           | FastAPI + uvicorn        |
| workers         | `worker`        | RQ worker                |
| PostgreSQL      | `db`            | postgres:16-alpine       |
| Redis           | `redis`         | redis:7-alpine           |
| cloudflared     | `cloudflared`   | cloudflare/cloudflared   |

## Run (inside the Ubuntu VM)

```bash
cp .env.example .env
docker compose up -d --build
```

Wait ~30s for images to build, then:

```bash
# local check (from the VM or host, via the VM IP)
curl -s localhost:8000/healthz        # -> {"ok":true}

# get the public URL (quick tunnel, no Cloudflare account needed)
docker compose logs cloudflared | grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com'
```

Open that `*.trycloudflare.com` URL in a browser — that satisfies completion bar #1
(app reachable through a cloudflared URL).

## Useful commands

```bash
docker compose ps                 # service status
docker compose logs -f worker     # watch jobs run
docker compose down               # stop (keeps data volume)
docker compose down -v            # stop + wipe Postgres data
```

The quick-tunnel hostname changes every restart. For a stable hostname you'd use a
named Cloudflare tunnel with a token — out of scope for this exercise.
