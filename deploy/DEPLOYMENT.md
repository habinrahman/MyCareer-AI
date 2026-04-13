# MyCareer AI — DigitalOcean Droplet deployment

This guide deploys the **Next.js** frontend, **FastAPI** backend, **Nginx** reverse proxy, and **Let’s Encrypt** TLS using Docker Compose on a single Ubuntu droplet (1 GB RAM minimum recommended; 2 GB is more comfortable for builds).

## What you get

| Component | Role |
|-----------|------|
| `api` | FastAPI + Uvicorn (2 workers), internal port 8000 |
| `web` | Next.js standalone `node server.js`, internal port 3000 |
| `nginx` | TLS termination, HTTP → HTTPS, proxies to `web` / `api` by hostname |
| `certbot` | Periodic `certbot renew` via webroot |

TLS uses a **single SAN certificate** named `mycareer-ai` covering both `APP_HOST` and `API_HOST`.

## 1. Create the Droplet

1. In DigitalOcean, create a **Droplet** (Ubuntu 22.04 or 24.04 LTS).
2. Choose SSH keys, enable **Monitoring** if you like.
3. Note the **public IPv4** (and IPv6 if you use it — update DNS accordingly).

## 2. DNS

Create **A** records (and **AAAA** if you use IPv6):

| Host | Target |
|------|--------|
| `APP_HOST` (e.g. `app.example.com`) | Droplet IP |
| `API_HOST` (e.g. `api.example.com`) | Droplet IP |

Wait for DNS to propagate before running Let’s Encrypt.

## 3. Server preparation

SSH in as root or a sudo user:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${VERSION_CODENAME:-jammy}") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and back in so `docker` works without `sudo`.

Optional **firewall** (allow SSH, HTTP, HTTPS only):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 4. Clone the app

```bash
sudo mkdir -p /opt/mycareer-ai
sudo chown "$USER":"$USER" /opt/mycareer-ai
cd /opt/mycareer-ai
git clone https://github.com/YOUR_ORG/ai-mentor.git .
# or: scp/rsync your project tree here
```

## 5. Environment files

From the repo root:

```bash
chmod +x deploy/scripts/*.sh
./deploy/scripts/bootstrap-env.sh
```

Then edit:

1. **`.env`** — `APP_HOST`, `API_HOST`, `LETSENCRYPT_EMAIL`, and `NEXT_PUBLIC_*` (especially `NEXT_PUBLIC_API_URL=https://YOUR_API_HOST`).
2. **`backend/.env`** — `OPENAI_API_KEY`, `SUPABASE_*`, `DATABASE_URL`, `SUPABASE_JWT_SECRET`, and **`CORS_ORIGINS`** including `https://YOUR_APP_HOST` (comma-separated if multiple).
3. **`frontend/.env.production`** — same `NEXT_PUBLIC_*` as in root `.env` (used at container runtime; the **image** still bakes in values from compose **build args**, which come from root `.env`).

**Important:** After changing any `NEXT_PUBLIC_*` value, rebuild the web image:

```bash
docker compose build web --no-cache && docker compose up -d web
```

## 6. Build and start

```bash
docker compose build
docker compose up -d
```

Check containers:

```bash
docker compose ps
docker compose logs -f --tail=100 api
```

You should see the app on **http://APP_HOST** and API on **http://API_HOST** (plain HTTP until certificates exist).

## 7. Let’s Encrypt (HTTPS)

When DNS resolves to this server:

```bash
./deploy/scripts/init-letsencrypt.sh
```

The script:

1. Starts `api`, `web`, and `nginx` (HTTP bootstrap with ACME webroot).
2. Runs `certbot certonly --webroot` for both hostnames with cert name **`mycareer-ai`**.
3. **Restarts** `nginx` so the entrypoint switches to the **phase 2** template (HTTPS).

Renewals: the `certbot` service runs `certbot renew` on a loop. Nginx continues to serve `/.well-known/acme-challenge/` on port 80 after phase 2.

## 8. Day-two deploys

After `git pull` and env changes:

```bash
./deploy/scripts/deploy.sh
```

## Local development (no Nginx / no TLS)

Publish API and web on localhost and skip Nginx/Certbot:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.dev.yml up -d
```

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:3000`

Use `backend/.env` and local `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` for the browser.

## Supabase dashboard

Under **Authentication → URL configuration**, add:

- Site URL: `https://APP_HOST`
- Redirect URLs: `https://APP_HOST/auth/callback`

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `certbot` fails HTTP-01 | DNS, port 80 open, `docker compose logs nginx` |
| Browser CORS errors | `CORS_ORIGINS` in `backend/.env` includes `https://APP_HOST` |
| 502 from Nginx | `docker compose ps`, `docker compose logs api web` |
| Next.js calls wrong API | Rebuild `web` with correct `NEXT_PUBLIC_API_URL` build arg |

## File reference

| Path | Purpose |
|------|---------|
| `docker-compose.yml` | Production stack |
| `deploy/docker-compose.dev.yml` | Overrides for local published ports |
| `deploy/docker/nginx/` | Custom Nginx image + phase 1/2 templates |
| `deploy/scripts/bootstrap-env.sh` | Copy example env files |
| `deploy/scripts/init-letsencrypt.sh` | First TLS issuance |
| `deploy/scripts/deploy.sh` | Rebuild + `up -d` |
| `backend/Dockerfile` | API image |
| `frontend/Dockerfile` | Next standalone image |

The legacy `deploy/nginx.example.conf` is a static reference; the running config is generated inside the **nginx** container from `deploy/docker/nginx/templates/`.
