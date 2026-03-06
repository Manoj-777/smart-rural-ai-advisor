# Smart Rural AI Advisor — Architecture Handoff for Kiro

Last updated: 2026-03-06

## 1) System Overview

Smart Rural AI Advisor is an AWS serverless, multilingual advisory platform focused on smallholder farmer workflows:

- AI conversational advisory (`/chat`) with tool-calling.
- Voice input/output (`/transcribe`, `/voice`) for low-literacy access.
- Crop doctor image analysis (`/image-analyze`) using Bedrock multimodal.
- Domain tools for weather, crop recommendations, schemes, soil guidance, farm calendar, and price lookups.
- Cognito-backed sign-in with custom backend OTP + PIN reset endpoints for prototype recovery flow.

The architecture follows a **single API Gateway + multiple Lambda functions + shared DynamoDB data plane + S3/CloudFront frontend** model.

## 2) High-Level Components

### Frontend (React + Vite)

Location: `frontend/src`

Core characteristics:
- React SPA with route-based pages (`ChatPage`, `CropDoctorPage`, `WeatherPage`, `PricePage`, `FarmCalendarPage`, `SoilAnalysisPage`, `CropRecommendPage`, auth/profile pages).
- Cognito session handling in client (`amazon-cognito-identity-js`) for sign-in lifecycle.
- API wrapper attaches JWT token and language/user context headers.
- Speech input via browser-native APIs first; MediaRecorder fallback uploads audio to backend `/transcribe`.
- TTS playback through backend `/voice` endpoint.

### Backend (AWS Lambda Python)

Location: `backend/lambdas`

Primary handlers:
- `agent_orchestrator/handler.py` — main conversational brain and tool-use orchestrator.
- `farmer_profile/handler.py` — profile CRUD + OTP send/verify + PIN reset.
- `image_analysis/handler.py` — crop disease/pest image reasoning with Bedrock model `apac.amazon.nova-pro-v1:0`.
- `weather_lookup/handler.py` — weather + farming recommendations.
- `crop_advisory/handler.py` — retrieval-augmented crop guidance.
- `govt_schemes/handler.py` — curated/knowledge-backed scheme results.
- `transcribe_speech/handler.py` — audio-to-text pipeline.
- `tts/handler.py` — speech synthesis (Polly + gTTS strategy).

Shared utilities:
- `backend/utils/guardrails.py` — prompt and output safety checks.
- `backend/utils/rate_limiter.py` — per-user request controls.
- `backend/utils/dynamodb_helper.py` — persistence helpers.
- `backend/utils/translate_helper.py`, `polly_helper.py` — language services.
- orchestrator utils (`chat_history.py`, `response_cache.py`, `audit_logger.py`).

### Infrastructure

Location: `infrastructure/template.yaml`

Provisions:
- API Gateway routes for all frontend-consumed endpoints.
- Lambda functions with IAM policies for Bedrock, DynamoDB, Translate, Polly, Transcribe, S3, CloudWatch logs.
- DynamoDB tables for user profiles, chat history, cache/rate-limit/audit (logical split depends on template resources).
- S3 + CloudFront static hosting for frontend.
- Cognito user pool/client for app auth.

## 3) Request Flows

### A) Conversational Advisory Flow (`/chat`)

1. Frontend sends user message + language + session metadata.
2. Orchestrator validates/sanitizes input, checks rate limits, resolves session history.
3. Prompt is built with farmer context and tool instructions.
4. Bedrock Converse call is made (primary model: Nova Pro; fallback: Nova Lite if configured by code path).
5. If tool use is requested by model, orchestrator invokes internal tool Lambdas/functions and loops.
6. Final response is post-processed (guardrails, translation normalization, optional TTS pointer), cached, audited, and returned.

### B) Voice Flow

Input path:
1. Client captures voice.
2. Browser speech recognition attempted first.
3. On fallback, recorded audio is sent to `/transcribe`.
4. Backend transcribes and returns text.

Output path:
1. Client requests speech via `/voice` with target language.
2. Backend routes to Polly where supported; fallback to gTTS for broader language coverage.
3. Audio stream/URL returned for client playback.

### C) Crop Doctor Flow (`/image-analyze`)

1. Client uploads/encodes crop image with optional text context.
2. Lambda validates payload and format.
3. Bedrock multimodal inference is called with model `apac.amazon.nova-pro-v1:0`.
4. Output is shaped into farmer-safe advisory format (issue, confidence language, remediation steps).

### D) Auth + Recovery Flow (Prototype)

Sign-in:
- Cognito username/phone + PIN authentication from frontend.

Recovery:
1. `/otp/send` generates secure OTP server-side.
2. For prototype mode, response includes `demo_otp` only when env `ENABLE_DEMO_OTP=true`.
3. `/otp/verify` validates code.
4. `/pin/reset` updates user PIN after successful OTP verification chain.

## 4) Security and Safety Model

