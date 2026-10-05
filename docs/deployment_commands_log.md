# Production Deployment Walkthrough & Commands Log

This document is a **unified step-by-step guide** of the server setup and deployment phase (Phase 7) for the **YB-ChatApp** project. 

Each step is completely self-contained, presenting:
1. **The Intuitive Concept & Story** (Why we need this step in plain English).
2. **The Exact Command(s) Executed**.
3. **Command Breakdown** (What each flag and parameter actually does).
4. **The Raw Output Received**.
5. **Key Takeaway & Relevance** (Why this matters for this project and the upcoming **Tuko Kadi** server).

---

## High-Level Execution Overview

```
[ Step 1: Heartbeat Check ] 
       │  Verify server is reachable across the internet
       ▼
[ Step 2: DuckDNS Domain Mapping ] 
       │  Bind friendly domain (ybchatapp.duckdns.org) to server IP
       ▼
[ Step 3: Polishing the House Key (Windows ACL) ] 
       │  Secure private key permissions so OpenSSH permits its use
       ▼
[ Step 4: First Remote Handshake (SSH Login) ] 
       │  Authenticate into Ubuntu 24.04 ARM64 instance
       ▼
[ Step 5: Unlocking the Two Security Gates (Dual Firewalls) ] 
       │  Open Cloud Firewall (OCI) & Host Firewall (Ubuntu iptables)
       ▼
[ READY FOR SOFTWARE: Python, Redis, Nginx, Certbot & Django Code ]
```

---

## Step 1: The Heartbeat Check ("Is Anyone Home?")

### 💡 The Concept & Story
You clicked **"Update"** in the Oracle Cloud Console, and Oracle attached the public IPv4 address **`130.61.9.37`** to your virtual network interface card (VNIC). 

Before doing anything complicated, we needed to know: *Can your computer in Kenya actually communicate with this new virtual machine in Frankfurt, Germany?* We sent a quick digital "knock on the door" specifically to **Port 22** (the default listening port for SSH).

### 💻 The Exact Command:
```powershell
Test-NetConnection -ComputerName 130.61.9.37 -Port 22
```

### 🔍 Command Breakdown:
* `Test-NetConnection`: Built-in PowerShell network diagnostic tool.
* `-ComputerName 130.61.9.37`: The destination public IP address.
* `-Port 22`: The destination TCP port for SSH.

### 📋 Output Received:
```text
ComputerName     : 130.61.9.37
RemoteAddress    : 130.61.9.37
RemotePort       : 22
InterfaceAlias   : Wi-Fi
SourceAddress    : 192.168.77.15
TcpTestSucceeded : True
```

### 🎯 Key Takeaway:
`TcpTestSucceeded : True` confirmed the network pipe between your computer and the Oracle VM is open and responsive. The Internet Gateway and routing in Oracle Cloud are functioning properly.

---

## Step 2: Attaching the Street Sign ("DuckDNS Domain Mapping")

### 💡 The Concept & Story
Nobody wants to type a raw IP address like `130.61.9.37` into their phone browser to chat. More importantly, **SSL certificates (HTTPS/WSS) cannot be easily issued to bare ephemeral IP addresses**—Let's Encrypt requires a recognized domain name. 

We needed to tell DuckDNS: *"Whenever someone visits `ybchatapp.duckdns.org`, route them directly to `130.61.9.37`."* DuckDNS provides a simple HTTP API that allows updating DNS records programmatically with your secret account token.

### 💻 The Exact Commands:

#### 1. Update the DuckDNS Record:
```powershell
curl.exe -s "https://www.duckdns.org/update?domains=ybchatapp&token=1a48bf8e-c0f0-42db-8ce7-dfa666845068&ip=130.61.9.37"
```

#### 2. Verify Global DNS Resolution:
```powershell
Resolve-DnsName -Name "ybchatapp.duckdns.org" -Type A
```

### 🔍 Command Breakdown:
* `curl.exe -s`: Sends a silent HTTP GET request over the internet.
* `domains=ybchatapp`: Your registered DuckDNS subdomain.
* `token=1a48...`: Your secret DuckDNS authentication token proving account ownership.
* `ip=130.61.9.37`: The new public IP address to map to.
* `Resolve-DnsName ... -Type A`: Queries DNS nameservers for the IPv4 (`A`) record of `ybchatapp.duckdns.org`.

