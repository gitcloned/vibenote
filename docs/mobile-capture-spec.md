# Vibenote Mobile Capture — Product Spec

> Local-first for knowledge, cloud-only for transit. Your vault never leaves your machine. Captures pass through the relay like a letter through the postal system — the post office handles the envelope, not the contents of your thinking.

---

## 1. The problem

You're in a conversation on WhatsApp. Someone drops a link about GRPO training for small models. You know it connects to two threads of research you've been building in Vibenote. But you're on your phone, walking, not in front of your laptop. By the time you sit down, the link is buried in the chat and the thought that connected it to your research is gone.

This happens five times a day. On the bus reading Twitter. In a meeting when someone says something that connects to your open questions. Watching a YouTube video before bed. Talking to a friend who mentions a paper you should read. The thinking happens everywhere. The capture tool is on your laptop.

Vibenote's vault is local-first — threads, structured notes, concepts, all live on your machine. That's a feature, not a bug. But the capture surface needs to be everywhere, because thinking doesn't wait for you to open your laptop.

## 2. Story: Ashish on the bus

Ashish is riding the bus home. He opens WhatsApp and sees a message from a colleague: a link to a new paper about using DPO to fine-tune small models for conversational tutoring. He knows this connects to both his SLM optimization research and his AI education thread — it's exactly the intersection his concept pages identified.

He long-presses the message. Taps share. Picks "Vibenote" from the share sheet. The Vibenote capture screen opens with the link pre-filled. He types: "DPO for tutoring — the paper we've been waiting for. Connects to both research threads." Taps Capture. A green checkmark. Back to WhatsApp. Five seconds.

He doesn't know or care that the capture went through a relay server. He doesn't know or care that his laptop is asleep in his bag. What he knows: the thought is captured, it'll be classified into the right thread(s) when his laptop wakes up, and the next time he asks "what should I work on next?" this paper will be in the answer.

Later that evening, he opens his laptop. Vibenote's poller has already drained the relay — his capture is in the vault, classified into both `slm-optimization-research` and `ai-education-research`. When he processes his threads, the concept pages update. The connection he noticed on the bus is now permanent knowledge.

## 3. Design principles (mobile-specific)

These extend the core Vibenote principles from the web product spec.

**1. Capture must be faster than forgetting.** If it takes more than 5 seconds to go from "I want to save this" to "it's saved," the habit dies. Every tap counts. The share sheet is the ideal entry point because it's already where the user is — zero context switches.

**2. The phone is a capture device, not a knowledge device.** Mobile capture is high-frequency, low-depth. The phone sends raw material into the vault. Synthesis, processing, querying, concept extraction — that happens on the laptop where Claude runs. Don't try to replicate the full Vibenote experience on mobile. Capture fast, think later.

**3. No accounts, no sign-ups, no third-party services in the default path.** The QR code IS the setup. Scan it, capture works. No Tailscale, no Cloudflare account, no OAuth. Power users can add direct connectivity later. The default path has zero friction.

**4. Offline-tolerant, not offline-first.** The phone doesn't need to reach the laptop in real time. Captures queue (in the relay or in the PWA's local storage) and sync when connectivity exists. The user should never see "cannot connect" — just "captured, will sync."

**5. Local-first for knowledge, cloud-only for transit.** The relay is a dumb pipe. It holds raw captures for up to 24 hours, then they're on the laptop and nowhere else. The relay never sees structured notes, concepts, or synthesis. Users who want zero transit can use Tailscale for direct phone→laptop capture.

## 4. Architecture

### Three tiers of connectivity

Users choose their tier. The product works at all three. Higher tiers unlock more features.

| Tier | How it works | Setup friction | Features |
|---|---|---|---|
| **Relay (default)** | Phone → cloud relay → laptop polls | Scan QR code (10 seconds) | Capture only. Works when laptop is off. |
| **Direct (Tailscale)** | Phone → laptop via VPN | Install Tailscale on both devices (5 min) | Capture + query + browse. Real-time. |
| **Air-gapped** | Laptop only, no mobile | Zero | Claude Code + Chrome extension only. Maximum privacy. |

New users start at Relay. Power users upgrade to Direct when they want mobile query/browse. Privacy-maximalists stay Air-gapped.

### Relay architecture

