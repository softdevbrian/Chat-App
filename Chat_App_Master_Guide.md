# Antigravity Master Guide: Real-Time Chat App Learning Project

## Purpose of This Document

This document is a **template and instruction set for Antigravity** (the AI coding agent) on how to walk the user through building a **Real-Time Multi-Room Chat Application** from absolute beginner to expert level, using the exact same technology stack that powers the **Tuko Kadi Online Multiplayer** relay server.

By the end of this project, the user will deeply understand:
- Django & Django Channels
- WebSockets (connect, disconnect, send, receive)
- ASGI vs WSGI
- Redis as a pub/sub message broker
- Room groups and message broadcasting
- Nginx reverse proxy with SSL/WSS
- Daphne ASGI production server
- systemd services
- Reconnection resilience
- Connecting from a Flutter/Dart client

---

## Rules for Antigravity

### Pacing & Interaction
1. **Execute one phase at a time.** Never jump ahead.
2. **After completing each phase**, create a detailed explanation Markdown file in:
   ```
   C:\My_Projects\# Django Projects\CHAT_APP\docs\chat_app_learning\Phase X - Phase Name.md
   ```
   *(Optionally mirrored to `C:\My_Projects\#Flutter Projects\TUKO_KADI\#TukoKadi Projo\docs\chat_app_learning\` for easy reference from the Flutter workspace).*
3. The phase MD file must include:
   - **What we just built** — plain English summary
   - **Every file we created or modified** — with the full file content and line-by-line explanations
   - **Key concepts explained** — as if teaching a complete beginner (what is ASGI? what is a WebSocket? what is Redis? etc.)
   - **How this maps to Tuko Kadi** — a dedicated section showing the direct parallel to the card game relay
   - **Diagram(s)** — Mermaid diagrams showing data flow where applicable
   - **Common mistakes & debugging tips**
   - **Glossary** — define any new technical terms introduced in this phase
4. After creating the phase MD file, **stop and ask the user**:
   > "Phase X is complete. I've created the detailed explanation at [link]. Do you have any questions about what we just implemented? If not, let me know and I'll proceed to Phase Y."
5. **Only proceed to the next phase after the user explicitly approves.**
6. If the user has questions, answer them thoroughly, update the phase MD file if needed, and re-ask for approval.

### Code & Infrastructure Division
- **Antigravity writes all code**: Creates files, writes Python/HTML/JS/Dart, edits configs.
- **The user handles infrastructure**: SSH into Oracle VM, run deployment commands, set up DuckDNS, etc. Antigravity provides the exact commands but the user executes infrastructure steps.
- **Antigravity runs local commands**: `python manage.py check`, `pip install`, etc. on the user's Windows machine.

### Local Development Strategy (Windows)
- **Phases 2–5:** Use Django's `InMemoryChannelLayer` (built into Channels, requires zero additional software). This lets us build and test WebSockets without Redis on Windows.
- **Phase 4:** Explain what Redis does conceptually, configure `CHANNEL_LAYERS` with both `InMemoryChannelLayer` (active) and `RedisChannelLayer` (commented out, ready for production). The user sees the code for both.
- **Phase 7 (Deployment):** Switch to `RedisChannelLayer` on the Oracle VM where Redis is installed. This is where the user first sees Redis working live.
- **Why this approach:** Redis does not natively run on Windows. Rather than requiring Docker Desktop or WSL2 (complex setups that distract from learning Django), we use the in-memory layer locally and Redis in production. This mirrors how many Django developers work.

### Project Locations
- **Master Guide Location**: `C:\My_Projects\# Django Projects\CHAT_APP\Chat_App_Master_Guide.md`
- **Django Chat Server Project Root**: `C:\My_Projects\# Django Projects\CHAT_APP\`
- **Phase Explanation Files**: `C:\My_Projects\# Django Projects\CHAT_APP\docs\chat_app_learning\`
- **Flutter Client Code** (Phase 10): Inside the existing Tuko Kadi project (`lib/screens/chat_test/`)

### Naming Convention for Phase Files
```
Phase 0 - Project Overview.md
Phase 1 - Python and Tools Setup.md
Phase 2 - Django Project Scaffolding.md
Phase 3 - WebSockets and Your First Consumer.md
Phase 4 - Redis and Room Groups.md
Phase 5 - Building the Chat Frontend.md
Phase 6 - User Presence and Notifications.md
Phase 7 - Production Deployment.md
Phase 8 - Reconnection and Resilience.md
Phase 9 - Emoji Reactions and Advanced Features.md
Phase 10 - Connecting from Flutter.md
Phase 11 - Review and Tuko Kadi Bridge.md
```

---

## Phase Overview

### Phase 0 — Project Overview & Prerequisites
**What:** Explain the big picture — what we're building, why, and how every piece maps to Tuko Kadi.
**Antigravity actions:**
- Create `Phase 0 - Project Overview.md` with:
  - The overall Tuko Kadi online multiplayer goal and why a chat app is the perfect training project
  - Architecture diagram: `Client → Internet → Nginx (SSL) → Daphne → Redis → Daphne → Nginx → Client`
  - Technology stack table with explanations of each tool and why it was chosen
  - Concept mapping table: Chat App feature → Tuko Kadi equivalent
  - The "develop locally, deploy to cloud" workflow explained (why we build on Windows first, then deploy to Oracle VM)
  - Overview of all 11 phases so the user sees the full journey
- Create the project directories:
  - `C:\My_Projects\# Django Projects\CHAT_APP\`
  - `C:\My_Projects\# Django Projects\CHAT_APP\docs\chat_app_learning\`
**User actions:** Read and understand the big picture.
**Checkpoint:** Ask if the user has questions before proceeding.

---

### Phase 1 — Python & Tools Setup
**What:** Install Python on Windows, verify it works, explain what pip and virtualenv are.
**Antigravity actions:**
- Check if Python 3 is already installed (`python --version` / `python3 --version`)
- If not installed, guide the user to download from [python.org](https://www.python.org/downloads/) with these critical notes:
  - **CHECK "Add python.exe to PATH"** during installation (most common beginner mistake)
  - Verify with `python --version` and `pip --version` after install
- Create `Phase 1 - Python and Tools Setup.md` with:
  - What is Python? (the language our server is written in)
  - What is pip? (Python's package manager — like `pub` for Dart)
  - What is a virtual environment? (an isolated folder of Python packages — like a sandbox)
  - Why we use a virtualenv (avoids polluting system Python, makes deployment reproducible)
  - How `pip` compares to Dart's `pub` and `pubspec.yaml`
  - Prerequisites checklist:
    - [ ] Python 3.10+ installed and on PATH
    - [ ] `pip --version` works
    - [ ] Oracle VM is ready (from infrastructure guide)
    - [ ] DuckDNS domain is resolving
    - [ ] SSL certificate is working
  - Reference to the existing `infrastructure_setup_guide.md` for cloud setup
  - How SSL/WSS works (TLS handshake explained simply with a diagram)
  - Why mobile apps (Android/iOS) require WSS and reject plain WS
**User actions:** Install Python if not present, verify prerequisites.
**Checkpoint:** Ask if the user has questions.

---

### Phase 2 — Django Project Scaffolding
**What:** Create the Django project locally on Windows, understand every generated file.
**Antigravity actions:**
- Create virtualenv inside `C:\My_Projects\# Django Projects\CHAT_APP\`:
  ```pwsh
  cd "C:\My_Projects\# Django Projects\CHAT_APP"
  python -m venv venv
  venv\Scripts\activate   # Windows activation
  pip install django channels daphne
  django-admin startproject chat_project .
  python manage.py startapp chat
  ```
- Initialize Git repo with `.gitignore` (exclude `venv/`, `__pycache__/`, `db.sqlite3`, `*.pyc`)
- Create `Phase 2 - Django Project Scaffolding.md` with:
  - What is Django? (web framework, MVT pattern explained)
  - What is a "project" vs an "app"? (`chat_project` = the overall config, `chat` = one feature module)
  - Every single generated file explained in detail:
    - `manage.py` — the command-line Swiss army knife
    - `chat_project/settings.py` — the central brain (every default setting explained)
    - `chat_project/urls.py` — URL routing (like Flutter's route table)
    - `chat_project/wsgi.py` — traditional HTTP entry point (we won't use this)
    - `chat_project/asgi.py` — async entry point (THIS is what Daphne uses)
    - `chat/models.py` — database models (we won't use these for the relay)
    - `chat/views.py` — HTTP request handlers
    - `chat/apps.py` — app configuration
  - What is `INSTALLED_APPS`? Why does `daphne` need to be first?
  - What is `SECRET_KEY`? (Django's encryption key — never commit to public repos, but fine for this learning project)
  - Run `python manage.py check` to verify
  - Run `python manage.py runserver` and visit `http://127.0.0.1:8000` to see Django's welcome page
  - How this compares to Flutter project structure (`pubspec.yaml` = `settings.py`, `lib/` = `chat/`)
  - Tuko Kadi mapping: This is the same structure as `tuko_server/` on the Oracle VM
**User actions:** None (Antigravity creates everything locally on Windows).
**Checkpoint:** Ask if the user has questions.

---

### Phase 3 — WebSockets & Your First Consumer
**What:** Add Django Channels, write the first WebSocket consumer that echoes messages, and test it.
**Antigravity actions:**
- Create `chat/consumers.py` with a simple **echo consumer** (receives a message, sends it back)
- Create `chat/routing.py` with WebSocket URL routing
- Update `chat_project/asgi.py` to use `ProtocolTypeRouter` and `URLRouter`
- Configure `CHANNEL_LAYERS` with `InMemoryChannelLayer` in `settings.py`
- Add `ASGI_APPLICATION = 'chat_project.asgi.application'` to `settings.py`
- Create `Phase 3 - WebSockets and Your First Consumer.md` with:
  - **What is HTTP?** (request → response, connection closes) with diagram
  - **What is WebSocket?** (persistent bidirectional pipe, both sides can send at any time) with diagram
  - **HTTP vs WebSocket side-by-side comparison** with Mermaid sequence diagrams
  - **What is the WebSocket upgrade handshake?** (starts as HTTP, upgrades to WS)
  - **What is ASGI?** (Asynchronous Server Gateway Interface — async version of WSGI, required for WebSockets)
  - **What is WSGI?** (the traditional synchronous protocol — cannot handle WebSockets)
  - **What is a Consumer?** (Django Channels' equivalent of a View, but for WebSocket connections)
  - The consumer lifecycle: `connect()` → `receive()` → ... → `disconnect()`
  - Line-by-line explanation of every line in the echo consumer
  - Line-by-line explanation of `routing.py` (URL patterns for WebSockets)
  - Line-by-line explanation of `asgi.py` (the protocol router)
  - **How to test manually:** Open browser, press F12, go to Console tab, run:
    ```javascript
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/chat/test/');
    ws.onopen = () => { console.log('Connected!'); ws.send('Hello server!'); };
    ws.onmessage = (e) => console.log('Echo:', e.data);
    ```
  - **Error handling:** Add `try/except json.JSONDecodeError` in `receive()` with explanation of why malformed data must be caught
  - **Debugging tips:** Common errors (consumer not found, 403 forbidden, connection refused) and how to fix each
  - Tuko Kadi mapping: `consumers.py` → `GameRelayConsumer`, `routing.py` → WebSocket URL with room codes
**User actions:** Test the WebSocket in their browser console.
**Checkpoint:** Ask if the user has questions.

---

### Phase 4 — Redis & Room Groups
**What:** Explain Redis and Channel Layer groups, implement multi-room message broadcasting. Still using `InMemoryChannelLayer` locally, but the code is production-ready.
**Antigravity actions:**
- Update `consumers.py` to use `self.channel_layer.group_add()`, `group_send()`, `group_discard()`
- Room name is extracted from the URL: `ws/chat/<room_name>/`
- Messages sent by one user appear in all connected clients in the same room
- Show both channel layer configs in `settings.py` (InMemory active, Redis commented with explanation):
  ```python
  # LOCAL DEVELOPMENT (no Redis needed on Windows):
  CHANNEL_LAYERS = {
      'default': {
          'BACKEND': 'channels.layers.InMemoryChannelLayer',
      },
  }

  # PRODUCTION (uncomment on Oracle VM where Redis is installed):
  # CHANNEL_LAYERS = {
  #     'default': {
  #         'BACKEND': 'channels_redis.core.RedisChannelLayer',
  #         'CONFIG': { 'hosts': [('127.0.0.1', 6379)] },
  #     },
  # }
  ```
- Create `Phase 4 - Redis and Room Groups.md` with:
  - **What is Redis?** (ultra-fast in-memory database, used as a message broker here)
  - **Why do we need Redis?** (InMemoryChannelLayer only works within a single process — if you run 2 Daphne workers, they can't talk to each other. Redis is the shared backbone.)
  - **What is a Channel Layer?** (Django Channels' abstraction for inter-process messaging)
  - **What is a Channel?** (a unique ID for each connected WebSocket — like a phone number)
  - **What is a Group?** (a named collection of channels — like a group chat or a game room)
  - **The three critical Group operations:**
    - `group_add(group_name, channel_name)` = "add this phone to this group chat"
    - `group_send(group_name, message)` = "send this message to everyone in the group"
    - `group_discard(group_name, channel_name)` = "remove this phone from the group chat"
  - Diagram: Multiple clients → Daphne → Channel Layer → Redis → fan-out to all group members
  - **InMemoryChannelLayer vs RedisChannelLayer** — comparison table, when to use each
  - **Why we use InMemory locally:** Redis doesn't run natively on Windows. We switch to Redis on the VM.
  - **Important limitation:** InMemoryChannelLayer only works within a **single Daphne process**. Two separate `runserver` commands can't communicate. Redis solves this in production.
  - Test with 2+ browser tabs in the same room — type in one, see it in all
  - Tuko Kadi mapping: Each game room (`game_K7M9X2`) = a Channel Layer group. `group_add` = player joins. `group_send` = host broadcasts game state. `group_discard` = player leaves/disconnects.
**User actions:** Test with multiple browser tabs.
**Checkpoint:** Ask if the user has questions.

---

### Phase 5 — Building the Chat Frontend
**What:** Create a proper HTML/CSS/JS chat interface served by Django, replacing the browser console testing.
**Antigravity actions:**
- Create `chat/templates/chat/index.html` — landing page with room name input and "Join" button
- Create `chat/templates/chat/room.html` — full chat interface with:
  - Message display area (scrollable, auto-scrolls to bottom)
  - Username input (or prompt on page load)
  - Message text input + send button
  - Connection status indicator (green/red dot)
  - Room name displayed in header
- Create `chat/static/chat/style.css` — clean, modern styling
- Create `chat/views.py` — Django views for `index` and `room`
- Update `chat_project/urls.py` — route `/` and `/chat/<room_name>/`
- Configure static files in `settings.py`:
  ```python
  STATIC_URL = '/static/'
  STATICFILES_DIRS = []  # Django finds app-level static/ folders automatically
  ```
- Create `Phase 5 - Building the Chat Frontend.md` with:
  - **What are Django templates?** (HTML files with special tags like `{{ variable }}` and `{% url %}`)
  - **What are static files?** (CSS, JS, images — served separately from templates)
  - **How Django finds templates** (`APP_DIRS=True` in settings → looks in `chat/templates/chat/`)
  - **JavaScript WebSocket API in detail:**
    - `new WebSocket(url)` — creates the connection
    - `ws.onopen` — fires when connected
    - `ws.onmessage` — fires when a message arrives
    - `ws.onerror` — fires on error
    - `ws.onclose` — fires when disconnected
    - `ws.send(data)` — sends a message to the server
  - **JSON message protocol** — why we use JSON (structured, extensible, same as Tuko Kadi's `GameMessage`)
  - **Message format convention:**
    ```json
    {"type": "chat_message", "username": "Brian", "message": "Hello!"}
    ```
  - Auto-scroll implementation explained
  - "You" vs other users styling (align right vs left, like WhatsApp/iMessage)
  - `DEBUG=True` static file serving vs production (`collectstatic` + Nginx)
  - Tuko Kadi mapping: The browser is playing the role of the Flutter app. The JS WebSocket code is equivalent to what `GameClient` does in Dart.
**User actions:** Open browser, create rooms, chat between tabs.
**Checkpoint:** Ask if the user has questions.

---

### Phase 6 — User Presence & Notifications
**What:** Track who's connected in each room, broadcast join/leave events, show online user list.
**Antigravity actions:**
- Update `consumers.py` to:
  - Accept `username` via the first message after connection (a `set_username` message type)
  - Maintain a **class-level dictionary** of connected users per room: `room_users = {}` (dict of room_name → set of usernames)
  - On connect: add user to set, broadcast `user_joined` to group, send current user list to the new user
  - On disconnect: remove user from set, broadcast `user_left` to group
  - Handle edge case: browser crash (no clean disconnect) — `disconnect()` still fires
- Update `room.html` to:
  - Display online users sidebar with count badge
  - Show join/leave notifications as system messages (gray, centered)
  - Update sidebar dynamically when `user_joined` / `user_left` messages arrive
- Add **multiple message types** in the consumer's `receive()`:
  ```python
  data = json.loads(text_data)
  msg_type = data.get('type')
  if msg_type == 'set_username':
      ...
  elif msg_type == 'chat_message':
      ...
  ```
- Create `Phase 6 - User Presence and Notifications.md` with:
  - **Managing state in async consumers:**
    - Instance variables (`self.username`) — per-connection
    - Class variables (`cls.room_users`) — shared across all connections in the same process
    - Why class variables work with `InMemoryChannelLayer` but need Redis-backed storage in production (for multi-worker setups)
  - **`self.send()` vs `self.channel_layer.group_send()`:**
    - `self.send()` = send to THIS one client (private message, initial state sync)
    - `group_send()` = send to ALL clients in the room (broadcast)
  - **Multiple message types in one consumer** — the `type` field pattern (same pattern Tuko Kadi uses for `playCard`, `drawCard`, `nikoKadi`, `gameStateSnapshot`, etc.)
  - **Graceful disconnect handling** — why `disconnect()` must always clean up (browser crash, network drop, tab close all trigger it)
  - Tuko Kadi mapping:
    - `user_joined` → `playerJoined` in lobby
    - `user_left` → `playerLeft` / `playerDisconnected`
    - User list sidebar → Lobby player roster (avatars, names, ready status)
    - `set_username` first-message pattern → `registerPlayer` message in Tuko Kadi
**User actions:** None (Antigravity updates the code).
**Checkpoint:** Ask if the user has questions.

---

### Phase 7 — Production Deployment
**What:** Deploy the chat app to the Oracle VM with Nginx, SSL, Daphne, and Redis — making it accessible from anywhere in the world.
**Antigravity actions:**
- Generate a deployment script and step-by-step instructions for the user
- Create `Phase 7 - Production Deployment.md` with:

  **7.1 — Transferring code to the VM:**
  - Use `scp` (Secure Copy) to upload the project from Windows to the VM (excluding the local `venv/`):
    ```pwsh
    scp -i ~\.ssh\id_ed25519 -r "C:\My_Projects\# Django Projects\CHAT_APP" ubuntu@YOUR_VM_IP:~/chat_server/
    ```
  - Explain what `scp` does (copies files over SSH — like drag-and-drop but via terminal)
  - Alternative: create the files directly on the VM via `nano` or Git

  **7.2 — Setting up the VM environment:**
  - Create virtualenv on the VM: `python3 -m venv venv && source venv/bin/activate`
  - Install dependencies: `pip install django channels channels-redis daphne`
  - Note: on ARM64 (Ampere), all pip packages install smoothly

  **7.3 — Switch to Redis channel layer:**
  - Uncomment `RedisChannelLayer` config in `settings.py`, comment out `InMemoryChannelLayer`
  - Verify Redis is running: `redis-cli ping` → `PONG`
  - Set `DEBUG = False` and add domain to `ALLOWED_HOSTS`

  **7.4 — Collect static files for production:**
  ```bash
  python manage.py collectstatic --noinput
  ```
  - Explain why: Django's dev server serves static files automatically, but Daphne does NOT. Nginx serves them instead from `STATIC_ROOT`.
  - Add `STATIC_ROOT = '/home/ubuntu/chat_server/staticfiles/'` to `settings.py`

  **7.5 — Nginx configuration:**
  - Create `/etc/nginx/sites-available/chat_app` with:
    - Port 80 → 301 redirect to HTTPS
    - Port 443 with SSL (reuse existing cert or get a new one)
    - `/ws/chat/` → proxy to Daphne on 127.0.0.1:8001 (different port than Tuko Kadi's 8000)
    - `/static/` → serve from `STATIC_ROOT`
    - `/` → health check page
  - Explain every Nginx directive

  **7.6 — systemd service:**
  - Create `/etc/systemd/system/chat-app.service` (runs Daphne on port 8001)
  - Enable + start
  - How to check logs: `sudo journalctl -u chat-app -f`

  **7.7 — Testing from phone:**
  - Open phone browser → `https://YOUR_DOMAIN.duckdns.org/chat/`
  - Join a room, send messages from phone AND laptop simultaneously
  - This proves: DNS ✓, SSL ✓, Nginx ✓, Daphne ✓, Redis ✓, WebSocket ✓

  **7.8 — Debugging production issues:**
  - `sudo journalctl -u chat-app -f` — live Daphne logs
  - `sudo journalctl -u nginx -f` — live Nginx logs
  - `sudo nginx -t` — test config syntax
  - `redis-cli monitor` — watch Redis messages in real time
  - Common errors: 502 Bad Gateway (Daphne not running), 403 Forbidden (`ALLOWED_HOSTS`), connection refused (firewall)

  - Tuko Kadi mapping: This is the EXACT same deployment process for the game relay — same Nginx, same Daphne, same Redis, same systemd. Only the consumer logic differs.

**User actions:** SSH into VM, run the deployment commands, test from phone browser.
**Checkpoint:** Ask if the user has questions.

---

### Phase 8 — Reconnection & Resilience
**What:** Handle disconnects gracefully — auto-reconnect, heartbeats, connection status UI.
**Antigravity actions:**
- Update the JavaScript frontend (`room.html`) to:
  - Auto-reconnect with **exponential backoff** (1s → 2s → 4s → 8s → 16s → max 30s)
  - Show a "Reconnecting..." banner overlay during reconnection attempts
  - Re-send `set_username` after reconnecting (server doesn't remember you)
  - Show "Connected" / "Disconnected" status indicator
- Update the Django consumer to:
  - Send periodic **ping** messages every 30 seconds
  - Detect dead connections via ping timeout
- Update Nginx config:
  - Verify `proxy_read_timeout 86400s` is set (prevents Nginx from killing idle WebSockets)
- Create `Phase 8 - Reconnection and Resilience.md` with:
  - **Why do connections drop?** (mobile network switch, carrier NAT timeout ~30-60s, phone sleep, app backgrounded, poor signal, server restart)
  - **Exponential backoff explained** with diagram:
    - Attempt 1: wait 1s
    - Attempt 2: wait 2s
    - Attempt 3: wait 4s
    - ... doubles each time up to max 30s
    - Why: prevents thousands of clients from hammering the server simultaneously after an outage
  - **Ping/pong heartbeat explained:**
    - Server sends `{"type": "ping"}` every 30 seconds
    - Client responds with `{"type": "pong"}`
    - If server gets no pong within 60s, it closes the connection (triggers client reconnect)
    - If client gets no ping within 60s, it assumes the server is dead and reconnects
  - **What happens to missed messages?** (they're lost — the chat app doesn't buffer. Tuko Kadi solves this by re-sending the full game state snapshot on reconnect)
  - **Nginx timeout chain:** Client ↔ Nginx (`proxy_read_timeout`) ↔ Daphne (`--ping-interval`) ↔ Consumer (application-level ping)
  - Tuko Kadi mapping: `GameClient` needs the same reconnection with exponential backoff. On reconnect, it requests a fresh `GameStateSnapshot` from the host to catch up on missed actions.
**User actions:** Test on phone — toggle airplane mode, switch Wi-Fi ↔ mobile data, background the browser. Observe reconnection behavior.
**Checkpoint:** Ask if the user has questions.

---

### Phase 9 — Emoji Reactions & Advanced Features
**What:** Add floating emoji reactions, room capacity limits, room auto-cleanup, and typing indicators.
**Antigravity actions:**
- **Emoji Reactions:**
  - Add `emoji_reaction` message type to consumer
  - Add emoji button bar to `room.html` (🔥 😂 👀 👏 💀 ⏳)
  - CSS animation for floating emojis (rise from bottom, fade out)
  - Reactions are broadcast to room but NOT stored (ephemeral, like Tuko Kadi)

- **Room Capacity Limits:**
  - Add `MAX_USERS_PER_ROOM = 8` to consumer
  - On `connect()`, check current user count. If full, send error message and close connection with `self.close(code=4001)` (custom close code)
  - Frontend shows "Room is full" alert

- **Typing Indicators:**
  - Add `typing_start` / `typing_stop` message types
  - Frontend sends `typing_start` on keypress, `typing_stop` after 2s of inactivity (debounce)
  - Other users see "Brian is typing..." below the message area

- **Stale Room Cleanup:**
  - Track `last_activity` timestamp per room
  - Background task (Django management command or periodic consumer check) prunes rooms idle for 1+ hours
  - Explain why this matters (Redis memory, channel layer pollution)

- Create `Phase 9 - Emoji Reactions and Advanced Features.md` with:
  - **Multiple message types in one consumer** — the full type registry pattern:
    ```python
    MESSAGE_HANDLERS = {
        'chat_message': handle_chat,
        'emoji_reaction': handle_emoji,
        'typing_start': handle_typing,
        'set_username': handle_username,
    }
    ```
  - **Custom WebSocket close codes** (4000–4999 range, what each means)
  - **Debouncing** explained (typing indicator — don't send 60 events per second)
  - **CSS @keyframes animation** for floating emojis
  - Tuko Kadi mapping:
    - Emoji reactions → identical `emojiReaction` message type
    - Room capacity → `maxPlayers` (2–8)
    - Typing indicator → turn timer / "Player X is thinking..."
    - Stale cleanup → room pruning for abandoned games
**User actions:** Play with the features in browser.
**Checkpoint:** Ask if the user has questions.

---

### Phase 10 — Connecting from Flutter (Dart WebSocket Client)
**What:** Build a minimal Flutter screen that connects to the deployed chat server via WSS, proving Flutter can talk to our Django server.
**Antigravity actions:**
- Add `web_socket_channel` package to `pubspec.yaml` (the standard Flutter WebSocket package)
- Create `lib/screens/chat_test/chat_test_screen.dart` — a standalone screen with:
  - Room code text field
  - Username text field
  - Connect/Disconnect button
  - Message list (ListView)
  - Message input + send button
  - Connection status indicator
  - Emoji reaction buttons
- Use `WebSocketChannel.connect('wss://YOUR_DOMAIN.duckdns.org/ws/chat/ROOM/')` to connect
- Handle connection lifecycle in `StatefulWidget` (`initState`, `dispose`)
- Add a temporary route in the app to navigate to `ChatTestScreen` (debug-only)
- Create `Phase 10 - Connecting from Flutter.md` with:
  - **Dart `dart:io` WebSocket vs `web_socket_channel` package:**
    - `dart:io` — low-level, platform-specific, more control
    - `web_socket_channel` — high-level, stream-based, works on web+mobile
    - Why `web_socket_channel` is preferred (same API everywhere, integrates with Dart Streams)
  - **WebSocket connection in Dart — line by line:**
    ```dart
    final channel = WebSocketChannel.connect(Uri.parse('wss://...'));
    channel.stream.listen((message) { ... });
    channel.sink.add(jsonEncode({'type': 'chat_message', ...}));
    channel.sink.close();
    ```
  - **JSON encoding/decoding in Dart** (`dart:convert` — `jsonEncode()`, `jsonDecode()`)
  - **StreamSubscription lifecycle** — why you must cancel in `dispose()` (memory leaks)
  - **Cross-platform testing:** Chat between Flutter app (phone) and browser (laptop) in the same room — proves the server doesn't care who the client is
  - **Reconnection in Dart** — implementing the same exponential backoff from Phase 8 but in Dart
  - Tuko Kadi mapping: This is EXACTLY what `GameClient.connectOnline()` will do:
    - `WebSocketChannel.connect()` → `GameClient._socket`
    - `channel.stream.listen()` → `GameClient._onMessage()`
    - `channel.sink.add()` → `GameClient.sendAction()`
    - `channel.sink.close()` → `GameClient.disconnect()`
**User actions:** Run the Flutter app on a physical device, chat between phone (Flutter) and laptop (browser).
**Checkpoint:** Ask if the user has questions.

---

### Phase 11 — Review & Tuko Kadi Bridge
**What:** Review everything learned, map every concept to the Tuko Kadi relay server, and confirm readiness.
**Antigravity actions:**
- Create `Phase 11 - Review and Tuko Kadi Bridge.md` with:
  - **Complete concept mapping table** — every chat app concept → Tuko Kadi equivalent (expanded version of the table at the bottom of this document)
  - **Architecture comparison** — side-by-side Mermaid diagrams:
    - Chat app: Client → Server → broadcast to group (server knows content)
    - Tuko Kadi: Client → Server → relay to group (server is BLIND — just passes bytes)
  - **What's different in Tuko Kadi:**
    - Host-authority model (one client is "special" — the host runs the game engine)
    - The server NEVER inspects game messages — it's a dumb relay (unlike the chat app which parses message types)
    - Game state snapshots on reconnect (chat doesn't re-send history, Tuko Kadi does)
    - Turn-based flow (only one player acts at a time, enforced by the host)
    - Room codes are 6-char random strings, not user-chosen names
  - **What's identical:**
    - `group_add` / `group_send` / `group_discard`
    - Nginx + SSL + WSS
    - Daphne + Redis + systemd
    - Flutter WebSocket client
    - Reconnection with exponential backoff
    - Emoji reactions
    - Room capacity limits
  - **Confidence checklist:**
    - [ ] I understand what a WebSocket is and how it differs from HTTP
    - [ ] I can explain what Django Channels does
    - [ ] I understand the consumer lifecycle (connect → receive → disconnect)
    - [ ] I know what Redis does and why it's needed
    - [ ] I understand Channel Layer groups (add, send, discard)
    - [ ] I can deploy a Django Channels app to a Linux server with Nginx + SSL
    - [ ] I can connect to a WSS server from Flutter/Dart
    - [ ] I understand reconnection with exponential backoff
    - [ ] I'm ready to build the Tuko Kadi relay server
  - **Recommended next steps:** Return to the `implementation_plan.md` and begin the real Tuko Kadi relay
**User actions:** Review, check off the confidence items, confirm readiness.
**Checkpoint:** Final sign-off before transitioning to the real Tuko Kadi relay server.

---

## Security Notes (Antigravity Reference)

Apply these throughout the relevant phases:
- **`ALLOWED_HOSTS`**: Always set explicitly in `settings.py` for production (Phase 7). Prevents HTTP Host header attacks.
- **`SECRET_KEY`**: Fine to leave default for this learning project. For Tuko Kadi production, use environment variables.
- **`DEBUG = False`**: Always set in production (Phase 7). `DEBUG = True` leaks stack traces to attackers.
- **CSRF**: Not relevant for WebSocket connections (CSRF is an HTTP-form concern). Mention briefly in Phase 3.
- **CORS**: Not relevant — we're not making cross-origin HTTP requests. WebSocket connections don't use CORS.
- **Origin checking**: Django Channels can validate `Origin` headers on WebSocket upgrade. Mention in Phase 7 but don't enforce (our Flutter app sends a non-browser origin).
- **Rate limiting**: Not implemented in the chat app, but mention as a Tuko Kadi consideration in Phase 11.

---

## Concept Mapping Reference (Chat App → Tuko Kadi)

| Chat App Concept | Tuko Kadi Equivalent |
|---|---|
| Chat room (by name) | Game room (6-char code) |
| User joins room | Player joins lobby |
| User sends message | Player plays card / draws / declares Niko Kadi |
| Server broadcasts message to room | Host broadcasts `GameStateSnapshot` to all players |
| User list sidebar | Lobby player roster (2–8 players) |
| Join/leave notifications | `playerJoined` / `playerLeft` events |
| `set_username` first message | `registerPlayer` message |
| Emoji reactions | Floating `🔥 😂 👀 👏 💀 ⏳` reactions on game table |
| Typing indicator | Turn timer / "Player X is thinking..." |
| Room capacity limit | `maxPlayers` (2–8) |
| Auto-reconnect with backoff | `GameClient` reconnection with exponential backoff |
| Ping/pong heartbeat | `_socket.pingInterval = Duration(seconds: 10)` |
| Room auto-cleanup | Stale room pruning after 1 hour idle |
| Django consumer | `GameRelayConsumer` |
| `self.send()` | Send to one specific player |
| `group_send()` | Broadcast to all players in the game |
| Redis channel layer | Same Redis channel layer |
| Nginx WSS proxy | Same Nginx WSS proxy |
| Daphne ASGI server | Same Daphne ASGI server |
| systemd service | Same `tuko-relay.service` |
| `web_socket_channel` (Flutter) | `GameClient.connectOnline()` |
| `collectstatic` + Nginx `/static/` | Same static file serving |
| `scp` code transfer | Same deployment method |
| `journalctl -u chat-app -f` | `journalctl -u tuko-relay -f` |
