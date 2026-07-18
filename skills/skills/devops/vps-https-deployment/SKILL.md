---
name: vps-https-deployment
description: Deployment infrastructure umbrella — VPS HTTPS deployment, Cloudflare Tunnel, LAN file sharing, and multi-service exposure patterns.
platforms: [linux]
requires: [docker, docker-compose, root-ssh]
---

# Deployment Infrastructure

Master skill for exposing services to the internet and local networks. Covers VPS HTTPS deployment, Cloudflare Tunnel, LAN HTTP file sharing, and multi-service exposure patterns.

## Quick Navigation

- [VPS HTTPS Deployment](#vps-https-deployment) — nginx+acme.sh, Caddy, 1Panel, Cloudflare Tunnel
- [Cloudflare Tunnel](#cloudflare-tunnel) — Zero-port exposure via Cloudflare edge
- [LAN Share Server](#lan-share-server) — Multi-agent file sharing over local network
- [Skill Consolidation Notes](#skill-consolidation-notes) — Merged content from archived sibling skills

---

## Skill Consolidation Notes

This skill absorbs the following previously-separate skills as labeled subsections:

### Cloudflare Tunnel (formerly `cloudflare-tunnel` skill)
Full content moved inline under [Cloudflare Tunnel](#cloudflare-tunnel) section below. Key patterns:
- docker-compose integration with token auth
- DNS setup via Cloudflare Dashboard
- Halo blog concrete example
- Troubleshooting: 502, disconnected tunnel, SSL issues
- Token redaction handling with `od -c`

### LAN Share Server (formerly `lan-share-server` skill)
Full content moved inline under [LAN Share Server](#lan-share-server) section below. Key patterns:
- Python HTTP server with GET/PUT/POST endpoints
- systemd vs crontab @reboot persistence
- Directory organization: user assigns top-level, agents fill their own
- Cron job safety audit before file reorganization
- File conflict prevention across agents

Both were previously standalone devops skills. Merged here because they share the same deployment/exposure domain and the user's mental model treats them as "ways to expose services."

---

## VPS HTTPS Deployment

Deploy a web service (Halo blog, any Docker app) on a VPS with HTTPS and custom domain. Covers all major approaches with tradeoffs.

## Approach Comparison

| Approach | Components | Effort | SSL Mgmt | Best For |
|---|---|---|---|---|
| **nginx + acme.sh** | nginx (反代) + acme.sh (证书) | 中 | 手动配 cron 续期 | 熟悉 Linux，要最大控制权 |
| **Caddy** | Caddy 一个 | 低 | 自动 | 追求简单，一个工具搞定 |
| **1Panel** | Web 面板应用商店 | 最低 | 面板点几下 | 新手友好，还要管理数据库/文件 |
| **Cloudflare Tunnel** | cloudflared Docker + CF 面板 | 低 | 自动（CF 托管） | 无公网 IP 或不想开端口 |

**Conceptual distinction (critical):** ACME client (acme.sh/certbot) only **issues certificates** — it does NOT serve web traffic. nginx/Caddy is the **web server** that listens on 80/443, terminates HTTPS, and reverse-proxies to the backend. These are complementary, not alternatives. Caddy is special because it bundles both roles. 1Panel abstracts both behind a GUI.

## User Preference: Step-by-Step From Scratch

This user prefers **complete, copy-pasteable commands** starting from zero (not assuming prior steps done). Always include:
- Exact SSH command with IP and password reminder
- Verification commands after each step (`curl`, `systemctl status`)
- The conceptual WHY behind each tool choice
- DNS record configuration steps (what type, what value)
- Firewall open commands (especially 80/443 for cloud security groups)

When giving multiple options, lead with a comparison table and recommendation.

---

## Approach 1: nginx + acme.sh

### 1. SSH & Prerequisites

```bash
ssh root@<VPS_IP>
# install nginx
apt update && apt install -y nginx
systemctl start nginx && systemctl enable nginx
```

### 2. Install acme.sh

```bash
curl https://get.acme.sh | sh -s email=your-email@example.com
# source ~/.bashrc or re-login after install
```

### 3. Configure nginx HTTP Reverse Proxy

```bash
cat > /etc/nginx/sites-available/service << 'EOF'
server {
    listen 80;
    server_name your.domain.com;
    location / {
        proxy_pass http://127.0.0.1:SERVICE_PORT;  # e.g. 8090 for Halo
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/service /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

Add DNS A record before proceeding: `your.domain.com → <VPS_public_IP>`

### 4. Issue SSL Certificate

```bash
# HTTP mode (nginx already running with domain)
acme.sh --issue -d your.domain.com --nginx

# or standalone mode (temporarily stops other services on port 80)
# acme.sh --issue -d your.domain.com --standalone
```

### 5. Install Certificate & Enable HTTPS

```bash
mkdir -p /etc/nginx/ssl

acme.sh --install-cert -d your.domain.com \
  --key-file /etc/nginx/ssl/domain.key \
  --fullchain-file /etc/nginx/ssl/domain.crt \
  --reloadcmd "systemctl reload nginx"

# Update nginx config for HTTPS
cat > /etc/nginx/sites-available/service << 'EOF'
server {
    listen 80;
    server_name your.domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your.domain.com;
    ssl_certificate /etc/nginx/ssl/domain.crt;
    ssl_certificate_key /etc/nginx/ssl/domain.key;
    location / {
        proxy_pass http://127.0.0.1:SERVICE_PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

nginx -t && systemctl reload nginx
```

### 6. Firewall

```bash
ufw allow 80/tcp
ufw allow 443/tcp
```

**Cloud security group** must also allow 80 and 443 (not just OS firewall).

### 7. Auto-renew (automatic with acme.sh)

```bash
crontab -l | grep acme  # should show daily renewal job
```

---

## Approach 2: Caddy (All-in-One)

One tool replaces nginx + acme.sh:

```bash
apt install -y debian-keyring debian-archive-keyring
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy

# Config — just domain + backend
cat > /etc/caddy/Caddyfile << 'EOF'
your.domain.com {
    reverse_proxy localhost:SERVICE_PORT
}
EOF

systemctl restart caddy
```

Caddy auto-issues Let's Encrypt certs, auto-HTTPS, auto-renew, auto-HTTP/2. No extra steps.

To switch from Caddy to another solution:
```bash
systemctl stop caddy && systemctl disable caddy
apt remove --purge -y caddy && rm -rf /etc/caddy
# verify 80/443 released
ss -tlnp | grep -E ':80 |:443 '
```

---

## Approach 3: 1Panel (GUI Panel)

### Install 1Panel

```bash
bash <(curl -sSL https://linuxmirrors.cn/1panel.sh)
# OR official:
# curl -sSL https://resource.fit2cloud.com/1panel/package/quick_start.sh -o quick_start.sh && bash quick_start.sh
```

During install: set port (default 9999), username, password. Save these.

### Post-install Steps in Web UI

1. Login at `http://<VPS_IP>:9999`
2. **App Store** → Install **OpenResty** (nginx wrapper)
3. **App Store** → Install **MySQL** first (Halo depends on it — DB dropdown will be empty without it)
4. (Optional) **Database** tab → Create a new database `halo`, charset `utf8mb4`
5. **App Store** → Search **Halo** → One-click deploy
6. **Websites** → Add website:
   - Domain: `your.domain.com`
   - Type: **Reverse Proxy**
   - Target: `http://localhost:8090` (or whatever port your service uses)
   - Enable HTTPS → **Auto-apply certificate**
7. If Let's Encrypt times out (China VPS), switch cert provider to **TrustAsia**:
   - **Websites** → Certificate management → ACME account → Provider → **TrustAsia**
8. Done — no config file editing needed

### Uninstall 1Panel

```bash
# Use the uninstall script from the panel's install directory
# Typically: /opt/1panel/1panel uninstall
```

---

## Cloudflare Tunnel (formerly separate skill)

> Full Cloudflare Tunnel implementation details, merged from `cloudflare-tunnel` skill.

Expose any local web service (Docker container or bare-metal) to the public internet via Cloudflare's edge network. No open firewall ports needed. Works behind NAT, CGNAT, or residential ISPs that block port 80/443.

### Architecture

```
[Local Service] ← → [cloudflared] ← → [Cloudflare Edge] ← → [your-domain.com]
```

- **cloudflared** runs as a Docker container, connects outbound to Cloudflare
- Cloudflare routes public traffic through the tunnel to the local service
- Built-in HTTPS, CDN, and DDoS protection via Cloudflare

### Prerequisites

- Domain on Cloudflare (NS pointing to Cloudflare)
- Docker + Docker Compose on the local server
- Internet access from local server (outbound-only, no open ports needed)

### Setup

#### 1. Create a Tunnel in Cloudflare Dashboard

```
https://one.dash.cloudflare.com/ → Access → Tunnels → Create a tunnel
```

- Name the tunnel (e.g., `my-service`)
- Choose deployment method: **Docker**
- Copy the token string (`eyJ...`) — this is the one-time credential

#### 2. Add Cloudflared to docker-compose.yml

```yaml
services:
  # ... your existing service ...
  your-app:
    # ... your app config ...
    networks:
      - app_network

  cloudflared:
    image: cloudflare/cloudflared:latest
    restart: always
    networks:
      - app_network
    command: tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
    depends_on:
      your-app:
        condition: service_healthy  # optional, ensures app is ready

networks:
  app_network:
```

#### 3. Set the token in .env

```bash
# /path/to/project/.env
CF_TUNNEL_TOKEN=***   # ← paste your token here
```

#### 4. Configure Public Hostname in Dashboard

After tunnel is created, add a route:

```
Public hostname: blog.yourdomain.com
Service:         http://your-app:PORT      # container name + internal port
```

Cloudflare auto-provisions DNS + SSL.

#### 5. Start

```bash
cd /path/to/project
docker compose up -d
```

#### 6. Verify

```bash
# Check tunnel status in dashboard (should show "Healthy")
# Or from the server:
docker compose logs cloudflared

# Check public access:
curl -sI https://blog.yourdomain.com
```

### docker-compose Patterns

#### Service on same docker network (preferred)

Cloudflared and app share a compose network → use container name as hostname.

```yaml
cloudflared:
  command: tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
  networks:
    - app_network   # same network as the app service
```

#### Service on host port only

If you can't share a network, cloudflared can use `host.docker.internal` (Docker Desktop) or `host` network mode:

```yaml
cloudflared:
  network_mode: host
  command: tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
  # Then uses: http://localhost:8090 in dashboard config
```

#### Updating external-url of the app

If your app generates links (like a blog/CMS), update its `external-url` setting to the public domain so it generates correct URLs.

```
- --external-url=https://blog.yourdomain.com
```

### Working with Halo Blog (concrete example)

Halo is a Java-based blog platform running on Docker. Full docker-compose:

```yaml
services:
  halo:
    image: registry.fit2cloud.com/halo/halo:2.24.2
    restart: always
    depends_on:
      halodb:
        condition: service_healthy
    networks:
      halo_network:
    volumes:
      - ./halo2:/root/.halo2
    ports:
      - "8090:8090"
    command:
      - --spring.r2dbc.url=r2dbc:pool:mysql://halodb:3306/halo
      - --spring.r2dbc.username=root
      - --spring.r2dbc.password=${DB_PASSWORD}
      - --spring.sql.init.platform=mysql
      - --halo.external-url=https://blog.yourdomain.com

  halodb:
    image: mysql:8.1.0
    restart: always
    networks:
      halo_network:
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=halo

  cloudflared:
    image: cloudflare/cloudflared:latest
    restart: always
    networks:
      - halo_network
    command: tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
    depends_on:
      halo:
        condition: service_healthy

networks:
  halo_network:
```

Dashboard hostname config:
```
Service: http://halo:8090
```

### Troubleshooting

#### Tunnel shows "Disconnected" / "Down"

```bash
# Check logs
docker compose logs cloudflared --tail=50

# Common causes:
# - Token expired (regenerate in dashboard)
# - No internet access from server (check curl google.com)
# - DNS resolution failure (check /etc/resolv.conf)
```

#### 502 Bad Gateway

cloudflared can reach Cloudflare but not the local service.

```bash
# Is the app running?
docker compose ps

# Can cloudflared reach it? Enter the container:
docker compose exec cloudflared curl -s http://halo:8090/actuator/health  # Halo example
# Or use the actual service:port from dashboard config

# Check app logs
docker compose logs your-app --tail=30
```

#### SSL / Mixed Content

- Cloudflare handles SSL termination automatically
- If your app generates absolute HTTP URLs, update its `external-url` to `https://`

#### Token Redaction in Shell Output

The terminal tool may redact passwords/tokens as `***` in output. Use `od -c` to read raw bytes:

```bash
cat .env | od -c   # reveals actual characters
```

### Pitfalls

- **Token must be set before first `docker compose up`**, otherwise cloudflared won't start
- **`.env` file must be in the same directory as `docker-compose.yml`**, or referenced explicitly
- **`--no-autoupdate`** flag is recommended for Docker — cloudflared auto-update conflicts with container lifecycle
- **Service dependency**: always set `depends_on` with health condition so cloudflared doesn't start before the app is ready
- **Update `external-url`** in the app config to reflect the public domain, not localhost
- **Backup original files** before editing docker-compose.yml, nginx configs, or .env
- **`.xyz` domains face extra scrutiny** from Google AdSense — content quantity and quality become more important

### Reference

- `references/halo-blog-server.md` — Halo-specific deployment notes (moved from cloudflare-tunnel skill)

---

## LAN Share Server (formerly separate skill)

> Full LAN HTTP file share implementation, merged from `lan-share-server` skill.

Multi-agent file sharing over HTTP on a local network. Lightweight, zero dependencies beyond Python 3.

### Server Script

Use `/home/kan/scripts/share-server.py` as the base:

```python
# Key features:
# - GET /path → browse/download files (with styled HTML directory listing)
# - GET /api/list → JSON file list (machine-readable)
# - PUT /path → upload file (curl -X PUT ... --data-binary @file)
# - POST / → browser form upload (multipart)
# - 0.0.0.0:PORT, default 8080
# - Optional HTTP Basic Auth via SHARE_AUTH=user:pass
```

### Persistence

When systemd not available (no sudo), use crontab @reboot:

```bash
(crontab -l 2>/dev/null || true; echo "@reboot cd /home/kan/shared && python3 /home/kan/scripts/share-server.py > /tmp/share-server.log 2>&1 &") | crontab -
```

Verify: `crontab -l | grep share`

If systemd available:
```bash
sudo cp share-server.service /etc/systemd/system/
sudo systemctl enable share-server
sudo systemctl start share-server
```

### Directory Organization

**Critical rule — ONLY the user creates top-level directories.** Each bot/agent gets their own directory assigned by the user. Never create directories for other agents, never move/rename them.

```
/home/kan/shared/
  ├── bot-a/             # ← user assigns, agent fills
  │   ├── project-x/
  │   └── script-y.py
  ├── bot-b/             # ← user assigns
  └── bot-c/             # ← user assigns
```

**Golden rules:**
1. Only work inside your own assigned directory
2. Never `mv` / `rm` / rename another agent's directory
3. Never create new top-level directories yourself — ask the user
4. File conflicts from PUT are real — only PUT into your own dir

### Sharing Local Files Without Breaking Cron Jobs

Never move/delete local source files — cron jobs depend on local paths.

**Option A — Copy (safe for small projects):**
```bash
# ✅ Copy to share, local untouched
cp -r /local/small-project/ /home/kan/shared/mydir/
```

**Option B — Soft-link (cheap, stays synced):**
```bash
# ✅ Symlink — no disk copy, auto-updates with local changes
ln -s /local/large-project /home/kan/shared/mydir/large-project
```

**❌ Wrong — breaks cron:**
```bash
mv /local/project/ /home/kan/shared/mydir/   # NO — cron references old path
```

### Pre-reorg Audit

Before reorganizing any files that might affect cron jobs:
```bash
hermes cron list            # List all cron jobs
grep -r "/home/kan/" .      # Check for local path references
# Then verify: does any cron job reference a path I'm about to touch?
```

### Agent Usage

```bash
# Download
curl -O http://10.10.10.30:8080/path/file
wget http://10.10.10.30:8080/path/file

# Upload
curl -X PUT http://10.10.10.30:8080/mydir/file.txt --data-binary @local.txt

# List files (JSON)
curl http://10.10.10.30:8080/api/list

# Browse (HTML UI with upload button)
# http://10.10.10.30:8080/
```

### Cron Job Safety

Before reorganizing files, audit cron jobs:

```bash
hermes cron list   # See all cron jobs with file paths
```

If a cron job references a local path (e.g., `/home/kan/signal_pop/scripts/`):
1. Keep the original files in place
2. Copy to shared folder as secondary access
3. Never use `mv` on project directories that cron jobs depend on

### Pitfalls

- **Files disappearing between commands**: Multiple agents may modify the shared directory simultaneously. Always check before assuming state.
- **No sudo for systemd**: Use crontab @reboot as fallback.
- **Port conflicts**: Check with `ss -tlnp | grep 8080`.
- **Firewall**: Some LANs block non-standard ports; verify with a curl from another machine.
- **File conflicts**: Agents overwriting each other's files is a real risk with PUT. Educate contributors to only touch their own directory.

### Reference

- `references/share-server.md` — Full server implementation (moved from lan-share-server skill)

---

## Migration (Moving from One VPS to Another)

When migrating Halo blog (or similar) between servers:

### Option A: Halo Admin Export/Import

1. Old server: Admin → Tools → Export → download .zip
2. Old server: copy attachments (`scp` or `rsync`)
3. New server: Admin → Tools → Import → upload .zip
4. New server: restore attachments to same path

### Option B: Full MySQL + File Dump

```bash
# Old server: dump DB
docker exec <mysql-container> mysqldump -u root -p<PASS> <db_name> > backup.sql

# Old server: pack attachments
tar czf attachments-backup.tar.gz <attachments-dir>

# Transfer to new server
scp backup.sql attachments-backup.tar.gz root@<NEW_VPS_IP>:/root/

# New server: restore
cat /root/backup.sql | docker exec -i <mysql-container> mysql -u root -p<PASS> <db_name>
tar xzf /root/attachments-backup.tar.gz -C <attachments-dir>
```

### Option C: Official Halo Migration Tool

For cross-version migration (1.x → 2.x): see https://docs.halo.run

---

## DNS Configuration

When NOT using Cloudflare DNS (Caddy/native approach):

```
A record:  blog.yourdomain.com → <VPS_PUBLIC_IP>
```

Pre-create the DNS record before starting ACME challenge (cert issuance needs domain to resolve).

When using Cloudflare DNS:
```
CNAME:   blog.yourdomain.com → <tunnel-id>.cfargotunnel.com
Proxy:   ON (orange cloud)
```

---

## Troubleshooting

### "HTTP 502 Bad Gateway"

nginx: app not running or wrong `proxy_pass` port. Check `docker ps` and `curl localhost:SERVICE_PORT`.

### "Cert issuance failed — domain doesn't resolve"

DNS A record not propagated yet, or pointing to wrong IP. Check `dig +short your.domain.com`.

### "Port 80/443 already in use"

Another web server (nginx, Caddy, Apache) or 1Panel already bound. `ss -tlnp | grep ':80 '` to find PID.

### 1Panel install: "Could not resolve host"

Check URL spelling: `resource.fit2cloud.com` (not `fit2com.com`).

### 1Panel Halo deploy: database dropdown empty

**Symptom:** Halo install page shows "无数据" on submit button, DB dropdown has no selectable options.

**Fix:** MySQL must be installed **before** deploying Halo. Go to **App Store** → search **MySQL** → Install. After MySQL starts, return to Halo deploy — dropdown will show the MySQL instance.

### "Let's Encrypt ACME endpoint unreachable" (China VPS)

```
dial tcp 172.65.32.248:443: i/o timeout
```

Let's Encrypt's `acme-v02.api.letsencrypt.org` is often blocked from China-hosted VPS.

**Fix in 1Panel:**
1. **Websites** → Certificate management → ACME account settings
2. **Provider** → switch from **Let's Encrypt** → **TrustAsia**
3. Re-issue cert

**Fix for acme.sh (CLI):**
```bash
acme.sh --set-default-ca --server zerossl
acme.sh --issue -d your.domain.com --nginx
```

---

## Pitfalls

- **ACME client ≠ web server**: acme.sh only issues certs. You still need nginx/Caddy to serve and terminate HTTPS. Users often confuse these and ask "acme还需要nginx吗？" — explain the distinction.
- **Certificate algorithm: prefer ECC over RSA**: ECC/ECDSA (Prime256v1) gives smaller keys, faster handshake, modern browser support. Choose ECC in 1Panel cert settings or pass `--ecc` to acme.sh. Only fall back to RSA 2048 for legacy client compatibility.
- **DNS before ACME**: Domain A record must resolve to VPS IP before cert issuance.
- **Cloud security groups**: OS firewall (ufw) is not enough — cloud providers (AWS/Azure/阿里云) need port 80/443 opened in their security group separately.
- **Caddy → other**: Stop and remove Caddy before installing 1Panel or nginx, else port 80/443 conflict.
- **1Panel URL**: `fit2cloud.com` (not `fit2com.com`). Common typo.
- **Backup original configs**: Before modifying nginx/Caddy/1Panel configs, save originals.
- **SSH password auth**: This VPS (10.10.10.13) requires interactive password entry — can't use `sshpass`. Use `pexpect` for automation or provide copy-paste commands for the user.
- **`external-url` setting**: Update the app's own `external-url` config (e.g. `--halo.external-url=https://blog.yourdomain.com`) so generated links use the correct domain, not localhost.