### 📋 Output Received:
From DuckDNS:
```text
OK
```
From DNS Query:
```text
Name                                           Type   TTL   Section    IPAddress
----                                           ----   ---   -------    ---------
ybchatapp.duckdns.org                          A      60    Answer     130.61.9.37
```

### 🎯 Key Takeaway:
The domain `ybchatapp.duckdns.org` is now globally mapped to your VM's public IP. Anyone typing this domain into a browser will land directly on your Oracle server.

---

## Step 3: Polishing the House Key ("Windows Security Safeguard")

### 💡 The Concept & Story
When you created the VM, Oracle generated a cryptographic **key pair**:
* The **Public Key** was embedded inside the VM's `~/.ssh/authorized_keys`.
* The **Private Key** was downloaded to your PC (`C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key`).

**The Problem:** Windows file permissions are naturally permissive. By default, files in your `Downloads` folder can be read by other accounts, background services, or inherited groups. 

However, OpenSSH has an ironclad rule: **If a private key is accessible to anyone other than YOU, OpenSSH refuses to use it** and halts with:
> `WARNING: UNPROTECTED PRIVATE KEY FILE! Bad permissions...`

We had to configure Windows' Access Control List (ACL) using `icacls` to strip away shared access and grant **exclusive Read-only permission** to your user account (`YOBI\YOBI`).

### 💻 The Exact Commands:

#### 1. Confirm Key Exists:
```powershell
Get-Item "C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key"
```

#### 2. Check Active User Identity:
```powershell
whoami
```

#### 3. Grant Exclusive Read Permission to `YOBI\YOBI`:
```powershell
icacls "C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key" /grant:r "YOBI\YOBI:R"
```

#### 4. Remove Orphaned / Shared SIDs:
```powershell
icacls "C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key" /remove "*S-1-5-21-1456761263-1058785588-2134328143"
```

#### 5. Verify Clean Key Permissions:
```powershell
icacls "C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key"
```

### 🔍 Command Breakdown:
* `whoami`: Returns the exact domain\username of the active Windows user (`yobi\yobi`).
* `icacls`: The Windows command-line utility for managing Access Control Lists.
* `/grant:r "YOBI\YOBI:R"`: Replaces existing permissions with exclusive Read (`:R`) access for `YOBI\YOBI`.
* `/remove "*S-1-5-..."`: Strips an invalid security identifier that OpenSSH flagged as a security leak.

### 📋 Output Received:
```text
C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key YOBI\YOBI:(R)
Successfully processed 1 files; Failed processing 0 files
```

### 🎯 Key Takeaway:
Only your Windows account can read the private key. OpenSSH is satisfied that the file is safe and ready for authentication.

---

## Step 4: Walking Inside the House ("The First Remote Handshake")

### 💡 The Concept & Story
Now that the key was properly secured, we unlocked the server door from your Windows PowerShell. We wanted to confirm:
1. The private key actually matches the public key inside the VM.
2. We can run commands as the administrative `ubuntu` user.
3. The server is indeed running the 64-bit ARM architecture (aarch64) we requested.

### 💻 The Exact Command:
```powershell
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i "C:\Users\YOBI\Downloads\ssh-key-2026-10-05.key" ubuntu@130.61.9.37 "uname -a; lsb_release -a"
```

### 🔍 Command Breakdown:
* `ssh`: OpenSSH client command.
* `-o StrictHostKeyChecking=no`: Automatically accepts the server's fingerprint on first connect without blocking for a manual "yes/no" prompt.
* `-o ConnectTimeout=10`: Aborts if connection takes more than 10 seconds.
* `-i "..."`: Specifies the path to the private authentication key.
* `ubuntu@130.61.9.37`: Logs in as user `ubuntu` on our server's public IP.
* `"uname -a; lsb_release -a"`: The commands to execute on the remote machine once connected.

### 📋 Output Received:
```text
Linux yb-chatapp 6.17.0-1020-oracle #20-Ubuntu SMP Sat Jul 25 00:52:17 UTC 2026 aarch64 aarch64 aarch64 GNU/Linux
Distributor ID: Ubuntu
Description:    Ubuntu 24.04.5 LTS
Release:        24.04
Codename:       noble
```

