# Smart Rural AI Advisor — Session, Authentication & TTL Reference

> **Owner:** Manoj RS  
> **Last Updated:** 2026-03-04  
> **Scope:** Complete reference for every timeout, TTL, session limit, and authentication setting across the full stack.

---

## 1. Authentication — AWS Cognito

| Setting | Value |
|---|---|
| **User Pool** | `smart-rural-ai-farmers` (`ap-south-1_X58lNMEcn`) |
| **App Client** | `4c3c6he88im15hmv5rdkv3m6h0` |
| **ID Token validity** | **1 hour** |
| **Access Token validity** | **1 hour** |
| **Refresh Token validity** | **30 days** |
| **Auth flows** | `USER_PASSWORD_AUTH`, `USER_SRP_AUTH`, `REFRESH_TOKEN_AUTH` |
| **Password policy** | Minimum 6 characters, no complexity requirements |
| **Unused account validity** | 7 days |

### Auth Flow

```
User enters phone + password
      ↓
cognitoAuth.signIn()  →  Cognito USER_SRP_AUTH
      ↓
Returns: idToken (1h), accessToken (1h), refreshToken (30d)
      ↓
FarmerContext stores login state + localStorage keys:
  farmer_id, farmer_phone, farmer_name, last_activity
      ↓
Every API call:
  apiFetch() → getIdToken() → Authorization: Bearer <idToken>
      ↓
Token expired? Cognito SDK auto-refreshes using refreshToken (silent, no user action)
      ↓
Refresh token expired (30d)? → Full re-login required
```

### Key Files

| File | Purpose |
|---|---|
| `frontend/src/services/cognitoAuth.js` | All Cognito operations: signUp, signIn, getSession, getIdToken, signOut, forgotPassword, changePassword, deleteUser |
| `frontend/src/contexts/FarmerContext.jsx` | Auth state management, session restore, idle timeout, activity tracking |
| `frontend/src/utils/apiFetch.js` | JWT auto-attachment to every API request |

---

## 2. Frontend Session Timeouts

| Mechanism | Value | Implementation |
|---|---|---|
| **Idle timeout** | **30 minutes** | `IDLE_TIMEOUT_MS = 30 * 60 * 1000` in `FarmerContext.jsx` |
| **Cognito session check** | Every **5 minutes** | `SESSION_CHECK_MS = 5 * 60 * 1000` in `FarmerContext.jsx` |
| **Activity tracking** | mousedown, keydown, touchstart, scroll, mousemove | Throttled to once per 30 seconds to avoid performance impact |
| **Tab-reopen detection** | Checks `last_activity` in localStorage | If > 30 min stale on page load → auto-logout |
| **Session restore timeout** | **3 seconds** | Race timeout prevents white screen if Cognito is slow/offline |

### Idle Timeout Flow

```
User active → last_activity updated in localStorage (throttled every 30s)
      ↓
setInterval every 60s checks: (now - last_activity) > 30 min?
  YES → auto-logout, redirect to login
  NO  → continue
      ↓
Separately, every 5 min: validate Cognito session still valid
  Invalid → auto-logout
  Valid   → continue
```

---

## 3. Chat Session Storage & Retrieval

### Dual-Sync Architecture

The chat system uses **two storage layers** that sync on every page load:

```
┌──────────────┐    ┌──────────────────────────┐
│  localStorage │    │  DynamoDB (chat_sessions) │
│  (browser)    │◄──►│  (cross-device)           │
└──────────────┘    └──────────────────────────┘
     Fast              Persistent + Shared
     Same browser      Any device, same farmer_id
```

**Merge logic on mount:** DynamoDB sessions win for conflicts; local-only sessions are kept.

### Storage Limits

| Parameter | Value | Where Enforced |
|---|---|---|
| **Max sessions per farmer** | **20** | Backend (`chat_history.py`) — auto-evicts oldest |
| **Max messages per session** | **100** (50 user + 50 assistant) | Backend (`handler.py`) — returns friendly "start a new session" message |
| **Conversation context window** | Last **40 messages** sent to Bedrock | Backend (`get_chat_history(limit=40)`) — older messages exist in DB but aren't in model context |
| **localStorage message cap** | **50 messages** per session | Frontend (`ChatPage.jsx`) — localStorage is a fast cache, not source of truth |
| **Session title/preview** | First user message, max **60 chars** | Frontend + backend both derive preview |

### Session Lifecycle

```
User opens chat → generate UUID session_id
      ↓
Each message → saved to localStorage (instant) + DynamoDB (async)
      ↓
Messages persist for 30 days (DynamoDB TTL)
      ↓
After 30 days → DynamoDB auto-deletes message rows + session blobs
      ↓
If farmer has > 20 sessions → oldest auto-evicted on next save
      ↓
If session has > 100 messages → backend returns "limit reached" message
```

