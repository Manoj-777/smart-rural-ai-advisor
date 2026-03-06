# Smart Rural AI Advisor — Eraser Diagram Prompt (Iteration 3 - CORRECTED)

Use this prompt in Eraser AI to generate a **current-state AWS architecture** diagram.

## Objective
Generate one detailed but readable architecture diagram for Smart Rural AI Advisor.

## Scope
- Include only currently used components.
- Show request flow, data flow, telemetry flow.
- Include CRUD paths for profile and chat/session data.
- **CORRECTED**: Frontend (React SPA) is served via CloudFront from S3, but API calls go directly from browser to API Gateway (standard web architecture).

## Components
- Users: Farmers (web browser - mobile/desktop)
- Edge: CloudFront (CDN)
- Frontend Storage: S3 Static Website (React build artifacts)
- Audio Storage: S3 Audio Bucket (TTS MP3 files with presigned URLs)
- Knowledge Base Storage: S3 Knowledge Base Bucket (crop documents for Bedrock KB)
- API/Security: API Gateway (REST API, 9 routes), Cognito User Pool (phone+PIN auth), IAM (execution roles), Secrets Manager (OpenWeather API key)
- Compute: Agent Orchestrator Lambda (120s, 256MB), Weather Lambda (30s, 256MB), Crop Advisory Lambda (30s, 256MB), Govt Schemes Lambda (30s, 256MB), Image Analysis Lambda (60s, 512MB), Transcribe Lambda (60s, 256MB), Farmer Profile Lambda (30s, 256MB), HealthCheck Lambda (10s, 128MB)
- AI/ML: Bedrock Nova Pro (apac.amazon.nova-pro-v1:0 - primary reasoning), Bedrock Nova Lite (global.amazon.nova-2-lite-v1:0 - bidirectional fallback + translation tasks), Bedrock Knowledge Base (RAG), Bedrock Guardrails (optional, content safety), Amazon Translate (13 languages), Amazon Polly (Hindi/English TTS), Amazon Transcribe (voice-to-text), gTTS library (11 Indian languages TTS)
- Data: DynamoDB farmer_profiles (PK: farmer_id), chat_sessions (PK: session_id, SK: timestamp, TTL: 30 days), otp_codes (PK: phone, TTL: 5 minutes), rate_limits (PK: farmer_id, TTL: auto-expire)
- Monitoring: CloudWatch Logs, CloudWatch Metrics
- External: OpenWeather API (current weather + 5-day forecast)

## Icon Mapping (force these icon categories)
- Users: person icon
- CloudFront/API/Cognito/IAM/Secrets: network/security/service icons
- Lambda components: compute/function icon
- Bedrock/Translate/Polly/Transcribe: AI/ML managed service icons
- DynamoDB tables: database/table icons
- S3 buckets: storage bucket icons
- CloudWatch: monitoring/observability icons
- OpenWeather: external system icon

## API Endpoint to Compute Mapping (CORRECTED)
**Note**: All API calls originate from the React SPA running in the user's browser, NOT from S3. S3 only serves static files.

- Browser (React SPA) → API Gateway `/chat` → Agent Orchestrator Lambda
- Browser (React SPA) → API Gateway `/voice` → Agent Orchestrator Lambda  
- Browser (React SPA) → API Gateway `/image-analyze` → Image Analysis Lambda
- Browser (React SPA) → API Gateway `/weather/{location}` → Weather Lambda (direct endpoint, also callable as tool)
- Browser (React SPA) → API Gateway `/schemes` → Govt Schemes Lambda (direct endpoint, also callable as tool)
- Browser (React SPA) → API Gateway `/profile/{farmerId}` (GET/PUT/DELETE) → Farmer Profile Lambda
- Browser (React SPA) → API Gateway `/otp/send` → Farmer Profile Lambda
- Browser (React SPA) → API Gateway `/otp/verify` → Farmer Profile Lambda
- Browser (React SPA) → API Gateway `/pin/reset` → Farmer Profile Lambda
- Browser (React SPA) → API Gateway `/transcribe` → Transcribe Lambda
- Browser (React SPA) → API Gateway `/health` → HealthCheck Lambda (inline handler)