### Application controls
- Input validation and normalization in every public handler.
- Guardrails for prompt injection/off-topic/unsafe content handling.
- Response sanitization and controlled formatting to reduce unsafe outputs.
- DynamoDB-backed rate limiting.
- Audit logging for sensitive orchestration steps.

### Authentication and access
- Cognito token-based frontend auth for protected actions.
- IAM least-privilege intent in Lambda execution roles (service-scoped policies).

### Prototype vs production toggles
- `ENABLE_DEMO_OTP=true` is demo-friendly but not production-safe.
- Production posture should disable demo OTP and use trusted out-of-band delivery only.

## 5) Data and State

Main state categories:
- User identity/profile + preferences.
- Session/chat history.
- Response cache entries.
- Rate limiter counters/windows.
- Audit records.

Storage and lifecycle:
- DynamoDB stores short/medium-lived conversational and control-plane state.
- TTL/cleanup logic is used where configured to keep operational data bounded.

## 6) Deployment and Operations

### Backend deployment
- CloudFormation/SAM template is source of truth.
- Build + package + deploy updates Lambda/API/IAM resources.

### Frontend deployment
- Vite build output uploaded to S3 bucket.
- CloudFront invalidation required to clear stale assets after release.

### Typical release checks
- Smoke-test `/chat`, `/otp/send`, `/otp/verify`, `/pin/reset`, `/image-analyze`.
- Verify stack status reaches `UPDATE_COMPLETE`.
- Confirm latest frontend build hash is served after invalidation.

## 7) Current Known Architecture Notes

- `ARCHITECTURE_FOR_KIRO.md` is now the canonical handoff doc for architecture generation.
- Repository contains some legacy/inactive scripts used during earlier OTP/telecom experiments.
- There is an incomplete/inactive `backend/lambdas/whatsapp_notification/handler.py` that is not currently wired as active API path.

## 8) Production Hardening Checklist (When Exiting Prototype Mode)

1. Set `ENABLE_DEMO_OTP=false`.
2. Enforce strict OTP attempt and lockout policies.
3. Add/verify WAF and API throttling at edge.
4. Tighten IAM permissions by explicit resource ARNs where possible.
5. Add centralized secret management and rotation checks.
6. Expand synthetic monitoring for multilingual/voice/image endpoints.

---

## 9) Copy-Paste Prompt for Kiro CLI

Use this prompt in Kiro CLI to generate architecture assets (diagram spec, service contracts, and implementation notes) directly from this repo context.

```text
You are generating architecture deliverables for the repository “smart-rural-ai-advisor”.

Objective:
Produce a complete, implementation-grounded AWS architecture package that matches the existing code and infra.

Constraints:
- Do not invent services not present in code/template unless clearly marked “recommended future improvement”.
- Treat infrastructure/template.yaml as the deployment source of truth.
- Treat frontend/src and backend/lambdas as runtime source of truth.
- Keep prototype-vs-production distinctions explicit, especially around OTP.

Deliverables required:
1) Executive architecture summary (1-2 pages)
2) Component inventory table:
	- Component name
	- Runtime (Lambda/React/Cognito/etc.)
	- Responsibility
	- Inputs/outputs
	- Dependencies
3) API contract map:
	- Route
	- Method
	- Auth requirements
	- Request/response schema summary
	- Backing Lambda
4) Data model and state map:
	- DynamoDB entities/tables, primary keys, TTL usage
	- Session, cache, audit, profile state boundaries
5) End-to-end sequence flows:
	- /chat tool-calling flow
	- Voice (transcribe + TTS) flow
	- Crop Doctor image analyze flow
	- OTP send/verify + PIN reset flow
6) Security posture section:
	- Guardrails, validation, auth, rate limits, logging
	- Prototype risks and production hardening actions
7) Deployment architecture:
	- Backend release path (SAM/CloudFormation)
	- Frontend release path (S3 + CloudFront invalidation)
	- Rollback considerations
8) Mermaid diagrams:
	- C4-ish container diagram
	- Request flow sequence for /chat with tool-use
	- Auth recovery sequence (OTP + PIN reset)
9) Gap analysis:
	- Legacy/inactive modules
	- Operational risks
	- Prioritized technical debt list

Repository specifics to incorporate:
- Main orchestrator: backend/lambdas/agent_orchestrator/handler.py
- Profile/OTP/PIN: backend/lambdas/farmer_profile/handler.py
- Image analysis model: apac.amazon.nova-pro-v1:0 in backend/lambdas/image_analysis/handler.py
- Infra source: infrastructure/template.yaml
- Frontend routes/pages under frontend/src
- Demo OTP env flag: ENABLE_DEMO_OTP

Output format:
- Start with “Architecture Fidelity Notes” that lists assumptions.
- Then provide each deliverable section in order.
- Include Mermaid code blocks that are syntactically valid.
- End with “Action Plan (30/60/90 days)” tailored to this repo.
```

