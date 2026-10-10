# ⚡ Tuko Chat — Real-Time WebSocket Messaging Platform & PWA

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Channels](https://img.shields.io/badge/Django_Channels-4.0%2B-2575fc?style=flat)](https://channels.readthedocs.io/)
[![Daphne](https://img.shields.io/badge/Daphne-ASGI-blueviolet?style=flat)](https://github.com/django/daphne)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=flat&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![Oracle Cloud](https://img.shields.io/badge/Oracle_Cloud-Ubuntu_ARM64-F80000?style=flat&logo=oracle&logoColor=white)](https://www.oracle.com/cloud/)
[![SSL / TLS](https://img.shields.io/badge/SSL-Let's_Encrypt-003A70?style=flat&logo=letsencrypt&logoColor=white)](https://letsencrypt.org/)

> **Live Production URL:** [https://ybchatapp.duckdns.org](https://ybchatapp.duckdns.org)  
> **Mobile & Desktop Installable:** Fully compliant Progressive Web App (PWA) with offline caching and standalone execution.

---

## 📖 Overview

**Tuko Chat** is a production-deployed real-time messaging application engineered with **Django Channels**, **Daphne (ASGI)**, and **WebSockets**. Designed to mimic high-performance chat clients like Slack and WhatsApp Web, it combines sub-50ms bidirectional messaging with lightweight data persistence, user discovery, creator governance, cryptographic password recovery, and installable PWA capabilities.

The platform is deployed live on an **Oracle Cloud Infrastructure (OCI) Ampere ARM64 Virtual Machine** running Canonical Ubuntu 24.04 LTS, fronted by **Nginx 1.24** with automated **Let's Encrypt SSL/TLS** certificates and a **Redis 7.0** channel layer.

---

## 🚀 Key Features

### 1. ⚡ High-Throughput WebSockets (ASGI + Daphne + Redis)
- **Bidirectional Pipes:** Continuous, full-duplex communication over secure WebSockets (`wss://`) replacing legacy HTTP polling.
- **Dual Layer Architecture:**
  - *Local Development:* Auto-fallback to `InMemoryChannelLayer` for seamless zero-dependency development on Windows.
  - *Production Cloud:* High-concurrency `RedisChannelLayer` managing multi-worker pub/sub channels.

### 2. 💬 Dual-Mode Conversations (Channels & Direct Messages)
- **Public & Custom Chat Groups:** Users can dynamically create new topic groups (e.g. `#gamers`, `#projects`, `#general`).
- **Creator Governance:** The user who creates a chat group is awarded a `👑 Owner` badge and exclusive administrative rights to permanently delete the group and wipe its message stream.
- **1-on-1 Direct Messages (DMs):** Search any registered user by username or email via a debounce-throttled REST API endpoint to immediately launch an isolated two-way DM.
- **Dynamic Participant Roster:** Built-in **Members Drawer / Bottom Sheet** showing all conversation participants with avatar badges, ownership status, and active presence dots.

### 3. 🧹 Lean FIFO Database Pruning (100-Message Buffer)
- **SQLite Optimization:** Every group and DM maintains a hard limit of the **most recent 100 messages**.
- **Automated FIFO Eviction:** Older messages beyond the 100-message boundary are automatically pruned on each new interaction, ensuring the database stays fast, lightweight, and leak-free.

### 4. 🔐 Dual-Identity Authentication & Cryptographic Security
- **Flexible Login Backend:** Custom `EmailOrUsernameModelBackend` allowing users to authenticate seamlessly using either their username **or** registered email address.
- **Preset Avatar Engine:** 8 customizable SVG/Emoji gradient avatar identities (`🦁 Lion`, `🦅 Eagle`, `⚡ Bolt`, `🔥 Fire`, `👑 Crown`, `🚀 Rocket`, `🎯 Target`, `💎 Diamond`).
- **Brevo SMTP Password Recovery:** Secure password reset links sent via **Brevo SMTP Relay** (`smtp-relay.brevo.com:587` with TLS), signed with Django's `default_token_generator` and base64 user UID encoding.

### 5. 📱 Progressive Web App (PWA)
- **Native Experience:** Includes a Web App Manifest (`manifest.json`) and Service Worker (`sw.js`).
- **Installable Everywhere:** Prompts install on Android, iOS (Add to Home Screen), macOS, and Windows with standalone window frames and branded splash icons (192px & 512px).
- **Offline Shell Caching:** Serves core UI assets instantly from CacheStorage even under intermittent connectivity.

### 6. 🎨 Responsive Slate UI
- **Executive 2-Pane Desktop Auth:** Features a brand showcase with live mock conversational animation on the left and form controls on the right.
- **Mobile-First Chat Interface:** Slide-over sidebar, sticky bottom chat bar, touch-friendly pill buttons (`👥 Members`, `🗑️ Delete`), and auto-scrolling message streams.

---

## 🏛️ System Architecture

```
                                [ CLIENT PLATFORMS ]
                    (Android / iOS PWA, Chrome, Edge, Safari)
                                        │
                                        │ HTTPS / WSS (Port 443)
                                        ▼
                     ┌──────────────────────────────────────┐
                     │         ORACLE CLOUD VIRTUAL         │
                     │          FIREWALL & IPTABLES         │
                     └──────────────────┬───────────────────┘
                                        │
                                        │ Port 443
                                        ▼
                     ┌──────────────────────────────────────┐
                     │             Nginx 1.24               │
                     │      (SSL Termination & Router)      │
                     └──────────┬───────────────────┬───────┘
                                │                   │
                 Static Assets  │                   │ Reverse Proxy
                 & PWA Shell    │                   │ /ws/ & /api/
                 (/static/)     │                   ▼
                                │       ┌───────────────────────┐
                                │       │      Daphne ASGI      │
                                │       │     Server :8001      │
                                │       └───────────┬───────────┘
                                ▼                   │
                     ┌────────────────────┐         │ Django Channels
                     │    staticfiles/    │         ▼
                     │ (Direct File Disk) │ ┌───────────────────┐
                     └────────────────────┘ │   Redis 7.0 DB    │
                                            │  (Channel Layer)  │
                                            └─────────┬─────────┘
                                                      │
                                                      │ ORM Queries & Pruner
                                                      ▼
                                            ┌───────────────────┐
                                            │   SQLite DB       │
                                            │ (100-Msg Buffer)  │
                                            └───────────────────┘
                                                      │
                                                      │ Password Reset
                                                      ▼
                                            ┌───────────────────┐
                                            │  Brevo SMTP Relay │
                                            │ (Port 587 + TLS)  │
                                            └───────────────────┘
```

---

## 📂 Project Directory Structure

```
CHAT_APP/
├── chat/                               # Main Application Package
│   ├── migrations/                     # Database Schema Migrations
│   │   └── 0001_initial.py
│   ├── static/chat/                    # Client Assets & PWA Engine
│   │   ├── icon-192.png                # PWA Icon (192x192)
│   │   ├── icon-512.png                # PWA Splash Icon (512x512)
│   │   ├── manifest.json               # Web App Manifest
│   │   ├── style.css                   # App Global Styling
│   │   └── sw.js                       # Service Worker (Cache & Offline)
│   ├── templates/chat/                 # Jinja/Django Template Views
│   │   ├── emails/
│   │   │   └── password_reset_email.html # Brevo Transactional Email
│   │   ├── auth.html                   # Sign In & Registration (Split Hero)
│   │   ├── dashboard.html              # Vue 3 Chat Hub & Members Drawer
│   │   └── reset_password_confirm.html # Token Verification & New Password
│   ├── backends.py                     # Dual Username/Email Auth Backend
│   ├── consumers.py                    # Async Daphne WebSocket Consumer
│   ├── models.py                       # UserProfile, Conversation, Message
│   ├── routing.py                      # WebSocket URL Route Resolver
│   ├── urls.py                         # HTTP & JSON API Route Table
│   └── views.py                        # Views, FIFO Pruner & REST Endpoints
├── chat_project/                       # Project Configuration Root
│   ├── asgi.py                         # ASGI Entrypoint (ProtocolTypeRouter)
│   ├── settings.py                     # App Settings & Environment Config
│   ├── urls.py                         # Root URLconf
│   └── wsgi.py                         # WSGI Fallback
├── deploy/                             # Production Server Units
│   └── chat-app.service                # Systemd Unit File for Daphne
├── docs/                               # Engineering Documentation & Learning
│   ├── chat_app_learning/              # Phase 0 through Phase 8 Detailed Logs
│   │   ├── Phase 0 - Project Overview.md
│   │   ├── ...
│   │   ├── Phase 7 - Production Deployment.md
│   │   └── Phase 8 - Full-Stack Portfolio Overhaul, PWA, Brevo SMTP & Real-Time Engine.md
│   ├── deployment_commands_log.md      # Command-by-Command Server Setup Log
│   ├── errors_and_fixes_log.md         # Deep-Dive Debugging & Root Cause Playbook
│   ├── oracle_cost_management_and_vm_control.md
│   └── vm_remote_management_guide.md
├── .env.example                        # Environment Variables Blueprint
├── .gitignore                          # Git Ignored Files
├── db.sqlite3                          # Local SQLite Database
├── manage.py                           # Django CLI Management Script
├── requirements.txt                    # Python Dependencies List
└── README.md                           # Project Documentation
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.12, Django 5.1+, Django Channels 4.0+ |
| **ASGI Server** | Daphne 4.1+ |
| **Channel Layer Broker** | Redis 7.0 (Production) / InMemoryChannelLayer (Local) |
| **Database** | SQLite 3 (Indexed with 100-message FIFO auto-pruner) |
| **Frontend Reactive Layer** | Vue 3 (CDN Reactive Controller), Vanilla CSS3 / Flexbox / Grid |
| **PWA Stack** | Service Worker API, CacheStorage API, Web App Manifest |
| **Email Relay** | Brevo SMTP Relay (`smtp-relay.brevo.com`) via TLS |
| **Hosting & OS** | Oracle Cloud Infrastructure (Ampere A1 ARM64), Canonical Ubuntu 24.04 LTS |
| **Web Server & SSL** | Nginx 1.24.0, Certbot (Let's Encrypt automated SSL) |

---

## 💻 Local Setup & Development (Windows / macOS / Linux)

### 1. Clone the Repository
```bash
git clone https://github.com/softdevbrian/Chat-App.git
cd Chat-App
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a local `.env` file in the project root:
```ini
DEBUG=True
SECRET_KEY=your-local-insecure-secret-key
USE_REDIS=False

# Optional: To test sending real Brevo password reset emails locally:
BREVO_SMTP_LOGIN=bd87da001@smtp-brevo.com
BREVO_SMTP_KEY=your_brevo_smtp_master_key
DEFAULT_FROM_EMAIL=Tuko Chat <briankuriasupport@gmail.com>
```

*(Note: When `USE_REDIS=False`, Django Channels automatically uses `InMemoryChannelLayer`, so you do not need Redis installed to run WebSockets locally!)*

### 5. Run Migrations & Start Server
```bash
python manage.py migrate
python manage.py runserver
```

Open your browser at:
- **Sign In / Create Account:** [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Chat Hub:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 📧 Brevo SMTP Configuration & Multi-Project Reusability

Tuko Chat uses **Brevo (formerly Sendinblue)** to relay password reset emails. The configuration is completely decoupled and designed for effortless reuse across multiple client projects.

### How Brevo Works in this Architecture
1. The user requests a password reset link at `/forgot-password/`.
2. Django encodes the user's primary key (`uidb64`) and generates a cryptographic one-time token (`token`) via `default_token_generator`.
3. An HTML email containing the reset link is dispatched through Brevo's SMTP server (`smtp-relay.brevo.com:587`) using TLS encryption.
4. When clicked, `/reset-password/<uidb64>/<token>/` verifies that the token has not expired and matches the user's current password hash.

### Using the Same Brevo Account Across Future Projects
You **do not** need to create a new Brevo account for every project! Here is how to manage one account across multiple apps:

1. **Custom Senders per Project:**
   - In Brevo Dashboard, navigate to **Senders & Domains** -> **Senders** -> **Add a Sender**.
   - Add the specific email address (e.g. `support@yourdomain.com` or `yourname@gmail.com`) and verify the confirmation email.
2. **Project-Specific `DEFAULT_FROM_EMAIL`:**
   - In each project's `settings.py` or `.env`, customize the sender display name without changing your SMTP credentials:
     ```python
     DEFAULT_FROM_EMAIL = 'Project Alpha <support@yourdomain.com>'
     # In another project:
     DEFAULT_FROM_EMAIL = 'Project Beta <notifications@yourdomain.com>'
     ```
3. **Dedicated SMTP Keys:**
   - Go to **SMTP & API** in Brevo and click **Generate a new SMTP Key**.
   - Name each key after the project (e.g., `Chat_App_Production`, `ECommerce_Staging`).
   - If one project is retired or compromised, revoke that key without affecting your other applications.
4. **Free Tier Capacity:**
   - Brevo provides **300 free emails per day**, which is plenty for authentication, signups, and password recovery across multiple development and portfolio projects.

---

## ☁️ Production Deployment (Oracle Cloud VM)

The live production instance is deployed under the Oracle Cloud Always Free tier using the following operational structure:

### 1. Daphne Daemon Unit (`/etc/systemd/system/chat-app.service`)
```ini
[Unit]
Description=Daphne ASGI Server for Django Channels Chat App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/chat_server
ExecStart=/home/ubuntu/chat_server/venv/bin/daphne -b 127.0.0.1 -p 8001 chat_project.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 2. Nginx WebSocket & Reverse Proxy Configuration (`/etc/nginx/sites-available/chat_app`)
```nginx
server {
    server_name ybchatapp.duckdns.org;

    location /static/ {
        alias /home/ubuntu/chat_server/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl; # Managed by Certbot Let's Encrypt
}
```

---

## 📚 Complete Documentation Index

For deep-dive architecture notes, step-by-step learning milestones, and the complete debugging log:

- 📘 **[Phase 8 Milestone Guide](docs/chat_app_learning/Phase%208%20-%20Full-Stack%20Portfolio%20Overhaul,%20PWA,%20Brevo%20SMTP%20&%20Real-Time%20Engine.md):** Complete breakdown of the portfolio overhaul, PWA engine, Brevo email setup, and FIFO pruning mechanics.
- 📕 **[Errors & Fixes Playbook](docs/errors_and_fixes_log.md):** Comprehensive post-mortem log analyzing all technical obstacles (authentication backends collision, SMTP sender mismatches, mobile header wrapping bugs, etc.) from symptom to root cause.
- 📗 **[Production Deployment Log](docs/deployment_commands_log.md):** Step-by-step console commands for setting up Oracle Cloud VM, iptables, Daphne, Redis, and Nginx.
- 📙 **[Oracle Cloud Cost & VM Management](docs/oracle_cost_management_and_vm_control.md):** Best practices for keeping Oracle Always Free instances permanently within zero-cost limits.

---

## 👨‍💻 Author & Acknowledgements

- **Developer:** Brian Kuria ([@softdevbrian](https://github.com/softdevbrian))
- **Live Project:** [https://ybchatapp.duckdns.org](https://ybchatapp.duckdns.org)
- **Built With:** Django, Channels, Daphne, Redis, Vue.js, Brevo, and Oracle Cloud Infrastructure.