## Mandatory Flows (CORRECTED)
1. **Frontend Delivery**: Farmer (browser) → CloudFront → S3 Static Website (serves React SPA)
2. **API Calls**: Browser (React SPA) → API Gateway (HTTPS, CORS-enabled)
3. **IMPORTANT**: Do NOT draw "S3 Web → API Gateway" - S3 only serves static files, API calls come from browser
4. **Authentication**: Browser → Cognito (sign-in, token refresh)
5. **Authorization**: API Gateway → Cognito Authorizer (JWT validation on protected routes)
6. **IAM Roles**: Lambda execution roles authorize downstream AWS service access (show as note/boundary, not data flow)
7. **Chat/Voice**: API Gateway → Agent Orchestrator Lambda
8. **Tool Invocation**: Agent Orchestrator → Domain Lambdas (Weather, Crop, Schemes, Profile) via Lambda.invoke()
9. **AI Services**: Agent Orchestrator → Bedrock Nova Pro/Lite, Translate, Polly, Guardrails (optional)
10. **Knowledge Base**: Crop Advisory Lambda → Bedrock KB → S3 Knowledge Base Bucket
11. **Image Analysis**: Image Analysis Lambda → Bedrock Nova Pro Vision
12. **Voice Transcription**: Transcribe Lambda → Amazon Transcribe service
13. **TTS Audio**: Polly/gTTS → S3 Audio Bucket (presigned URLs, 1-2 hour expiry)
14. **Profile CRUD**: Farmer Profile Lambda ↔ farmer_profiles table (bidirectional)
15. **OTP Management**: Farmer Profile Lambda ↔ otp_codes table (create/read/delete)
16. **Chat History**: Agent Orchestrator ↔ chat_sessions table (read last 40 messages, write new messages)
17. **Rate Limiting**: Agent Orchestrator ↔ rate_limits table (read/update counters)
18. **Weather Data**: Weather Lambda → Secrets Manager (read API key) → OpenWeather API
19. **Monitoring**: All Lambdas + API Gateway → CloudWatch (logs + metrics)
20. **Response Path**: Lambda → API Gateway → Browser (React SPA) → Farmer (rendered UI)

## Request/Data Flow Detail (numbered sequence)
### A) Chat/Text request
1. Farmer opens SPA via CloudFront (origin S3 Web)
2. SPA authenticates with Cognito and stores session/JWT tokens
3. SPA sends chat payload + JWT to API Gateway `/chat`
4. API Gateway validates JWT via Cognito authorizer/claims
5. API Gateway invokes Agent Orchestrator Lambda
6. Orchestrator reads profile/session context from DynamoDB (`farmer_profiles`, `chat_sessions`)
7. Orchestrator checks/updates `rate_limits`
8. Orchestrator invokes Bedrock Nova Pro (fallback Nova Lite on failure policy)
9. Orchestrator may call domain Lambdas as tools (weather/crop/schemes/image/profile)
10. Orchestrator may call Translate and Polly based on user language and output mode
11. Orchestrator writes response/session records to `chat_sessions`
12. API Gateway returns response to SPA
13. SPA renders response to farmer in browser UI

### B) Profile + OTP lifecycle
1. SPA calls `/otp/send` -> Profile Lambda writes OTP token in `otp_codes`
2. SPA calls `/otp/verify` -> Profile Lambda reads + validates OTP, then deletes/invalidates used OTP
3. SPA calls `/profile/{farmerId}` GET -> Profile Lambda reads `farmer_profiles`
4. SPA calls `/profile/{farmerId}` PUT -> Profile Lambda creates/updates `farmer_profiles`
5. SPA calls `/profile/{farmerId}` DELETE -> Profile Lambda deletes profile record; may trigger auth cleanup flow
6. Profile Lambda returns status payload to API Gateway -> SPA for each operation

### C) Weather request
1. SPA calls `/weather/{location}`
2. Weather Lambda reads OpenWeather key from Secrets Manager (authorized by IAM role)
3. Weather Lambda calls OpenWeather API
4. Weather Lambda returns normalized weather payload to API response
5. API Gateway returns weather payload to SPA UI

## Bidirectional CRUD Matrix (must appear in diagram notes)
- Farmer Profile Lambda <-> `farmer_profiles`
	- Create: PUT profile
	- Read: GET profile
	- Update: PUT profile
	- Delete: DELETE profile
- Farmer Profile Lambda <-> `otp_codes`
	- Create: OTP send
	- Read: OTP verify
	- Delete: OTP consumed/expired cleanup
- Agent Orchestrator <-> `chat_sessions`
	- Create/Append: save user and assistant messages
	- Read: retrieve recent conversation context
- Agent Orchestrator <-> `rate_limits`
	- Read: check current counters
	- Update/Create: increment counters with TTL window

## Telemetry Matrix (must appear with dashed lines)
- API Gateway -> CloudWatch (access metrics/logs)
- All Lambdas -> CloudWatch (application logs + metrics)
- Weather/Crop/Image/Profile Lambdas -> CloudWatch logs

## Exclusions (Do Not Add)
- WAF/Shield node as active deployed component
- Separate DynamoDB audit table
- Assumed phone GSI
- Extra Lambda services not in current backend

## Visual Rules
- Left-to-right layered: Users -> Edge -> API/Security -> Compute -> AI/ML + Data -> Observability + External
- Solid arrows: request/data
- Dashed arrows: telemetry
- Keep crossing lines minimal
- Label each arrow with action verb: invoke, read, write, retrieve, synthesize, translate, authenticate, log

## Final Prompt to Paste into Eraser (Iteration 3 - Canonical)
You are a senior cloud architect. Generate a production-grade AWS architecture diagram for Smart Rural AI Advisor (agri assistant for rural India).
Create one detailed technical diagram with clean layout, AWS icons, and labeled data flows.
Do not invent components that are not explicitly listed below.

