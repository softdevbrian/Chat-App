# Phase 5: Building the Chat Frontend (Vue 3 via CDN)

---

## 1. What We Just Built (Plain English Summary)

In Phases 3 and 4, we built and tested our real-time WebSocket backend using browser developer tools and automated Python test scripts.

In Phase 5, we replaced the raw developer console with a **sleek, fully responsive, modern web interface** powered by **Vue 3 (Composition API) loaded directly via CDN**:
1. **Lobby Landing Page (`chat/templates/chat/index.html`):** A clean landing card where users choose their handle, enter a room name, and click "Join Room". Form validation prevents empty or invalid room names and remembers previously used handles via `sessionStorage`.
2. **Chat Room Interface (`chat/templates/chat/room.html`):**
   - **Reactive Vue 3 Composition API:** Uses `ref`, `computed`, `onMounted`, `onBeforeUnmount`, and `nextTick` to manage real-time UI state without manual DOM queries (`document.getElementById`).
   - **Live Connection Status Badge:** Dynamic pulsating badge reflecting `Connecting...` (Yellow), `Connected` (Green), or `Disconnected` (Red).
   - **Modern Chat Bubble Layout:** My outgoing messages align to the right in an accent gradient; incoming messages from peers align to the left with their username label; system events (greetings and notifications) appear centered.
   - **Smooth Auto-Scroll:** The message container automatically scrolls to the newest message whenever a message arrives.
   - **Keyboard Interaction:** Hitting `Enter` immediately dispatches the message and refocuses the input box.
3. **Dedicated Stylesheet (`chat/static/chat/style.css`):** Built with custom CSS design tokens (CSS variables), glassmorphism header, responsive flex layouts, and custom scrollbars.
4. **Django HTTP Views & URL Routing:** Connected `/` (lobby) and `/chat/<room_name>/` (room).
5. **Automated View Tests (`chat/tests.py`):** Added tests verifying HTTP status `200` and template rendering for both views, passing alongside our WebSocket tests in **0.129s**.

---

## 2. Commands Executed and What Each Did (In Order)

Here is the exact sequence of commands and operations carried out in this phase:

### Step 1: Create `chat/views.py`
We defined `index(request)` (renders `chat/index.html`) and `room(request, room_name)` (renders `chat/room.html` passing `room_name` context).
- **What it did:** Implemented the HTTP view functions that serve our HTML templates.

### Step 2: Configure URL Routing (`chat/urls.py` and `chat_project/urls.py`)
We created `chat/urls.py` with routes for `''` and `'chat/<str:room_name>/'`, and mounted it in `chat_project/urls.py` under `include('chat.urls')`.
- **What it did:** Made the lobby accessible at `http://127.0.0.1:8000/` and rooms accessible at `http://127.0.0.1:8000/chat/<room>/`.

### Step 3: Create Modern CSS Stylesheet (`chat/static/chat/style.css`)
We wrote responsive CSS with dark-mode slate tones, message alignment classes (`.outgoing`, `.incoming`, `.message-system`), and status indicator animations.
- **What it did:** Provided styling for both the lobby and chat room views.

### Step 4: Create Lobby Template (`chat/templates/chat/index.html`)
We constructed the lobby interface with Vue 3 CDN, `v-model` form inputs, validation, and redirection to the room route.
- **What it did:** Created the entry portal where users pick their handle and room.

### Step 5: Create Chat Room Template (`chat/templates/chat/room.html`)
We built the reactive chat room interface with Vue 3, integrating the native JavaScript `WebSocket` client with Vue's reactive state and `{% verbatim %}` blocks.
- **What it did:** Delivered the full visual multi-user chat room experience.

### Step 6: Expand Automated Test Suite in `chat/tests.py`
We added `ChatViewTests` verifying that `reverse('chat:index')` and `reverse('chat:room', args=['lounge'])` return HTTP status `200` and use the expected templates.
- **What it did:** Ensured automated verification covering both HTTP page delivery and WebSocket communication.