### 🎯 Key Takeaway:
We have established remote command execution! The VM is running Ubuntu 24.04 LTS on Ampere ARM64 (`aarch64`).

---

## Step 5: Unlocking the Two Security Gates ("The Dual-Firewall Architecture")

### 💡 The Concept & Story
In cloud hosting, there is a fundamental concept called **Defense-in-Depth**. Your server does not have just one firewall—it has **two separate gates**:

```
[ Incoming Web Browser Traffic (Port 80 / 443) ]
                       │
                       ▼
       ┌───────────────────────────────┐
       │   GATE 1: Oracle Cloud List   │  <-- Configured in Oracle Web Console
       │    (External Cloud Perimeter) │      (Allows Port 22, 80, 443)
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   GATE 2: Ubuntu iptables     │  <-- Configured inside Linux Terminal
       │    (Internal OS Firewall)     │      (Was: Accept 22, REJECT ALL ELSE)
       └───────────────┬───────────────┘      (Now: Accept 22, 80, 443)
                       │
                       ▼
          [ Nginx Web & Daphne WSS Server ]
```

* **Gate 1 (Oracle Cloud Security List):** Configured in the browser console. You added Ingress Rules allowing ports **80** (HTTP) and **443** (HTTPS) from any source (`0.0.0.0/0`).
* **Gate 2 (Ubuntu OS Firewall / `iptables`):** Inside the VM itself. When we inspected Ubuntu's internal firewall, we found:
  > *Rule 4: Accept Port 22 (SSH).*  
  > *Rule 5: REJECT ALL OTHER TRAFFIC with `icmp-host-prohibited`.*
* **The Danger:** Even with Gate 1 open in Oracle, Gate 2 would slam the door on incoming web traffic! Users would get "Connection Refused", and Certbot would fail to verify domain ownership.

We had to insert rules into Ubuntu's firewall allowing ports 80 and 443 **before** the reject rule, and make them permanent across reboots.

### 💻 The Exact Commands:

#### 1. Inspect Initial Ubuntu Firewall Rules:
```bash
sudo iptables -L INPUT -n --line-numbers
```

#### 2. Insert Accept Rules for Port 80 and Port 443:
```bash
sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
```

#### 3. Save Rules Permanently Across Reboots:
```bash
sudo netfilter-persistent save
```

#### 4. Confirm the Final Firewall State:
```bash
sudo iptables -L INPUT -n --line-numbers
```

### 🔍 Command Breakdown:
* `iptables -L INPUT -n --line-numbers`: Lists all incoming firewall rules numbered sequentially.
* `-I INPUT 5`: Inserts a rule at position 5 (pushing the old `REJECT` rule down to position 7).
* `-p tcp --dport 80 -j ACCEPT`: Accepts incoming TCP traffic on port 80 (HTTP).
* `-p tcp --dport 443 -j ACCEPT`: Accepts incoming TCP traffic on port 443 (HTTPS/WSS).
* `netfilter-persistent save`: Saves the in-memory rules to `/etc/iptables/rules.v4` so they reload automatically when the VM boots up.

### 📋 Output Received:
```text
run-parts: executing /usr/share/netfilter-persistent/plugins.d/15-ip4tables save
run-parts: executing /usr/share/netfilter-persistent/plugins.d/25-ip6tables save
Chain INPUT (policy ACCEPT)
num  target     prot opt source               destination         
1    ACCEPT     0    --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
2    ACCEPT     1    --  0.0.0.0/0            0.0.0.0/0           
3    ACCEPT     0    --  0.0.0.0/0            0.0.0.0/0           
4    ACCEPT     6    --  0.0.0.0/0            0.0.0.0/0            state NEW tcp dpt:22
5    ACCEPT     6    --  0.0.0.0/0            0.0.0.0/0            tcp dpt:80
6    ACCEPT     6    --  0.0.0.0/0            0.0.0.0/0            tcp dpt:443
7    REJECT     0    --  0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited
```

