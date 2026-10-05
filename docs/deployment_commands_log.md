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

## Upcoming Step (Awaiting User Go-Ahead)

### Step 7: Clone Code & Configure Python Environment
We will:
1. Clone `https://github.com/softdevbrian/Chat-App.git` into `~/chat_server` on the VM.
2. Create an isolated Python virtual environment (`~/chat_server/venv`).
3. Install production dependencies (`requirements.txt`, including `channels-redis` and `daphne`).
4. Run `python manage.py collectstatic` to package CSS and JavaScript into `staticfiles/`.