### Step 7: Run Automated Unit Tests
```powershell
.\venv\Scripts\python.exe manage.py test
```
- **What it did:** Executed all 3 test cases (lobby view, room view, and room group WebSocket isolation).
- **Result:** `Ran 3 tests in 0.129s — OK`.

### Step 8: Validate System Configuration Health
```powershell
.\venv\Scripts\python.exe manage.py check
```
- **What it did:** Verified that URL routing, views, static file configs, and templates have zero errors.
- **Result:** `System check identified no issues (0 silenced)`.

---

## 3. Key Concepts Explained for Beginners

### Django Templates and Static Files
In Django:
- **Templates (`templates/`):** Dynamic HTML files rendered on the server. Django inspects template tags like `{% url %}`, `{% load static %}`, and context variables like `{{ room_name }}` before sending the HTML to the browser.
- **Static Files (`static/`):** Assets that do not change dynamically on the server (CSS stylesheets, images, client-side JavaScript). They are referenced via `{% load static %}` and `{% static 'chat/style.css' %}`.

### Solving the Django vs. Vue Template Syntax Collision (`{% verbatim %}`)
Both Django and Vue use double curly braces `{{ }}` for variable interpolation:
- Django wants `{{ room_name }}` to be evaluated by Python on the server.
- Vue wants `{{ message.text }}` to be evaluated by JavaScript in the browser.

If Django sees `{{ message.text }}`, it will search Python context for a variable called `message`, find nothing, and render a blank empty space!

**The Clean Solution: `{% verbatim %}`**
Django provides a built-in template tag called `{% verbatim %}`. Anything placed inside a `{% verbatim %}` block is ignored by Django's template parser and sent raw to the browser, allowing Vue to evaluate its reactive properties without collision:
```html
<!-- Handled by Django on the server -->
<h2># {{ room_name }}</h2>

<!-- Handled by Vue in the browser -->
{% verbatim %}
<span>Chatting as: {{ username }}</span>
<div v-for="msg in messages">{{ msg.message }}</div>
{% endverbatim %}
```

---

### Vue 3 Composition API via CDN (Zero Build Tooling)

We loaded Vue 3 using a standard script tag:
```html
<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
```

Instead of requiring Node.js, `npm`, Vite, or complex bundlers, we import Vue's modern Composition API functions directly:
```javascript
const { createApp, ref, computed, onMounted, onBeforeUnmount, nextTick } = Vue;
```

#### Core Vue Concepts Used:
1. **`ref()` (Reactive State):**
   ```javascript
   const messages = ref([]);
   const newMessage = ref('');
   ```
   Wrapping a value in `ref()` tells Vue to watch it. When `messages.value.push(data)` is called, Vue automatically updates the DOM without needing manual `document.createElement()` or `appendChild()` calls.
2. **`v-model` (Two-Way Binding):**
   ```html
   <input v-model="newMessage">
   ```
   Synchronizes the input box with our JavaScript `newMessage` variable in real time.
3. **`v-for` (List Rendering):**
   ```html
   <template v-for="(msg, index) in messages" :key="index">
   ```
   Renders a message bubble for each object in the `messages` array.
4. **`computed()` (Derived State):**
   ```javascript
   const statusText = computed(() => {
       return connectionStatus.value === 'connected' ? 'Connected' : 'Connecting...';
   });
   ```
   Automatically recalculates whenever `connectionStatus` changes.
5. **`nextTick()` (DOM Synchronization):**
   When a new message arrives, Vue takes a few milliseconds to render the new HTML element into the page. Calling `await nextTick()` ensures the DOM has updated before we calculate `messagesContainer.scrollTop = messagesContainer.scrollHeight` to auto-scroll to the bottom.

---

### Dynamic WebSocket Scheme (`ws://` vs `wss://`)
In `room.html`, notice how we construct the WebSocket URL:
```javascript
const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const wsUrl = `${wsScheme}${window.location.host}/ws/chat/${encodeURIComponent(roomName)}/`;
```
- When running locally on `http://127.0.0.1:8000/`, it connects to `ws://127.0.0.1:8000/...`.
- When deployed in production on `https://yourdomain.duckdns.org/`, it **automatically switches** to `wss://yourdomain.duckdns.org/...` with zero code changes required!