```
┌────────────────┐       ┌─────────────────────┐       ┌──────────────────┐
│ User's phone   │       │ Vibenote Relay       │       │ User's laptop    │
│                │       │ (Cloudflare Worker)  │       │                  │
│ PWA / Shortcut │       │                      │       │ vibenote-server  │
│                │ HTTPS │ POST /capture/<token> │ HTTPS │ GET /captures    │
│ Share from any │──────→│ → KV queue (TTL 24h) │←──────│ → import to vault│
│ app on phone   │       │                      │ poll  │ → classify       │
│                │       │ GET /captures/<token> │ 30s   │ → file to thread │
│                │←──────│ → return + delete     │       │                  │
│ "✓ Captured"   │  200  │                      │       │ ~/.vibenote/     │
└────────────────┘       └─────────────────────┘       └──────────────────┘
```

**Per-user isolation:** Each user gets a unique 32-character token at install time. Tokens are the only "identity" — no usernames, no passwords, no sessions. One token = one user's queue. Tokens can't be guessed (256-bit random).

**Data lifecycle:**
1. Phone POSTs capture to relay (HTTPS, encrypted in transit)
2. Relay stores in Cloudflare KV with TTL=24 hours
3. Laptop polls every 30 seconds, picks up pending captures
4. Relay deletes picked-up captures immediately
5. Unpicked captures auto-expire after 24 hours (Cloudflare KV TTL)

**What the relay stores:** Raw text only. The POST body: `{content, title?, url?, timestamp}`. No thread classification, no structured notes, no concepts, no vault content. The relay has no idea what Vibenote is — it's a generic message queue.

**What the relay NEVER sees:** Thread content, structured notes, concept pages, user queries, vault structure, processing output. All of that stays on the laptop.

### Direct architecture (Tailscale upgrade)

```
┌────────────────┐                           ┌──────────────────┐
│ User's phone   │    WireGuard tunnel       │ User's laptop    │
│                │    (E2E encrypted)         │                  │
│ PWA            │◄─────────────────────────► │ vibenote-server  │
│                │                            │ (:3137)          │
│ Full features: │  POST /api/capture         │                  │
│ - Capture      │  POST /api/ask             │ ~/.vibenote/     │
│ - Query        │  GET  /api/threads         │                  │
│ - Browse       │  GET  /api/concepts        │                  │
│ - Chat Q&A     │  GET  /                    │                  │
└────────────────┘                            └──────────────────┘
```

Same PWA, same API. The only difference: the PWA talks to `https://laptop.tailnet.ts.net:3137` instead of `https://capture.vibenote.dev`. More features unlock because the laptop is directly reachable (query, browse, chat Q&A — not just capture).

## 5. The relay service

### API (three endpoints)

```
POST /capture/<token>
  Body: {
    content: string,       // the captured text (required)
    title: string?,        // page title or source name
    url: string?,          // source URL
    timestamp: string?     // ISO 8601, defaults to now
  }
  Response: 200 {ok: true, queued: true}
  Errors: 400 (empty content), 429 (rate limit)

GET /captures/<token>
  Response: 200 {
    captures: [
      {content, title, url, timestamp, id},
      ...
    ]
  }
  Side effect: deletes returned captures from the queue
  Called by: the laptop poller only

GET /health
  Response: 200 {ok: true}
```

### Implementation: Cloudflare Worker + KV

~80 lines of JavaScript. Runs on Cloudflare's edge (free tier: 100K requests/day, more than enough for thousands of users).

```javascript
// Pseudocode — the actual Worker
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'POST' && url.pathname.startsWith('/capture/')) {
      const token = url.pathname.split('/')[2];
      const body = await request.json();
      if (!body.content?.trim()) return json({error: 'empty content'}, 400);

      // Queue in KV: key = token:timestamp, value = capture, TTL = 24h
      const id = crypto.randomUUID();
      await env.CAPTURES.put(
        `${token}:${id}`,
        JSON.stringify({...body, id, timestamp: body.timestamp || new Date().toISOString()}),
        {expirationTtl: 86400}
      );
      return json({ok: true, queued: true});
    }

    if (request.method === 'GET' && url.pathname.startsWith('/captures/')) {
      const token = url.pathname.split('/')[2];
      const list = await env.CAPTURES.list({prefix: `${token}:`});
      const captures = [];
      for (const key of list.keys) {
        const val = await env.CAPTURES.get(key.name);
        if (val) {
          captures.push(JSON.parse(val));
          await env.CAPTURES.delete(key.name);  // delete after read
        }
      }
      return json({captures});
    }

    return json({ok: true});  // health
  }
};
```

### Rate limiting

