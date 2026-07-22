# vibe-app — 🦙 Alpaca Meadow

A peaceful idle game for the GTM hands-on enablement exercise (issue #284):
an alpaca ambles across a meadow — press **Space** or **click** to graze, and
every few tufts of grass a new plant sprouts into your collection.

Matches the #284 reference stack exactly: **cloudflared · web · workers · PostgreSQL · Redis**.

## How the stack does real work

| #284 layer  | Compose service | Role in the game                                     |
|-------------|-----------------|------------------------------------------------------|
| application | `web`           | FastAPI — serves the game, `/eat`, `/walk`, `/state` |
| workers     | `worker`        | RQ — sprouts a new plant every 8 grass eaten         |
| PostgreSQL  | `db`            | persists grass eaten, distance walked, collected plants |
| Redis       | `redis`         | fast live grass counter + the job queue              |
| cloudflared | `cloudflared`   | public quick-tunnel URL                              |

## Run (inside the Ubuntu VM)

```bash
cp .env.example .env
docker compose up -d --build
```

```bash
curl -s localhost:8000/healthz     # -> {"ok":true}
docker compose logs cloudflared | grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com'
```

Open that `*.trycloudflare.com` URL and graze. 🌿

## Deploy

Push to `master` → GitHub Actions runs `deploy.sh` on the VM through Alpacon
(`git pull` + `docker compose up -d --build`), no SSH. See `.github/workflows/deploy.yml`.

The quick-tunnel hostname changes on every restart (ephemeral demo link).