---

## 4. How This Maps to Tuko Kadi (Browser Vue $\longleftrightarrow$ Flutter Dart)

Notice how the frontend architecture we just built in Vue maps directly to Flutter and Dart:

| Concept | Vue 3 Chat Frontend | Tuko Kadi Flutter Client |
|---|---|---|
| **Lobby Screen** | `index.html` (Username & Room input) | `LobbyScreen` (Player handle & Match code input) |
| **Active Room** | `room.html` (Chat stream & controls) | `GameTableScreen` (Card table, hand, discard pile) |
| **Reactive State** | `ref(messages)` | `List<GameAction> actions` inside `StatefulWidget` / `ChangeNotifier` |
| **Input Binding** | `v-model="newMessage"` | `TextEditingController` |
| **List Rendering** | `v-for="msg in messages"` | `ListView.builder(itemBuilder: ...)` |
| **Lifecycle Setup** | `onMounted(() => connect())` | `initState() => socket.connect()` |
| **Lifecycle Cleanup** | `onBeforeUnmount(() => socket.close())` | `dispose() => socket.sink.close()` |
| **Auto-Scroll** | `nextTick() + scrollTop` | `ScrollController.animateTo(...)` |

---

## 5. How to Test the New Web Interface Live

You can now use the full visual application directly in your browser:

### Step 1: Start the Server
In your PowerShell terminal:
```powershell
.\venv\Scripts\python.exe manage.py runserver
```

### Step 2: Open the Lobby
1. Open Google Chrome and visit:
   ```text
   http://127.0.0.1:8000/
   ```
2. You will see the **Tuko Chat Lobby**.
3. Enter your username (e.g. `Brian`) and room name (e.g. `lounge`).
4. Click **Join Room $\rightarrow$**.

### Step 3: Test Real-Time Multi-User Chat
1. Open a second browser tab (or Incognito window).
2. Visit `http://127.0.0.1:8000/` and join room `lounge` as `Alex`.
3. Type a message in Brian's tab and press **Enter**.
4. **Watch it appear instantly in both tabs**:
   - Brian's tab shows the message on the **right** in blue/purple.
   - Alex's tab shows the message on the **left** with Brian's name badge.
5. Notice the green **Connected** status indicator in the top right header!

---

## 6. Common Mistakes & Debugging Tips

1. **Django template syntax errors with Vue:**
   - **Error:** Vue expressions like `{{ msg.message }}` disappear or fail to render.
   - **Fix:** Wrap Vue HTML blocks inside `{% verbatim %} ... {% endverbatim %}` so Django doesn't consume the curly braces.
2. **Missing `APP_DIRS: True` in `settings.py`:**
   - **Error:** `TemplateDoesNotExist: chat/index.html`.
   - **Fix:** Ensure `TEMPLATES` in `settings.py` has `'APP_DIRS': True`, which directs Django to look inside each app's `templates/` directory.
3. **Hardcoding `ws://` instead of dynamic scheme:**
   - If you hardcode `new WebSocket('ws://...')`, the app will break once deployed to HTTPS/WSS in Phase 7 because browsers block unencrypted WebSockets on secure pages. Always use `window.location.protocol === 'https:' ? 'wss://' : 'ws://'`.

---

## 7. Glossary

- **Composition API:** Vue 3's function-based API (`ref`, `computed`, `onMounted`) organizing code cleanly by logical concerns.
- **Two-Way Data Binding (`v-model`):** Keeps an HTML input element and a JavaScript state variable automatically synchronized in both directions.
- **`nextTick`:** A Vue utility that defers execution until the next DOM update cycle has finished.
- **Glassmorphism:** A modern UI design trend featuring translucent frosted glass backgrounds (`backdrop-filter: blur()`).
- **CDN (Content Delivery Network):** A geographically distributed network of proxy servers delivering web assets (like Vue 3) fast and without local installations.