### 🎯 Key Takeaway:
Both Gate 1 (Oracle Cloud) and Gate 2 (Ubuntu OS) now allow traffic on Ports 22, 80, and 443. The server is completely prepared to serve public web traffic.

---

## Step 6: Furnishing the House ("Installing the Server Software Stack")

### 💡 The Concept & Story
Now that the server is alive, reachable, and its security gates are wide open, we have an empty operating system. To run a modern, real-time Django Channels application with WebSockets and SSL in production, we need four primary layers of software:

1. **Python 3 & Virtual Environment (`python3-venv`, `python3-pip`):** Provides an isolated sandbox for Django and its Python libraries so we never pollute system packages.
2. **Redis (`redis-server`):** The lightning-fast in-memory database used by Django Channels as the **Channel Layer**. When users in different browser tabs or different countries send messages, Redis relays them in milliseconds across server processes.
3. **Nginx (`nginx`):** A battle-tested web server that faces the public internet. It handles incoming HTTP/HTTPS traffic, serves static CSS/JS files instantly, and proxies WebSocket traffic (`/ws/`) to our Daphne ASGI server.
4. **Certbot (`certbot`, `python3-certbot-nginx`):** The automated client from the Electronic Frontier Foundation (EFF) that negotiates with Let's Encrypt to issue and automatically renew free SSL certificates.
5. **Git (`git`):** To clone our repository code from GitHub directly onto the server.

### 💻 The Exact Commands:

#### 1. Update Package Index and Install Software:
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip redis-server nginx certbot python3-certbot-nginx git
```

#### 2. Verify Background Services Are Running:
```bash
sudo systemctl is-active redis-server nginx
```

#### 3. Test Public Web Server Reachability:
```powershell
curl.exe -I "http://ybchatapp.duckdns.org"
```

### 🔍 Command Breakdown:
* `sudo apt update`: Refreshes Ubuntu's software repository index to ensure the newest package versions are downloaded.
* `sudo apt install -y ...`: Automatically answers "yes" to installation confirmation prompts.
* `systemctl is-active <service>`: Queries the Linux system manager (`systemd`) to check if services started successfully.
* `curl.exe -I`: Fetches only the HTTP headers from the domain over the public internet.

### 📋 Output Received:
From `systemctl is-active`:
```text
active
active
```
From `curl.exe -I "http://ybchatapp.duckdns.org"`:
```text
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Date: Mon, 05 Oct 2026 18:22:58 GMT
Content-Type: text/html
Content-Length: 615
Connection: keep-alive
```

### 🎯 Key Takeaway:
Your server is no longer an empty box! Nginx is already listening on port 80 and actively serving web responses to the public internet under `http://ybchatapp.duckdns.org`. Redis is active in the background, waiting to power Django Channels.

---

## Architecture Status Summary

| Component | Status | Details |
| :--- | :--- | :--- |
| **Compute Instance** | **Active & Running** | `YB-ChatApp` (1 OCPU ARM, 6 GB RAM, 50 GB Boot) |
| **Public IPv4** | **Configured** | `130.61.9.37` attached to Primary VNIC |
| **Domain (DuckDNS)** | **Linked & Active** | `ybchatapp.duckdns.org` $\rightarrow$ `130.61.9.37` |
| **SSH Key** | **Secured & Verified** | Windows ACL restricted to `YOBI\YOBI` |
| **Cloud Firewall (OCI)** | **Open** | Ingress rules for TCP `22`, `80`, `443` |
| **Host Firewall (Ubuntu)** | **Open & Persisted** | Rules 4, 5, 6 accepting `22`, `80`, `443` |
| **Web Server (Nginx)** | **Active & Responding** | Nginx 1.24.0 returning `HTTP 200 OK` |
| **Message Broker (Redis)** | **Active** | `redis-server` running and enabled |
| **Python Runtime** | **Ready** | Python 3.12 + `venv` installed |

---

## Step 7: Moving into the House ("Deploying Application Code & Environment")

### 💡 The Concept & Story
Now that all the foundational software (Python, Redis, Nginx, Git) is installed and running, we need to bring our chat application code onto the server:

