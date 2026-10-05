# Phase 7: Production Deployment (Oracle Cloud VM, Nginx, Redis & SSL)

---

## 1. What We Just Built (Plain English Summary)

In Phases 0 through 6, we built a fully featured, reactive real-time chat application with multi-room isolation and online user presence tracking running locally on Windows.

In Phase 7, we took the entire application from `localhost` and **deployed it live to the public internet** on a high-performance cloud architecture:
1. **Oracle Cloud Infrastructure (OCI) ARM VM:** Provisioned a 64-bit Ampere ARM virtual machine (`VM.Standard.A1.Flex`) running Canonical Ubuntu 24.04 LTS under Oracle's Always Free tier in Frankfurt, Germany.
2. **Dynamic DNS Mapping (DuckDNS):** Tied the VM's public IP address (`130.61.9.37`) to the domain **`ybchatapp.duckdns.org`** via DuckDNS's automated HTTP API.
3. **Dual-Layer Firewall Configuration:**
   - *Cloud Level:* Opened Ingress Rules for Ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) in the Oracle Cloud Security List.
   - *Host Level:* Configured and persisted Ubuntu's internal `iptables` firewall to accept TCP ports 80 and 443 before the general reject rule.
4. **Server Software Stack:** Installed Python 3.12, Redis 7.0, Nginx 1.24, Certbot, and Git on ARM64 Linux.
5. **Channels Redis Channel Layer:** Enabled `USE_REDIS=True` so messages and room groups broadcast through Redis across processes.
6. **24/7 Background Daemon (`systemd`):** Created and enabled `chat-app.service` to manage the Daphne ASGI server with auto-restart on crash and auto-boot on server restart.
7. **Nginx Reverse Proxy & SSL Termination:**
   - Reverse-proxies HTTP requests to Daphne on local port 8001.
   - Upgrades `/ws/` WebSocket connections to persistent, 2-way pipes with 24-hour read timeouts.
   - Directly serves 131 bundled static CSS/JS assets from `staticfiles/` with a 30-day browser cache.