Create a current-state AWS architecture diagram for Smart Rural AI Advisor.

Requirements:
1) Use this exact layer order from left to right:
Users, Edge+Frontend, API+Security, Compute, AI/ML, Data, Observability+External.
2) Add these components exactly:
- Users: Farmers
- Edge+Frontend: CloudFront, S3 Web, S3 Audio Cache, S3 Knowledge Docs
- API+Security: API Gateway, Cognito, IAM, Secrets Manager
- Compute: Agent Orchestrator Lambda, Weather Lambda, Crop Advisory Lambda, Govt Schemes Lambda, Image Analysis Lambda, Transcribe Lambda, Farmer Profile Lambda, HealthCheck Lambda
- AI/ML: Bedrock Nova Pro, Bedrock Nova Lite fallback, Bedrock Knowledge Base, Amazon Translate, Amazon Polly, Amazon Transcribe
- Data: DynamoDB farmer_profiles, chat_sessions, otp_codes, rate_limits
- Observability+External: CloudWatch, OpenWeather API
3) Draw these mandatory connections:
- Farmers->CloudFront->S3 Web
- S3 Web (running in browser)->API Gateway
- Do NOT draw Farmers->API Gateway
- API Gateway->S3 Web runtime (HTTP response to browser app)
- S3 Web runtime->Farmers (rendered response)
- S3 Web runtime<->Cognito (sign-in/session/token refresh)
- APIGateway->Cognito authorizer (JWT validation)
- API Gateway->Agent Orchestrator
- API Gateway->Farmer Profile Lambda
- API Gateway->Weather Lambda
- API Gateway->Image Analysis Lambda
- API Gateway->Transcribe Lambda
- API Gateway->Govt Schemes Lambda
- API Gateway->HealthCheck Lambda
- Weather Lambda->Secrets Manager (read API key)
- IAM roles authorize Lambda access to AWS services (show as governance boundary/note, not request-response arrow)
- Orchestrator->Weather/Crop/Schemes/Image/Profile Lambdas (tool calls)
- Orchestrator->Bedrock Nova Pro (primary), Nova Lite (fallback), Translate, Polly
- Crop Advisory->Bedrock KB->S3 Knowledge Docs
- Image Analysis->Bedrock Nova Pro
- Transcribe Lambda->Amazon Transcribe
- Polly->S3 Audio Cache
- Farmer Profile Lambda<->farmer_profiles (bidirectional CRUD)
- Farmer Profile Lambda<->otp_codes (create/read/delete)
- Orchestrator<->chat_sessions (read/write)
- Orchestrator<->rate_limits (read/update)
- Weather Lambda->OpenWeather API
- API Gateway and all Lambdas->CloudWatch
3.1) Authentication flow must be shown explicitly as a separate labeled chain:
- Farmers->CloudFront->S3 Web runtime
- S3 Web runtime<->Cognito (sign-in with phone+PIN, token refresh)
- S3 Web runtime->API Gateway (Authorization: Bearer JWT)
- API Gateway->Cognito authorizer (JWT validation)
- API Gateway->S3 Web runtime (authorized response)

3.2) OTP storage and verification flow must be shown explicitly as a separate labeled chain:
- S3 Web runtime->API Gateway `/otp/send`->Farmer Profile Lambda
- Farmer Profile Lambda->otp_codes (PutItem with TTL)
- S3 Web runtime->API Gateway `/otp/verify`->Farmer Profile Lambda
- Farmer Profile Lambda->otp_codes (GetItem for validation)
- Farmer Profile Lambda->otp_codes (DeleteItem on success/expiry)
- Farmer Profile Lambda->S3 Web runtime (verification status)
4) Add reverse/response edges for major synchronous paths:
- Lambda->API Gateway (handler responses)
- API Gateway->S3 Web runtime (HTTP response)
- S3 Web runtime->Farmers (rendered UI update)
5) Use line semantics:
- Solid lines for primary request/data and response paths
- Dashed lines for telemetry
6) Attach concise edge labels:
- authenticate, invoke, tool-call, query, retrieve, read, write, update, synthesize, transcribe, log, trace
7) Add a legend for solid vs dashed lines.
8) Keep diagram clean and readable: minimal crossing lines, grouped boundaries, no decorative clutter.
9) Do NOT add: WAF/Shield active node, AuditLogs DynamoDB table, speculative services, Farmers->API Gateway direct edge, API Gateway as CloudFront origin/proxy.
10) Add Bedrock Guardrails only if explicitly confirmed enabled in runtime configuration; otherwise omit.

## Acceptance Checklist
- Every listed component exists exactly once
- Every mandatory flow is shown
- Authentication chain is explicitly drawn end-to-end
- OTP send/verify path to `otp_codes` is explicitly drawn with put/get/delete semantics
- Bidirectional CRUD edges are explicitly directional where needed
- Telemetry is dashed and separated from core request flow
- No excluded/speculative components are present
- No contradictory frontdoor edges (all API calls originate from web app runtime)