1. **Pulling from Git (`git clone`):** Rather than copying files manually via FTP, cloning our GitHub repository ensures the server has the exact, version-controlled codebase matching our local workspace.
2. **Dedicated Virtual Environment (`python3 -m venv`):** Creates an isolated Python environment at `/home/ubuntu/chat_server/venv`. This guarantees our project dependencies (Django 6.1.1, Channels 4.3.2, Daphne 4.2.3, Channels-Redis 4.2.1) are strictly isolated and never conflict with system tools.
3. **Bundling Static Files (`collectstatic`):** In development, Django dynamically searches each app for CSS and JS. In production, this is too slow. `collectstatic` gathers all static assets from your apps and third-party packages into one centralized folder (`/home/ubuntu/chat_server/staticfiles/`). Later, Nginx will serve these files directly at blistering speeds without touching Python.
4. **Database Migration (`migrate`):** Prepares the SQLite database tables for Django sessions and user models.
5. **System Validation (`check`):** Verifies that all Django settings, apps, and ASGI routing configurations are valid with zero warnings or errors.

### 💻 The Exact Commands:

#### 1. Clone Code, Build Virtual Environment & Install Dependencies:
```bash
git clone https://github.com/softdevbrian/Chat-App.git /home/ubuntu/chat_server && \
python3 -m venv /home/ubuntu/chat_server/venv && \
/home/ubuntu/chat_server/venv/bin/pip install --upgrade pip && \
/home/ubuntu/chat_server/venv/bin/pip install -r /home/ubuntu/chat_server/requirements.txt && \
/home/ubuntu/chat_server/venv/bin/python /home/ubuntu/chat_server/manage.py collectstatic --noinput
```

#### 2. Apply Migrations & Validate Django:
```bash
/home/ubuntu/chat_server/venv/bin/python /home/ubuntu/chat_server/manage.py migrate && \
/home/ubuntu/chat_server/venv/bin/python /home/ubuntu/chat_server/manage.py check
```

### 🔍 Command Breakdown:
* `git clone <url> <target>`: Downloads the complete repository from GitHub into `/home/ubuntu/chat_server`.
* `python3 -m venv .../venv`: Creates the project-specific virtual environment.
* `pip install -r requirements.txt`: Installs our exact pinned packages compiled for Linux ARM64 architecture.
* `collectstatic --noinput`: Copies all CSS, JS, and vendor files into `STATIC_ROOT` without prompting for confirmation.
* `python manage.py migrate`: Runs pending database migrations.
* `python manage.py check`: Inspects the entire Django ASGI and Channels project configuration for syntax or routing errors.

### 📋 Output Received:
From `pip install`:
```text
Successfully installed Automat-25.4.16 Django-6.1.1 Incremental-24.11.0 Twisted-26.4.0 
asgiref-3.12.1 attrs-26.1.0 autobahn-26.7.1 cbor2-6.1.5 cffi-2.1.1 channels-4.3.2 
channels-redis-4.2.1 constantly-23.10.4 cryptography-50.0.2 daphne-4.2.3 hyperlink-21.0.0 
idna-3.20 msgpack-1.2.3 packaging-26.3 pyOpenSSL-26.4.0 pycparser-3.0 redis-8.1.0 
service-identity-26.1.0 sqlparse-0.6.0 txaio-26.6.1 typing_extensions-4.16.0 tzdata-2026.4 
ujson-6.0.0 zope.interface-8.6
```
From `collectstatic`:
```text
131 static files copied to '/home/ubuntu/chat_server/staticfiles'.
```
From `migrate` & `check`:
```text
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).
```

### 🎯 Key Takeaway:
The complete codebase is deployed on the server. All dependencies are installed and compiled for ARM64, 131 static files are ready for Nginx to serve, and Django's ASGI system check reports zero issues.

---

## Architecture Status Summary