8. **Automated Trusted SSL/TLS (Let's Encrypt):** Used Certbot to issue a trusted SSL certificate, enabling HTTPS (`https://`) and secure WebSockets (`wss://`) with automatic 90-day background renewal and permanent HTTP-to-HTTPS redirects.

---

## 2. Commands Executed and What Each Did (In Order)

For the detailed, unified narrative and execution breakdown of every single command, refer to the companion manual:  
👉 **[`docs/deployment_commands_log.md`](../deployment_commands_log.md)**

A high-level summary of the sequence:
1. **Network Probe:** Tested port 22 connectivity from Windows to the VM IP using `Test-NetConnection`.
2. **DuckDNS API Call:** Bound `ybchatapp.duckdns.org` to `130.61.9.37` via `curl`.
3. **DNS Validation:** Queried `Resolve-DnsName` to confirm global DNS propagation.
4. **Windows Key Lockdown:** Used `icacls` to restrict `ssh-key-2026-10-05.key` exclusively to `YOBI\YOBI`, satisfying OpenSSH requirements.
5. **First SSH Handshake:** Executed `uname -a; lsb_release -a` over SSH to confirm administrative access to Ubuntu 24.04 ARM64.
6. **OS Firewall Configuration:** Inserted `ACCEPT` rules for ports 80 and 443 into `iptables` and saved them permanently with `netfilter-persistent`.
7. **Package Installation:** Installed `python3-venv`, `redis-server`, `nginx`, `certbot`, `python3-certbot-nginx`, and `git` via `apt`.
8. **Repository Deployment:** Cloned `softdevbrian/Chat-App` into `/home/ubuntu/chat_server`, built the Python virtual environment, installed `requirements.txt`, applied SQLite migrations, and executed `collectstatic`.
9. **Daphne Service Setup:** Installed `deploy/chat-app.service` to `/etc/systemd/system/`, enabled it on boot, and started Daphne on `127.0.0.1:8001`.
10. **Nginx & SSL Provisioning:** Configured `/etc/nginx/sites-available/chat_app`, obtained a Let's Encrypt certificate with `certbot --nginx`, and granted `chmod 755 /home/ubuntu` for static asset delivery.

---

## 3. Production Architecture Deep-Dive

```
                      [ USER CLIENTS ]
             (Mobile Browsers, Desktop, Next.js)
                             │
                             │ HTTPS / WSS (Port 443)
                             ▼
             ┌───────────────────────────────┐
             │      GATE 1: Oracle Cloud     │  <-- Cloud Ingress Rules
             │        Security List          │
             └───────────────┬───────────────┘
                             │
                             │ Port 443
                             ▼
             ┌───────────────────────────────┐
             │      GATE 2: Ubuntu Linux     │  <-- Host Firewall (iptables)
             │            iptables           │
             └───────────────┬───────────────┘
                             │
                             │ Port 443
                             ▼
             ┌───────────────────────────────┐
             │         Nginx 1.24.0          │  <-- SSL Termination & Static Cache
             │    (Reverse Proxy / Router)   │
             └───────┬───────────────┬───────┘
                     │               │
      Static Files   │               │ /ws/ (WebSocket Upgrade) & / (HTTP)
      (/static/)     │               │ Proxy to 127.0.0.1:8001
                     ▼               ▼
             ┌──────────────┐ ┌──────────────┐
             │ staticfiles/ │ │ Daphne ASGI  │  <-- 24/7 Service (systemd)
             │ Direct Disk  │ │ Server :8001 │
             └──────────────┘ └──────┬───────┘
                                     │
                                     │ Channels Channel Layer
                                     ▼
                             ┌──────────────┐
                             │ Redis Server │  <-- In-Memory Message Broker
                             │  Port 6379   │
                             └──────────────┘
```

### Why This Stack?

1. **Why Daphne + Nginx (Instead of Daphne Alone)?**
   - Daphne is an ASGI application server designed specifically for async Python and WebSockets.
   - However, Daphne is not optimized for SSL termination, brute-force rate-limiting, or serving static files directly from disk.
   - Placing Nginx in front provides **SSL termination**, **DDoS protection**, and **instant static file delivery** (bypassing the Python interpreter entirely).

2. **Why Redis (Instead of InMemoryChannelLayer)?**
   - `InMemoryChannelLayer` stores message queues in Python process memory. If you run multiple server workers, or restart the server, all group rosters and queues vanish.
   - `RedisChannelLayer` runs as an external, lightning-fast in-memory database. Multiple Daphne worker processes can subscribe and broadcast across the same channel groups seamlessly.

3. **Why systemd?**
   - In production, server processes must survive unhandled exceptions, memory exhaustion, and cloud host reboots.
   - `systemd` acts as an active supervisor: if Daphne crashes, `systemd` revives it in 3 seconds.

4. **Why Ampere ARM64 on Oracle Cloud?**
   - Oracle's Always Free tier provides up to 4 OCPUs and 24 GB of RAM on Ampere A1 (ARM64) architecture.
   - We used **1 OCPU and 6 GB of RAM** for `YB-ChatApp`.
   - This leaves **3 OCPUs and 18 GB of RAM** available in your tenancy for the upcoming **Tuko Kadi** game server!

---

## 4. Key Concepts Learned & Relevance to Tuko Kadi

| Concept | What It Does in Chat App | How It Directly Powers Tuko Kadi |
| :--- | :--- | :--- |
| **`wss://` Secure WebSockets** | Encrypted real-time messaging without browser security blocks | Players' card moves, turn timers, and deck shuffles stream securely without MITM attacks |
| **Channel Layer (Redis)** | Relays messages between rooms across server workers | Synchronizes game room state across players, spectators, and game engine processes |
| **Nginx Reverse Proxy** | Proxies `/ws/` to port 8001 with 24h timeouts | Prevents mobile data disconnects during turn-based card gameplay |
| **systemd Supervision** | Daphne auto-restarts if process crashes | Game relay engine automatically recovers without manual developer intervention |
| **Client-Agnostic Backend** | Web, mobile, and Next.js connect to the same WSS URL | Mobile app (Flutter/React Native) and Next.js web lobby connect to the same Tuko Kadi card server |

---

## 5. Live Verification Checklist

- [x] Oracle ARM VM active with public IP: `130.61.9.37`
- [x] DuckDNS domain configured: `ybchatapp.duckdns.org`
- [x] Oracle Cloud Security List allowing ports `22`, `80`, `443`
- [x] Ubuntu `iptables` rules saved allowing `22`, `80`, `443`
- [x] Python 3.12, Redis, Nginx, Certbot, Git installed
- [x] `channels-redis==4.2.1` installed and active
- [x] 131 static assets compiled into `staticfiles/`
- [x] `chat-app.service` running via `systemd` on port 8001
- [x] Nginx reverse-proxying `/` and `/ws/` with upgrade headers
- [x] Let's Encrypt SSL active on `https://ybchatapp.duckdns.org`
- [x] Port 80 auto-redirects to HTTPS (301)
- [x] Static CSS served directly with `HTTP 200 OK`

---

## Live Production URL
👉 **[https://ybchatapp.duckdns.org](https://ybchatapp.duckdns.org)**