### Key Files

| File | Purpose |
|---|---|
| `frontend/src/pages/ChatPage.jsx` | Dual-sync session UI, localStorage + DynamoDB merge |
| `backend/lambdas/agent_orchestrator/utils/chat_history.py` | Server-side session CRUD (list, get, save, delete, rename) |
| `backend/lambdas/agent_orchestrator/utils/dynamodb_helper.py` | Individual message persistence with TTL |
| `backend/lambdas/agent_orchestrator/handler.py` | Message limit enforcement, context window building |

---

## 4. DynamoDB TTL Configuration

### Tables & TTL Status

| Table | TTL Enabled | TTL Attribute | Data Stored |
|---|---|---|---|
| `chat_sessions` | **Yes** | `ttl` | Chat messages, session blobs, response cache |
| `rate_limits` | **Yes** | `ttl_epoch` | Rate limit counters |
| `farmer_profiles` | **No** (intentional) | — | Farmer profiles persist indefinitely |

### Data TTLs by Type

| Data Type | TTL | DynamoDB PK Pattern | Auto-Cleanup |
|---|---|---|---|
| **Individual chat messages** | **30 days** | `{session_id}` / `{timestamp}` | DynamoDB TTL deletes |
| **Session blobs** (cross-device sync) | **30 days** | `hist:{farmer_id}` / `{session_id}` | DynamoDB TTL deletes |
| **Response cache** | **1h – 12h** (varies) | `cache:{sha256_hash}` / `cached` | DynamoDB TTL deletes |
| **Rate limit counters** | **2 min – 2 days** (varies) | `{rate_key}` / `{window}` | DynamoDB TTL deletes |

---

## 5. Response Cache TTLs

Cached responses avoid redundant Bedrock API calls. Cache key = SHA-256 of (normalized_query + location + crop + season).

| Query Category | Cache TTL | Rationale |
|---|---|---|
| **Weather** | **1 hour** | Weather changes frequently |
| **Crop advice** | **6 hours** | Crop recommendations are stable intra-day |
| **Pest/disease** | **6 hours** | Pest conditions change slowly |
| **Irrigation** | **6 hours** | Water needs are semi-stable |
| **Government schemes** | **12 hours** | Scheme data rarely changes |
| **General queries** | **3 hours** | Default conservative TTL |

**File:** `backend/lambdas/agent_orchestrator/utils/response_cache.py`

---

## 6. Rate Limiting

Per-session and per-farmer throttling to prevent abuse.

| Window | Max Requests | Counter TTL in DynamoDB |
|---|---|---|
| **Per minute** | **15** | 2 minutes |
| **Per hour** | **120** | 2 hours |
| **Per day** | **500** | 2 days |

**Fail-open design:** If the `rate_limits` table is unreachable, requests are **allowed** (availability > strictness for rural users).

**File:** `backend/lambdas/agent_orchestrator/utils/rate_limiter.py`

---

## 7. Complete Timeout/TTL Summary Matrix

| Component | Duration | Auto-Cleanup | Notes |
|---|---|---|---|
| Cognito ID Token | 1 hour | Auto-refreshed by SDK | Silent refresh using refresh token |
| Cognito Access Token | 1 hour | Auto-refreshed by SDK | Same as above |
| Cognito Refresh Token | 30 days | Manual re-login needed | Full auth cycle after expiry |
| Frontend idle timeout | 30 minutes | Auto-logout | Activity = mouse/key/touch/scroll |
| Frontend session check | 5 minutes | Auto-logout on invalid | Validates Cognito session |
| Chat messages (DynamoDB) | 30 days | DynamoDB TTL | Per-message TTL epoch |
| Chat session blobs | 30 days | DynamoDB TTL | Cross-device sync format |
| Response cache | 1h–12h | DynamoDB TTL | Per-category TTL |
| Rate limit (minute) | 2 minutes | DynamoDB TTL | 15 req/min limit |
| Rate limit (hour) | 2 hours | DynamoDB TTL | 120 req/hr limit |
| Rate limit (day) | 2 days | DynamoDB TTL | 500 req/day limit |
| Max sessions/farmer | 20 | Oldest evicted | Backend-enforced |
| Max messages/session | 100 | Friendly block | Backend-enforced |
| Model context window | 40 messages | Not stored separately | Last 40 fed to Bedrock |
| Farmer profiles | Indefinite | Never expires | Intentional — profiles are permanent |
| Unused Cognito accounts | 7 days | Cognito auto-cleanup | Temp passwords only |