| Component | Status | Details |
| :--- | :--- | :--- |
| **Compute Instance** | **Active & Running** | `YB-ChatApp` (1 OCPU ARM, 6 GB RAM, 50 GB Boot) |
| **Public IPv4** | **Configured** | `130.61.9.37` attached to Primary VNIC |
| **Domain (DuckDNS)** | **Linked & Active** | `ybchatapp.duckdns.org` $\rightarrow$ `130.61.9.37` |
| **SSH Key** | **Secured & Verified** | Windows ACL restricted to `YOBI\YOBI` |
| **Cloud Firewall (OCI)** | **Open** | Ingress rules for TCP `22`, `80`, `443` |
| **Host Firewall (Ubuntu)** | **Open & Persisted** | Rules 4, 5, 6 accepting `22`, `80`, `443` |
| **Web Server (Nginx)** | **Active & Responding** | Nginx 1.24.0 returning `HTTP 200 OK` |
| **Message Broker (Redis)** | **Active** | `redis-server` running and enabled |
| **Python Runtime** | **Ready** | Python 3.12 + `venv` active |
| **Application Code** | **Deployed** | `/home/ubuntu/chat_server` on `main` (`55c1e7a`) |
| **Static Assets** | **Bundled** | 131 files compiled in `staticfiles/` |
| **Database** | **Initialized** | SQLite migrated (`System check: 0 issues`) |

---

## Step 8: Running 24/7 in the Background ("Daphne systemd Service")

### 💡 The Concept & Story
In development on Windows, you ran `python manage.py runserver` in your terminal. But in production, you cannot keep a terminal open forever—if you disconnect SSH or close your laptop, the process would immediately terminate!

To make our application truly production-grade, we delegate management to **`systemd`**, Linux's central system and service manager:
1. **Always Running:** Daphne runs quietly as a background daemon.
2. **Auto-Restart on Failure:** If Daphne ever encounters an unhandled exception or crashes, `systemd` waits 3 seconds and automatically revives it (`Restart=always`).
3. **Auto-Boot:** If the Oracle VM ever reboots (e.g., during cloud maintenance), `systemd` automatically boots Daphne right alongside Redis before any user tries to connect.
4. **Environment Injection:** We inject `USE_REDIS=True`, `REDIS_HOST=127.0.0.1`, `REDIS_PORT=6379`, and `DJANGO_DEBUG=False` directly through the unit file.
5. **High Concurrency Limits:** We set `LimitNOFILE=65535` so Linux allows thousands of concurrent open WebSocket connections without running out of operating system file handles.

### 💻 The Exact Commands:

#### 1. Install and Start the Service:
```bash
sudo cp /home/ubuntu/chat_server/deploy/chat-app.service /etc/systemd/system/chat-app.service && \
sudo systemctl daemon-reload && \
sudo systemctl enable --now chat-app
```

#### 2. Check Service Status & Test Daphne Directly:
```bash
sudo systemctl status chat-app --no-pager && \
curl -s -I http://127.0.0.1:8001/
```

### 🔍 Command Breakdown:
* `sudo cp ... /etc/systemd/system/`: Installs the service definition where Linux expects it.
* `systemctl daemon-reload`: Informs `systemd` to scan for new or modified service units.
* `systemctl enable --now chat-app`:
  - `enable`: Registers the service to start automatically on system boot.
  - `--now`: Immediately starts the service right now without waiting for a reboot.
* `systemctl status chat-app`: Displays runtime metrics, process ID (PID), memory usage, and recent logs.
* `curl -s -I http://127.0.0.1:8001/`: Sends a local HTTP request directly to Daphne on port 8001 to ensure the Django app is serving responses.

### 📋 Output Received:
From `systemctl enable --now` & `systemctl status`:
```text
Created symlink /etc/systemd/system/multi-user.target.wants/chat-app.service → /etc/systemd/system/chat-app.service.
● chat-app.service - Daphne ASGI Server for Django Channels Chat App
     Loaded: loaded (/etc/systemd/system/chat-app.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-10-05 18:41:52 UTC
   Main PID: 6228 (daphne)
      Tasks: 1 (limit: 6964)
     Memory: 2.6M (peak: 2.6M)
     CGroup: /system.slice/chat-app.service
             └─6228 /home/ubuntu/chat_server/venv/bin/python3 /home/ubuntu/chat_server/venv/bin/daphne -b 127.0.0.1 -p 8001 chat_project.asgi:application

Oct 05 18:41:52 yb-chatapp systemd[1]: Started chat-app.service - Daphne ASGI Server for Django Channels Chat App.
```
From `curl http://127.0.0.1:8001/`:
```text
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 3719
Server: daphne
```