- Per-token: max 100 captures/hour (prevents abuse if a token leaks)
- Global: Cloudflare's built-in DDoS protection
- No auth beyond the token itself (tokens are 256-bit random — unguessable)

### Cost

Cloudflare Workers free tier:
- 100,000 requests/day
- 1 GB KV storage
- At 10 captures/user/day, this supports ~10,000 users for free
- Paid tier ($5/mo) supports millions

### Security properties

| Property | How it's achieved |
|---|---|
| **User isolation** | Unique 32-char token per user. KV keys are prefixed by token. No cross-user access. |
| **No accounts** | Token IS the identity. Generated at install, stored in config.json. |
| **Encryption in transit** | HTTPS (TLS 1.3) between phone → relay and relay → laptop. |
| **Ephemeral storage** | Captures deleted after laptop picks up, or auto-expire at 24h (KV TTL). |
| **No vault access** | Relay only sees raw capture text. Never sees threads, concepts, structured notes, or queries. |
| **Token rotation** | User can regenerate token via `vibenote-server --rotate-token`. Old token immediately invalid. |
| **Abuse protection** | Rate limiting per token. Leaked token can be rotated. No PII in captures (user's choice what to capture). |

## 6. The mobile PWA

### What it is

A Progressive Web App — a web page that's installable to the home screen and registers as a share target. Works on iOS (Safari) and Android (Chrome). No App Store, no native code, no build toolchain.

### Screens

**Screen 1: Capture (primary — the share target)**

```
┌──────────────────────────────────┐
│  Vibenote                    ✕   │
├──────────────────────────────────┤
│                                  │
│  DPO for tutoring — the paper    │ ← shared URL/text pre-filled
│  we've been waiting for.         │
│  Connects to both research       │
│  threads.                        │
│                                  │
│  https://arxiv.org/abs/...       │ ← source URL (if shared)
│                                  │
│  ┌──────────────────────────────┐│
│  │ Add a thought...             ││ ← optional comment
│  └──────────────────────────────┘│
│                                  │
│       [ Capture ]                │
│                                  │
│  ✓ Queued — will sync when       │
│    your laptop is online         │
└──────────────────────────────────┘
```

**Screen 2: Recent captures (secondary)**

```
┌──────────────────────────────────┐
│  Vibenote              [Capture] │
├──────────────────────────────────┤
│                                  │
│  Today                           │
│  ┌──────────────────────────────┐│
│  │ DPO for tutoring...          ││
│  │ arxiv.org · 2 min ago · ✓   ││
│  └──────────────────────────────┘│
│  ┌──────────────────────────────┐│
│  │ Registered on Toptal         ││
│  │ 3 hours ago · ✓ synced      ││
│  └──────────────────────────────┘│
│                                  │
│  Yesterday                       │
│  ┌──────────────────────────────┐│
│  │ Voice UX design patterns...  ││
│  │ youtube.com · ✓ synced       ││
│  └──────────────────────────────┘│
│                                  │
│  ● 3 captures synced today      │
│  ● 0 pending                    │
└──────────────────────────────────┘
```

### Share sheet integration

**Android (Web Share Target API):**
The PWA's `manifest.json` includes:
```json
{
  "share_target": {
    "action": "/capture",
    "method": "POST",
    "enctype": "multipart/form-data",
    "params": {
      "title": "title",
      "text": "text",
      "url": "url"
    }
  }
}
```

When the user shares from any Android app → Vibenote appears in the share sheet → content is pre-filled.

**iOS (limited Web Share Target support):**
iOS Safari's share sheet integration for PWAs is more limited. Fallback options:
- **iOS Shortcut** — "Share to Vibenote" shortcut that POSTs to the relay. Appears in the share sheet.
- **"Copy + open Vibenote"** — user copies text, opens the PWA, pastes. More steps but always works.

The PWA detects the platform and guides the user to the right setup.

### Offline support

The PWA uses a Service Worker to work offline:
1. User captures when offline (or laptop unreachable)
2. Capture saved to IndexedDB locally
3. Service Worker retries POST to relay every 60 seconds
4. When relay is reachable, captures sync and local copies are marked "synced"
5. The "Recent captures" screen shows sync status per capture

The user never sees "connection failed." They see "queued — will sync."

### PWA technical stack

- Plain HTML/CSS/JS (no framework — same philosophy as the Chrome extension)
- Service Worker for offline + background sync
- IndexedDB for local capture queue
- Web Share Target API for Android share sheet
- `manifest.json` for installability (home screen icon, standalone display)
- Total bundle: <50 KB

Hosted on Cloudflare Pages (free, global CDN, instant deploys from git).

## 7. The laptop poller

A background process on the user's laptop that drains the relay queue.

### How it runs

Part of `vibenote-server`. When the server starts, it spawns a polling loop:

```python
async def poll_relay():
    token = load_config()["relay_token"]
    relay_url = f"https://capture.vibenote.dev/captures/{token}"

    while True:
        try:
            response = httpx.get(relay_url)
            captures = response.json().get("captures", [])
            for capture in captures:
                handle_capture({
                    "content": capture["content"],
                    "title": capture.get("title", ""),
                    "url": capture.get("url", ""),
                })
            if captures:
                log(f"Imported {len(captures)} captures from relay")
        except Exception as e:
            log(f"Relay poll failed: {e}")

        await asyncio.sleep(30)  # poll every 30 seconds
```

Uses the existing `handle_capture` function from the bridge — same LLM classification, same multi-thread filing, same vault operations.

### When the laptop wakes up

If the laptop was asleep for hours, the first poll picks up ALL queued captures in one batch. They're classified and filed in order. The user opens their laptop and everything is already there.

## 8. Onboarding flow

### For the install script

The installer gains one new section after the existing setup:

```
Installing MCP server
  ✓ MCP server installed
  ✓ Added 'vibenote' to Claude Desktop MCP config

Mobile capture (optional)
  ✓ Generated capture token
  ✓ Relay poller configured

  Scan this QR code with your phone to enable mobile capture:

    ████████████████████████
    ████████████████████████
    ████████████████████████

  Or open: https://capture.vibenote.dev/setup#vn_a7f2...

  Your captures are end-to-end encrypted in transit and deleted
  from the relay after your laptop picks them up (max 24 hours).
```

The QR code encodes the setup URL with the token. The phone opens this URL → the PWA loads → pre-configured → "Add to Home Screen" prompt → done.

### For the PWA setup page

```
┌──────────────────────────────────┐
│  Welcome to Vibenote             │
├──────────────────────────────────┤
│                                  │
│  Your capture token is linked.   │
│                                  │
│  [ Add to Home Screen ]          │
│                                  │
│  Then share anything from        │
│  WhatsApp, YouTube, Twitter,     │
│  Safari — Vibenote will capture  │
│  it and sync to your laptop.     │
│                                  │
│  Your vault stays on YOUR        │
│  machine. Captures pass through  │
│  our relay briefly (encrypted,   │
│  deleted after sync).            │
│                                  │
│  For zero-cloud capture:         │
│  → Set up Tailscale (guide)      │
└──────────────────────────────────┘
```

## 9. Token management

### Generation

`install.sh` generates a token:
```bash
TOKEN="vn_$(openssl rand -hex 16)"
# → vn_a7f29c3d8e1b4f6a2d5e8c9b3f7a1d4e
```

Stored in `~/.vibenote/config.json`:
```json
{
  "relay_token": "vn_a7f29c3d8e1b4f6a2d5e8c9b3f7a1d4e",
  "relay_url": "https://capture.vibenote.dev"
}
```

### Rotation

If a token is compromised (phone lost, token accidentally shared):
```bash
vibenote-server --rotate-token
```

This:
1. Generates a new token
2. Updates config.json
3. Shows a new QR code
4. Old token is immediately invalid (relay rejects it)
5. User re-scans QR on their phone

### Revocation

```bash
vibenote-server --revoke-token
```

Deletes the token from config. Mobile capture stops working. Relay queue for the old token expires naturally (24h TTL).

## 10. Security model

### Threat analysis

| Threat | Mitigation |
|---|---|
| **Someone guesses a token** | 128-bit random (32 hex chars). Probability of collision: ~1 in 3.4 × 10^38. |
| **Token leaked (phone lost)** | Rotate token. Old token immediately invalid. Pending captures in relay expire in 24h. |
| **Relay operator reads captures** | Captures are raw text — user chooses what to share. The relay never sees the vault, synthesis, or queries. Accept this tradeoff or use Tailscale (zero-cloud tier). |
| **MITM attack on relay** | HTTPS (TLS 1.3) for all relay traffic. Certificate pinning in the PWA for extra assurance. |
| **Replay attack** | Each capture has a unique UUID. The poller deduplicates by ID. |
| **DDoS on relay** | Cloudflare's built-in DDoS protection. Per-token rate limiting (100/hour). |
| **Cross-user data access** | KV keys are prefixed by token. No API endpoint lists tokens or accesses other users' queues. |

### What the relay knows about a user

- A random token (no email, no name, no device ID)
- Timestamps of captures
- Raw capture text (ephemeral, deleted after pickup)
- IP addresses of POST and GET requests (standard HTTP, logged by Cloudflare)

### What the relay does NOT know

- Who the user is
- What threads exist in their vault
- What concepts connect their threads
- What their structured notes say
- What queries they've asked
- What their laptop's hostname or IP is (the laptop POLLs the relay — outbound only)

### Privacy tiers (user's choice)

| Tier | What transits cloud | Setup effort | Best for |
|---|---|---|---|
| **Air-gapped** | Nothing | None | Maximum privacy |
| **Relay (default)** | Raw capture text only, ephemeral | Scan QR (10s) | Most users |
| **Direct (Tailscale)** | Nothing (E2E encrypted) | Install Tailscale (5 min) | Power users who want mobile query |

## 11. What gets built, in order

### Phase 1: Foundation (required for all mobile paths)

- [ ] **HTTP server mode** (`vibenote-server --serve`) — the `/api/capture`, `/api/threads`, `/api/health` endpoints on localhost:3137. Already specced in `docs/web-product-spec.md`. ~150 lines of Python.
- [ ] **`vibenote-server` command** — start/stop/status of the HTTP server. PID file management. ~60 lines of bash.

### Phase 2: Relay

- [ ] **Cloudflare Worker** — the relay service. POST captures, GET captures, health check. ~80 lines of JS.
- [ ] **Deploy to Cloudflare** — create KV namespace, deploy Worker, configure `capture.vibenote.dev` domain.
- [ ] **Laptop poller** — background thread in vibenote-server that polls the relay every 30s and imports captures. ~50 lines of Python.
- [ ] **Token generation in install.sh** — generate token, store in config, print QR code. ~20 lines of bash.

### Phase 3: Mobile PWA

- [ ] **PWA scaffold** — HTML/CSS/JS, manifest.json, service worker. Capture screen + recent captures screen.
- [ ] **Share target** — Web Share Target API for Android. iOS Shortcut fallback.
- [ ] **Offline queue** — IndexedDB storage, background sync via Service Worker.
- [ ] **Setup page** — token linking via QR code URL, "Add to Home Screen" prompt.
- [ ] **Host on Cloudflare Pages** — deploy from the repo, global CDN.

### Phase 4: Direct connectivity (Tailscale tier)

- [ ] **Tailscale setup guide** — docs for users who want direct phone→laptop access.
- [ ] **PWA direct mode** — detect Tailscale connectivity, switch from relay to direct API calls. Unlock query/browse/chat on mobile.

### Phase 5: Polish

- [ ] **Token rotation UI** in vibenote-server
- [ ] **Sync status** in the PWA (pending/synced/failed per capture)
- [ ] **Push notification** when laptop imports a capture (optional, via Web Push)
- [ ] **Voice capture** — record audio in PWA, send to relay, laptop transcribes via Whisper

## 12. What NOT to build

- ❌ Native iOS/Android app (PWA covers 90% of the value, App Store review adds weeks)
- ❌ User accounts on the relay (tokens are sufficient — no email, no password, no OAuth)
- ❌ Vault sync to mobile (conflict resolution is hell, the phone doesn't need the full vault)
- ❌ Mobile processing/concept extraction (requires Claude CLI, which is laptop-only)
- ❌ Mobile editing of threads (editing on phone keyboards is miserable, do it on laptop)
- ❌ Real-time WebSocket push from relay to laptop (polling every 30s is simple and good enough)
- ❌ E2E encryption on relay (HTTPS is sufficient for ephemeral text transit; full E2E adds key management complexity that isn't worth it for <24h ephemeral storage)

## 13. Success metrics

After 2 weeks of mobile capture being live:

| Metric | Signal |
|---|---|
| **Captures from mobile / total captures** | >20% = mobile is a real capture surface |
| **Time from share to captured (on phone)** | <5 seconds = the habit will form |
| **Relay queue depth** | Usually 0 (laptop picks up quickly). Occasionally >0 (laptop was off). Never >50 (something's broken). |
| **Mobile capture → thread accuracy** | >80% filed correctly on first classification |
| **Return rate** | User captures from mobile >3 days/week = habit formed |
| **QR scan → first capture** | <2 minutes = onboarding works |

---

**Status:** Spec complete. Build sequence defined. Depends on HTTP server mode (Phase 1) which is also the foundation for the web product spec.
