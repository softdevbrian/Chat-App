# Phase 8: Full-Stack Portfolio Overhaul, PWA, Brevo SMTP & Real-Time Engine

---

## 📑 Document Index

1. [Phase 8 Overview & Portfolio Strategy](#1-phase-8-overview--portfolio-strategy)
2. [High-Level Architectural Blueprint](#2-high-level-architectural-blueprint)
3. [Database Architecture & The 100-Message FIFO Auto-Pruner](#3-database-architecture--the-100-message-fifo-auto-pruner)
4. [Dual-Mode Messaging & WebSocket Infrastructure](#4-dual-mode-messaging--websocket-infrastructure)
5. [Dual-Identity Authentication Engine](#5-dual-identity-authentication-engine)
6. [Comprehensive Brevo SMTP Guide & Multi-Project Reusability](#6-comprehensive-brevo-smtp-guide--multi-project-reusability)
   - [6.1 How Brevo SMTP Operates in This Architecture](#61-how-brevo-smtp-operates-in-this-architecture)
   - [6.2 Cryptographic Token Generation & Password Reset Flow](#62-cryptographic-token-generation--password-reset-flow)
   - [6.3 Reusing Your Brevo Account in Future Projects](#63-reusing-your-brevo-account-in-future-projects)
7. [Progressive Web App (PWA) Implementation & Favicon Suite](#7-progressive-web-app-pwa-implementation--favicon-suite)
   - [7.1 Web App Manifest (`chat/static/chat/manifest.json`)](#71-web-app-manifest-chatstaticchatmanifestjson)
   - [7.2 Service Worker Strategy (`chat/static/chat/sw.js`)](#72-service-worker-strategy-chatstaticchatswjs)
   - [7.3 Cross-Browser Favicon Suite Engineering & Linking](#73-cross-browser-favicon-suite-engineering--linking)
8. [UI/UX Overhaul: Desktop Split-Hero & Mobile Fluidity](#8-uiux-overhaul-desktop-split-hero--mobile-fluidity)
9. [Production Deployment & Live Verification](#9-production-deployment--live-verification)
10. [Key Architectural Lessons & Best Practices](#10-key-architectural-lessons--best-practices)

---

## 1. Phase 8 Overview & Portfolio Strategy

### 🎯 Objective
In Phases 0 through 7, we built a functional multi-room chat application and successfully deployed it live to an **Oracle Cloud Infrastructure (OCI) ARM64 Linux VM** using Daphne, Nginx, Redis, and automated Let's Encrypt SSL.

However, a basic demo room chat is not representative of modern commercial applications. In **Phase 8**, we completely overhauled the project into **Tuko Chat** — an enterprise-grade messaging platform and **Progressive Web App (PWA)** designed to showcase full-stack mastery in a developer portfolio:

- **From Static Rooms to Dynamic Messaging:** Replaced hardcoded chat rooms with a dual messaging system supporting user-created group channels and private 1-on-1 Direct Messages (DMs).
- **Persistent Yet Bounded Storage:** Implemented an automatic FIFO (First-In, First-Out) pruner that caps message storage at the **last 100 messages** per conversation, preventing database bloat while maintaining recollection.
- **Dual Login & Self-Service Account Recovery:** Added dual-identity authentication (sign in with Username OR Email) and cryptographic password resets powered by **Brevo SMTP Relay**.
- **Cross-Platform PWA Support:** Packaged the application with service worker offline caching and Web App Manifest icons, making it installable as a standalone app on phones and desktop.
- **Executive UI Redesign:** Replaced cramped single-column pages with a split-hero desktop layout, spacious header pills, a bottom-sheet members drawer, and the signature Slate & Electric Blue color theme.

---

## 2. High-Level Architectural Blueprint

The updated application architecture seamlessly integrates REST APIs, WebSocket consumers, asynchronous email delivery, and client-side PWA caching:

```
                            [ CLIENT PLATFORMS ]
              (Android / iOS PWA, Chrome, Firefox, Safari)
                                   │
                                   │ HTTPS (443) / WSS (443)
                                   ▼
              ┌─────────────────────────────────────────┐
              │           Nginx Reverse Proxy           │
              │  (SSL Termination & Direct Disk Cache)  │
              └────────────┬────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [ /static/ Assets ]         [ /ws/ & /api/ HTTP ]
    • CacheStorage              • Proxy to Daphne (:8001)
    • Service Worker (sw.js)    • ASGI Event Loop
    • Web Manifest              • Session & Auth State
                                         │
                                         ▼
                                ┌─────────────────┐
                                │ Django Channels │
                                └────────┬────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
      ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
      │   Channel Layer     │ │   SQLite Engine     │ │   Brevo SMTP Relay  │
      │ • Redis (Production)│ │ • FIFO 100-Msg Prune│ │ • Port 587 (TLS)    │
      │ • In-Memory (Local) │ │ • Custom DMs/Groups │ │ • Token Reset Link  │
      └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

---

## 3. Database Architecture & The 100-Message FIFO Auto-Pruner

### 3.1 Data Model Design (`chat/models.py`)

Three interconnected models drive all data persistence:

1. **`UserProfile` (`OneToOneField` with `User`):**
   - `avatar_id`: Stores the chosen avatar preset identifier (`avatar_1` to `avatar_8`).
   - `is_online`: Tracks real-time presence.
   - `last_seen`: Timestamp updated on connection/disconnection.

2. **`Conversation`:**
   - `name`: Human-readable channel name for groups (e.g., `#gamers`), or blank for DMs.
   - `is_direct_message`: Boolean distinguishing 1-on-1 private chats from public groups.
   - `created_by`: Foreign key pointing to the user who created the group.
   - `participants`: `ManyToManyField` referencing all users in the conversation.
   - `created_at`: Creation timestamp.

3. **`Message`:**
   - `conversation`: Foreign key to `Conversation`.
   - `sender`: Foreign key to `User`.
   - `text`: Message text content.
   - `timestamp`: UTC timestamp with auto-now-add.

### 3.2 The 100-Message FIFO Auto-Pruner Implementation

To keep the database lightweight and performant forever without running background cron jobs or external cleaners, we engineered an **in-transaction FIFO pruning method** directly on the `Conversation` model:

```python
def prune_messages(self, max_count=100):
    """
    Ensures the conversation retains at most `max_count` messages.
    Deletes older messages beyond the threshold in FIFO order.
    """
    total = self.messages.count()
    if total > max_count:
        excess = total - max_count
        # Identify IDs of the oldest messages beyond the retention window
        oldest_ids = list(
            self.messages.order_by('timestamp')
            .values_list('id', flat=True)[:excess]
        )
        if oldest_ids:
            self.messages.filter(id__in=oldest_ids).delete()
```

#### Why This Works:
- **Zero Background Overhead:** Evaluated on message reception and REST fetching.
- **Slice Deletion Safety:** In SQLite, direct `delete()` on a sliced queryset (e.g., `[:excess].delete()`) triggers an `AssertionError: Cannot filter a query once a slice has been taken.` By extracting the list of primary keys first (`.values_list('id', flat=True)`), deletion executes cleanly via `id__in=oldest_ids`.
- **Verified via Unit Tests:** Tested by firing 105 rapid sequential messages; the database precisely evicted the oldest 5 messages and preserved exactly 100.

---

## 4. Dual-Mode Messaging & WebSocket Infrastructure

### 4.1 Channels vs. Direct Messages (DMs)
- **Public Group Channels:** Any user can browse and join public channels (such as `#general`).
- **Private 1-on-1 DMs:** Created via the user search bar. When User A clicks User B in search results, the API checks if a DM already exists between them; if not, it instantiates an isolated `Conversation(is_direct_message=True)` containing exclusively those two participants.

### 4.2 Creator Governance & Moderation Rights
- The creator of a group is tracked via `conv.created_by`.
- When the creator opens their group, the frontend renders a distinct `👑 Owner` badge alongside a `🗑️ Delete Group` pill button.
- Calling `/api/groups/<id>/delete/` verifies that `request.user == conv.created_by`. Upon verification, the group and all its messages are deleted from SQLite.
- The WebSocket consumer broadcasts a `group_deleted` payload across the room group, notifying all connected participants to return to the lobby immediately.

### 4.3 Members Drawer / Bottom Sheet
The chat header features a dedicated `👥 <count> Members` toggle button. Tapping it opens a sleek sliding modal listing all participants with:
- Avatar emojis and gradient backgrounds.
- Username and badges (`👑 Owner`, `You`).
- Green glowing active presence dots.
- Real-time client synchronization: As new users message into the channel, Vue's reactive controller dynamically updates the member array.

---

## 5. Dual-Identity Authentication Engine

### 5.1 The Problem with Default Django Authentication
By default, Django's `ModelBackend` authenticates strictly against the `username` field. If a user enters their registered email address (`brian@gmail.com`) into the login input, authentication fails with `Invalid credentials`.

### 5.2 The Custom Authentication Backend (`chat/backends.py`)
We engineered `EmailOrUsernameModelBackend` inheriting from `ModelBackend`:

```python
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_id = username or kwargs.get('login_id')
        if not login_id:
            return None

        # Case-insensitive lookup matching either username OR email
        user = User.objects.filter(
            Q(username__iexact=login_id) | Q(email__iexact=login_id)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

Registered in `chat_project/settings.py`:
```python
AUTHENTICATION_BACKENDS = [
    'chat.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

---

## 6. Comprehensive Brevo SMTP Guide & Multi-Project Reusability

### 6.1 How Brevo SMTP Operates in This Architecture
When a user forgets their password, they submit their email at `/forgot-password/`. Django dispatches a branded HTML email containing a secure one-time reset link via **Brevo SMTP Relay** (`smtp-relay.brevo.com`).

#### Django SMTP Configuration (`chat_project/settings.py`):
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('BREVO_SMTP_LOGIN', 'bd87da001@smtp-brevo.com')
EMAIL_HOST_PASSWORD = os.environ.get('BREVO_SMTP_KEY', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Tuko Chat <briankuriasupport@gmail.com>')
```

### 6.2 Cryptographic Token Generation & Password Reset Flow

```
User enters Email
       │
       ▼
[ Django views.forgot_password_view ]
       │
       ├─► 1. Lookup User by email
       ├─► 2. Generate Base64 UID: urlsafe_base64_encode(force_bytes(user.pk))
       ├─► 3. Generate Cryptographic Token: default_token_generator.make_token(user)
       └─► 4. Render HTML Email: render_to_string('chat/emails/password_reset_email.html')
       │
       ▼
[ Brevo SMTP Relay (:587 TLS) ] ──► Delivered to User's Inbox
       │
       ▼
User clicks: https://ybchatapp.duckdns.org/reset-password/<uidb64>/<token>/
       │
       ▼
[ Django views.reset_password_confirm_view ]
       │
       ├─► Decode UID: force_str(urlsafe_base64_decode(uidb64))
       ├─► Verify Token: default_token_generator.check_token(user, token)
       └─► If Valid: Allow setting new password via user.set_password()
```

### 6.3 Reusing Your Brevo Account in Future Projects

You can use this exact same Brevo account across all your future personal, freelance, and portfolio projects without paying for new accounts or setting up separate providers. Here is the exact blueprint:

#### 1. Senders & Verified Domains
- Brevo enforces that the email address in `DEFAULT_FROM_EMAIL` must belong to a **Verified Sender** in your account.
- **Adding a new sender for a new project:**
  1. Log into your [Brevo Dashboard](https://app.brevo.com/).
  2. Click your account name at the top right -> **Senders, Domains & Dedicated IPs** -> **Senders**.
  3. Click **Add a sender**.
  4. Enter the sender name (e.g. `Portfolio App` or `Store Support`) and the email address (e.g. `myotherproject@gmail.com`).
  5. Brevo will send a 6-digit verification code / link to that inbox. Once confirmed, that sender is instantly activated.

#### 2. Project-Specific Custom Sender Names
In your future projects, you can customize the sender name displayed in the user's inbox simply by altering `DEFAULT_FROM_EMAIL` in `.env`:
```ini
# Project A (Chat App)
DEFAULT_FROM_EMAIL="Tuko Chat <briankuriasupport@gmail.com>"

# Project B (E-Commerce Store)
DEFAULT_FROM_EMAIL="Kuria Store <briankuriasupport@gmail.com>"

# Project C (SaaS Dashboard)
DEFAULT_FROM_EMAIL="Nova Analytics <briankuriasupport@gmail.com>"
```
*Because the underlying email address (`briankuriasupport@gmail.com`) is verified, Brevo will accept all of them and brand the sender accordingly!*

#### 3. Generating Dedicated SMTP Keys per Project
Never reuse the same master SMTP key across different codebases or repositories:
1. In Brevo Dashboard, go to **SMTP & API** -> **SMTP**.
2. Click **Generate a new SMTP Key**.
3. Name the key specifically after the project (e.g., `Project_Ecommerce_Staging`, `ChatApp_Production`).
4. Copy the key and store it in that project's `.env` as `BREVO_SMTP_KEY`.
5. **Benefit:** If one repository is made public or deprecated, you can revoke its key instantly from Brevo without disrupting any of your other live projects.

#### 4. Understanding Rate Limits & Best Practices
- **Free Tier Allowance:** Brevo provides **300 free emails per day** (which resets every 24 hours at 00:00 UTC).
- **Adequacy:** For transactional emails (password resets, account confirmations, email verification), 300 emails/day is more than enough to power 5 to 10 simultaneous demo and portfolio apps.
- **Spam Avoidance:** Always send transactional emails using clean HTML templates with unsubscribe/contact details and realistic subjects to maintain high inbox deliverability.

---

## 7. Progressive Web App (PWA) Implementation

### 7.1 Web App Manifest (`chat/static/chat/manifest.json`)
Defines the installation metadata:
```json
{
  "name": "Tuko Chat",
  "short_name": "TukoChat",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#0f172a",
  "icons": [
    {
      "src": "/static/chat/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/chat/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 7.2 Service Worker Strategy (`chat/static/chat/sw.js`)
- **Install & Pre-cache:** Caches critical UI stylesheets, fonts, and icons.
- **Cache-First Network Fallback:** Intercepts fetch requests; serves static assets from `caches` immediately and falls back to network when offline.
- **WebSocket Exemption:** WebSockets bypass service worker interception directly to Daphne.
- **Install Prompt Handling:** Captured in Vue's `onMounted` lifecycle via `beforeinstallprompt`, surfacing an in-app `📱 Install` button in the user header whenever available.

### 7.3 Cross-Browser Favicon Suite Engineering & Linking

A commercial-grade PWA requires a cohesive visual identity not only when installed, but also across web browsers, operating system taskbars, and bookmark trays.

#### 1. Why Modern Browsers Need Multiple Icon Formats:
- **Vector SVG (`favicon.svg`):** Modern desktop and mobile browsers (Chrome 80+, Firefox, Edge, Safari 14+) prioritize SVG favicons. They remain vector-sharp on high-density Retina/4K displays and scale from 16px to 512px without blurriness.
- **32x32 PNG (`favicon-32x32.png`):** Standard pixel-perfect fallback for Chromium and Gecko tab headers.
- **Multi-Resolution ICO (`favicon.ico`):** Traditional container required by legacy clients, Windows taskbar pinning, desktop shortcuts, and automated web crawlers that ping `/favicon.ico` at the domain root.
- **Apple Touch Icon (`icon-192.png`):** Used by iOS Safari when users tap *"Add to Home Screen"* and on Android launcher panels.

#### 2. Vector SVG Engineering (`chat/static/chat/favicon.svg`):
We designed a modern squircle badge matching Tuko Chat's signature Slate & Electric Blue aesthetic:
- **Base Geometry:** A 64x64 viewBox with an 18px rounded corner squircle (`rx="18"`).
- **Brand Gradient:** A 45-degree linear gradient transitioning from vibrant blue (`#3b82f6`) to deep indigo (`#6366f1`).
- **Focal Mark:** A crisp, centered white lightning bolt path (`M36 7 L18 35 L32 35 L27 57 L47 29 L33 29 Z`) with a subtle ambient drop shadow (`#boltGlow`).

#### 3. Programmatic Zero-Dependency Binary Generation (PNG & ICO):
To generate the binary PNG and ICO assets locally without third-party imaging dependencies (like Pillow), we built an in-memory generator using Python’s native `struct` and `zlib` modules:
- Formatted the lightning bolt polygon coordinates and calculated anti-aliased pixel boundaries via ray-casting.
- Built raw RGBA bytebuffers with squircle corner radius math.
- Streamed compressed PNG chunks (`IHDR`, `IDAT`, `IEND`).
- Packaged the PNG stream into an MS-ICO container by generating the 6-byte `ICONDIR` header and 16-byte `ICONDIRENTRY` struct pointing to the embedded PNG payload.

#### 4. Universal Template Integration:
Linked the complete icon suite into the `<head>` of all application templates (`dashboard.html`, `auth.html`, `reset_password_confirm.html`):
```html
<!-- Favicon Links -->
<link rel="icon" type="image/svg+xml" href="{% static 'chat/favicon.svg' %}">
<link rel="icon" type="image/png" sizes="32x32" href="{% static 'chat/favicon-32x32.png' %}">
<link rel="shortcut icon" href="{% static 'chat/favicon.ico' %}">
<link rel="apple-touch-icon" href="{% static 'chat/icon-192.png' %}">
```

#### 5. Server Synchronization & Static Asset Caching:
1. Deployed `favicon.svg`, `favicon-32x32.png`, and `favicon.ico` to the Oracle Cloud VM at `/home/ubuntu/chat_server/chat/static/chat/`.
2. Executed `python3 manage.py collectstatic --noinput` to copy assets to `/home/ubuntu/chat_server/staticfiles/`.
3. Reloaded Nginx to serve the new icons with a 30-day client cache header (`Cache-Control: public, max-age=2592000`).
4. Verified live delivery via curl:
   ```bash
   curl -sI https://ybchatapp.duckdns.org/static/chat/favicon.svg
   # Output: HTTP/1.1 200 OK, Content-Type: image/svg+xml
   ```

---

## 8. UI/UX Overhaul: Desktop Split-Hero & Mobile Fluidity

### 8.1 The Desktop Widescreen Squeeze Fix
- **Previous Issue:** On widescreen monitors (1920x1080), auth cards were locked to a narrow 380px single-column container, floating like an awkward phone emulator in a massive void.
- **The Solution:** Engineered a **Two-Pane Split-Hero Layout (`minmax(0, 1.15fr) minmax(0, 1fr)`)**:
  - *Left Pane (Showcase):* Branded banner (`⚡ Tuko Chat v2.0`), typography headline (*"Tuko pamoja."*), feature value propositions, and an animated mock chat conversation.
  - *Right Pane (Form):* Spacious form controls, tab switcher, show/hide password buttons, live password confirmation checks, and 2-column input grids.

### 8.2 The Mobile Chat Header Fix
- **Previous Issue:** Buttons wrapped text vertically into square blocks (`[ Delete ] / [ Group ]`) on narrow screens, and group titles collided with ownership tags.
- **The Solution:**
  - Added `white-space: nowrap; flex-shrink: 0;` across all action items.
  - Replaced long creator tags with a compact `👑 Owner` badge.
  - Added media query rules (`@media (max-width: 480px)`) that collapse pill text labels on mobile while keeping icon and member counts intact (`👥 2` and `🗑️`).

### 8.3 Signature Slate & Electric Blue Design System
- **Background (`--bg`):** `#0f172a` (Tailwind Slate-900).
- **Surface / Cards (`--surface`):** `#1e293b` (Slate-800).
- **Fields / Inputs (`--field`):** `#0b1120` (Dark obsidian).
- **Borders (`--line`):** `#334155` (Slate-700).
- **Text (`--text`):** `#f8fafc` (Slate-50) & `#94a3b8` (Slate-400).
- **Accent:** `#38bdf8` (Electric sky blue) and `linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)` for primary CTAs and outgoing chat bubbles.

---

## 9. Production Deployment & Live Verification

All Phase 8 enhancements were deployed live to the Oracle Cloud ARM64 VM (`ubuntu@130.61.9.37`):

1. **Asset Transfer:** Deployed updated models, views, consumers, static files, and templates to `/home/ubuntu/chat_server/`.
2. **Database Migration:** Applied schema migrations on the VM for `UserProfile` and `Conversation` models.
3. **Static Collection:** Executed `python3 manage.py collectstatic --noinput` to refresh Nginx's static cache.
4. **Daemon Restart:** Restarted `chat-app` systemd service:
   ```bash
   sudo systemctl restart chat-app && sudo systemctl reload nginx
   ```
5. **Live Verification:** Verified HTTP 200 responses, WebSocket upgrades, Brevo password reset delivery, and PWA manifest detection on **`https://ybchatapp.duckdns.org`**.

---

## 10. Key Architectural Lessons & Best Practices

1. **Authentication Backend Disambiguation:** When implementing custom authentication backends, always pass the explicit `backend` argument to `django.contrib.auth.login(request, user, backend=...)` to avoid multi-backend ambiguity errors.
2. **SMTP Envelope Alignment:** The `DEFAULT_FROM_EMAIL` address must match a verified sender identity on Brevo; otherwise, the relay will reject delivery with a `550 / 454 Sender Not Allowed` error.
3. **Responsive Flex Truncation:** In dense headers containing dynamic titles, always pair `white-space: nowrap` and `text-overflow: ellipsis` with `min-width: 0;` on parent flex containers; otherwise, child elements will refuse to shrink below their content width.
4. **SQLite Slicing Safety:** In Django ORM, never call `.delete()` directly on an already-sliced queryset. First extract the target IDs (`.values_list('id', flat=True)`), then delete by ID filter.
5. **PWA Standalone UX:** Progressive Web Apps require both high-resolution icons (at least 192px and 512px) and an active `fetch` listener in the service worker to satisfy Chromium's installability criteria.