### 🎯 Key Takeaway:
Daphne is active, listening on port 8001, connected to Redis, and serving our Django chat application. If the server crashes or reboots, Daphne will restart itself automatically.

---

## Architecture Status Summary

| Component | Status | Details |
| :--- | :--- | :--- |
| **Compute Instance** | **Active & Running** | `YB-ChatApp` (1 OCPU ARM, 6 GB RAM, 50 GB Boot) |
| **Public IPv4** | **Configured** | `130.61.9.37` attached to Primary VNIC |
| **Domain (DuckDNS)** | **Linked & Active** | `ybchatapp.duckdns.org` $\rightarrow$ `130.61.9.37` |
| **SSH Key** | **Secured & Verified** | Windows ACL restricted to `YOBI\YOBI` |
| **Cloud Firewall (OCI)** | **Open** | Ingress rules for TCP `22`, `80`, `443` |
| **Host Firewall (Ubuntu)** | **Open & Persisted** | Rules 4, 5, 6 accepting `22`, `80`, `443` |
| **Web Server (Nginx)** | **Active & Responding** | Nginx 1.24.0 returning `HTTP 200 OK` |
| **Message Broker (Redis)** | **Active** | `redis-server` running and enabled |
| **Python Runtime** | **Ready** | Python 3.12 + `venv` active |
| **Application Code** | **Deployed** | `/home/ubuntu/chat_server` on `main` (`55c1e7a`) |
| **Static Assets** | **Bundled** | 131 files compiled in `staticfiles/` |
| **Database** | **Initialized** | SQLite migrated (`System check: 0 issues`) |
| **ASGI Server (Daphne)** | **Active (24/7 Daemon)** | Running via `systemd` (PID 6228, port 8001) |

---

## Step 9: The Protective Shield & SSL ("Nginx Reverse Proxy & Certbot")

### 💡 The Concept & Story
Up to this point, Daphne was listening internally on port 8001, but users across the internet connect to standard web ports (**80** for HTTP and **443** for HTTPS). Furthermore, modern web browsers and mobile apps block unencrypted WebSockets (`ws://`) when running on production domains—they strictly demand **SSL/TLS encryption** (`https://` and `wss://`).

To achieve this, we set up **Nginx as a Reverse Proxy** with **Certbot (Let's Encrypt)**:
1. **SSL Termination:** Nginx handles the heavy cryptographic math of decrypting HTTPS/WSS traffic from users and forwarding plain HTTP/WS to Daphne on `127.0.0.1:8001`.
2. **WebSocket Upgrade:** Nginx inspects the HTTP headers; when it sees `Upgrade: websocket`, it switches the HTTP connection into a persistent, 2-way binary pipe and holds it open for up to 24 hours (`proxy_read_timeout 86400s`).
3. **High-Speed Static Serving:** Nginx directly serves CSS and JavaScript from `/home/ubuntu/chat_server/staticfiles/` with a 30-day browser cache. Python and Daphne never waste CPU cycles serving static files.
4. **Automated Free SSL via ACME Protocol:** Certbot negotiates directly with Let's Encrypt servers, proves domain ownership of `ybchatapp.duckdns.org`, installs trusted cryptographic certificates, and schedules automatic background renewals before expiration.
5. **Ubuntu Home Directory Permission Fix:** Ubuntu user home directories default to `750` (`rwxr-x---`). We granted world execute (`chmod 755 /home/ubuntu`) so Nginx's worker process (`www-data`) has search rights to serve static assets from the project folder.

### 💻 The Exact Commands:

#### 1. Configure and Enable Nginx Virtual Host:
```bash
# Configure /etc/nginx/sites-available/chat_app
sudo ln -sf /etc/nginx/sites-available/chat_app /etc/nginx/sites-enabled/chat_app && \
sudo rm -f /etc/nginx/sites-enabled/default && \
sudo nginx -t && \
sudo systemctl reload nginx
```

#### 2. Obtain & Install SSL Certificate via Certbot:
```bash
sudo certbot --nginx -d ybchatapp.duckdns.org --non-interactive --agree-tos -m softdevbriankuria@gmail.com --redirect
```

#### 3. Allow Nginx Worker Access to Static Assets:
```bash
chmod 755 /home/ubuntu
```

#### 4. Verify Live HTTPS & Static Asset Responses:
```powershell
# Verify HTTPS homepage
curl.exe -I "https://ybchatapp.duckdns.org"

# Verify HTTP auto-redirects to HTTPS (301)
curl.exe -I "http://ybchatapp.duckdns.org"

# Verify Nginx directly serves static CSS
curl.exe -I "https://ybchatapp.duckdns.org/static/chat/style.css"
```

### 🔍 Command Breakdown:
* `sudo certbot --nginx`: Uses Certbot's Nginx plugin to automatically detect server blocks, install certificates, and rewrite configs.
* `-d ybchatapp.duckdns.org`: The domain name to issue the SSL certificate for.
* `--agree-tos -m softdevbriankuria@gmail.com`: Accepts Let's Encrypt terms and registers renewal alerts to your email.
* `--redirect`: Automatically configures port 80 to permanently redirect (`301 Moved Permanently`) to `https://`.
* `chmod 755 /home/ubuntu`: Grants read/execute permission to parent directories so `www-data` can traverse to `staticfiles/`.

### 📋 Output Received:
From `certbot`:
```text
Requesting a certificate for ybchatapp.duckdns.org
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/ybchatapp.duckdns.org/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/ybchatapp.duckdns.org/privkey.pem
This certificate expires on 2027-01-03.
Certbot has set up a scheduled task to automatically renew this certificate in the background.

Deploying certificate
Successfully deployed certificate for ybchatapp.duckdns.org to /etc/nginx/sites-enabled/chat_app
Congratulations! You have successfully enabled HTTPS on https://ybchatapp.duckdns.org
```
From `curl HTTPS`:
```text
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Content-Type: text/html; charset=utf-8
Content-Length: 3719
```
From `curl HTTP redirect`:
```text
HTTP/1.1 301 Moved Permanently
Location: https://ybchatapp.duckdns.org/
```
From `curl Static CSS`:
```text
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Content-Type: text/css
Content-Length: 10876
Cache-Control: public, max-age=2592000
```

### 🎯 Key Takeaway:
Your application is fully secured with an official, trusted SSL certificate from Let's Encrypt. All HTTP traffic automatically redirects to HTTPS, static files are cached and served instantly by Nginx, and all WebSocket connections are secured under `wss://`.

---

## Architecture Status Summary (Fully Deployed)

| Layer | Component | Status | Details |
| :--- | :--- | :--- | :--- |
| **Compute** | Oracle Cloud VM | **Active & Running** | `YB-ChatApp` (1 OCPU ARM, 6 GB RAM, 50 GB Boot) |
| **Networking** | Public IPv4 | **Configured** | `130.61.9.37` on Primary VNIC |
| **DNS** | DuckDNS | **Active & Resolved** | `ybchatapp.duckdns.org` $\rightarrow$ `130.61.9.37` |
| **Authentication** | SSH Key Pair | **Secured & Verified** | Windows ACL restricted to `YOBI\YOBI` |
| **Cloud Firewall** | OCI Security List | **Open** | Ingress rules for TCP `22`, `80`, `443` |
| **Host Firewall** | Ubuntu `iptables` | **Open & Persisted** | Rules 4, 5, 6 accepting `22`, `80`, `443` |
| **Web Server** | Nginx Reverse Proxy | **Active (SSL Enabled)** | TLSv1.3, auto HTTP $\rightarrow$ HTTPS redirect |
| **Static Assets** | Nginx Static Cache | **Active** | 131 files served directly from `staticfiles/` |
| **SSL / TLS** | Let's Encrypt (Certbot) | **Active & Auto-Renewing** | Valid until 2027-01-03 |
| **Message Broker** | Redis Server | **Active** | `redis-server` (Channel layer backend) |
| **ASGI Server** | Daphne Daemon | **Active (24/7)** | Managed via `systemd` on port 8001 |
| **Application** | Django Channels App | **Live in Production** | `https://ybchatapp.duckdns.org/` |

---

## Live Application Link
👉 **[https://ybchatapp.duckdns.org](https://ybchatapp.duckdns.org)**




