# PROGRESS TRACKER — Smart Rural AI Advisor (Manoj RS - Backend + Infrastructure)

> **Last Updated:** February 26, 2026  
> **Purpose:** Track all completed work and remaining tasks so any new session can continue seamlessly.  
> **Hackathon Deadline:** March 4, 2026 at 11:59 PM IST

---

## ENVIRONMENT & CREDENTIALS

| Item | Value |
|------|-------|
| AWS Account ID | `948809294205` |
| IAM User | `manoj.rs` |
| Region | `ap-south-1` (Mumbai) |
| AWS CLI Version | v2.31.28 |
| SAM CLI Version | v1.154.0 (in `.venv313`) |
| Python (system) | 3.14 (C:\Python314) — **incompatible with SAM CLI** |
| Python (venv) | 3.13.12 (`.venv313\`) — **use this for SAM** |
| Docker | v29.2.1 (installed, daemon NOT running — not needed for current builds) |
| Lambda Runtime | `python3.13` |
| OpenWeatherMap API Key | *(stored in .env — not committed)* |
| S3 Bucket | `smart-rural-ai-948809294205` (versioning + encryption enabled) |
| SAM Stack Name | `smart-rural-ai` |
| API Gateway URL | `https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/` |
| Bedrock Model (Chat) | Claude Sonnet 4.5 (`anthropic.claude-sonnet-4-5-20250929-v1:0`) |
| Bedrock Model (Embeddings) | Titan Embeddings V2 (`amazon.titan-embed-text-v2:0`) |

### SAM CLI Commands (ALWAYS use this format)
```powershell
# Build
.\.venv313\Scripts\sam.exe build --template-file infrastructure/template.yaml

# Deploy (replace PLACEHOLDERs with real IDs when available)
.\.\.venv313\Scripts\sam.exe deploy --stack-name smart-rural-ai --region ap-south-1 --s3-bucket smart-rural-ai-948809294205 --s3-prefix sam-artifacts --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "OpenWeatherApiKey=$env:OPENWEATHER_API_KEY BedrockAgentId=PLACEHOLDER BedrockAgentAliasId=PLACEHOLDER BedrockKBId=PLACEHOLDER"
```

### Known Gotchas
- **SAM CLI + Python 3.14**: Pydantic v1 crashes. Always use `.venv313\Scripts\sam.exe`
- **PowerShell execution policy**: Set to `RemoteSigned` for CurrentUser
- **AWS CLI pager**: Set `$env:AWS_PAGER = ""` before long-output commands
- **JSON files with BOM**: `create_file` tool writes UTF-8 BOM; use Python to write JSON files for AWS CLI
- **SAM deploy template**: Omit `--template-file` flag so SAM uses `.aws-sam/build/template.yaml` (includes bundled dependencies)

---

## COMPLETED TASKS ✅

### 1. Backend Code — ALL DONE ✅
- [x] **Utility Modules** (`backend/utils/`)
  - `error_handler.py` — Centralized error handling with logging
  - `dynamodb_helper.py` — DynamoDB CRUD operations helper
  - `translate_helper.py` — AWS Translate integration (detect + translate)
  - `polly_helper.py` — AWS Polly text-to-speech (neural voices for hi-IN, ta-IN, te-IN, kn-IN, ml-IN, en-IN)
  - `response_helper.py` — Standardized API response with CORS headers

- [x] **Lambda Functions** (`backend/lambdas/`)
  - Each Lambda directory has: `handler.py`, `utils/` (copied from backend/utils), `requirements.txt`
  
  | Lambda | Path | Description |
  |--------|------|-------------|
  | `weather_lookup` | `backend/lambdas/weather_lookup/` | OpenWeatherMap current + 5-day forecast + farming advisory |
  | `agent_orchestrator` | `backend/lambdas/agent_orchestrator/` | Main chat: detect language → translate → Bedrock Agent → translate back → Polly TTS |
  | `farmer_profile` | `backend/lambdas/farmer_profile/` | GET/PUT /profile/{farmerId} with DynamoDB |
  | `govt_schemes` | `backend/lambdas/govt_schemes/` | 9 curated Indian agricultural schemes, keyword search |
  | `crop_advisory` | `backend/lambdas/crop_advisory/` | Bedrock KB retrieve() with vector search |
  | `image_analysis` | `backend/lambdas/image_analysis/` | Claude Sonnet 4.5 Vision for crop disease detection (4MB limit) |
  | `transcribe_speech` | `backend/lambdas/transcribe_speech/` | Base64 audio → S3 → Transcribe → poll → cleanup |

### 2. Testing — ALL DONE ✅
- [x] **Unit Tests** (`test_unit.py`) — 108 tests, ALL PASSING
- [x] **Smoke Tests** (`test_all.py`) — 92 tests, ALL PASSING
- [x] Tests cover: all Lambda handlers, all utility modules, edge cases, error handling

### 3. AWS Infrastructure — MOSTLY DONE ✅
- [x] **S3 Bucket** — `smart-rural-ai-948809294205` created with versioning + encryption
- [x] **Knowledge Base Docs Uploaded** — 6 markdown files in `s3://smart-rural-ai-948809294205/knowledge_base/`
  - `crop_guide_india.md`, `govt_schemes.md`, `irrigation_guide.md`, `pest_patterns.md`, `region_advisories.md`, `traditional_farming.md`
- [x] **DynamoDB Tables** — Both created manually
  - `farmer_profiles` (PK: `farmer_id`, type: String)
  - `chat_sessions` (PK: `session_id`, SK: `timestamp`, both String)
- [x] **SAM Template** (`infrastructure/template.yaml`)
  - Validated (basic + lint checks pass)
  - Runtime: `python3.13`
  - Defines: 8 Lambda functions + API Gateway
  - Parameters: `BedrockAgentId`, `BedrockAgentAliasId`, `BedrockKBId` (currently PLACEHOLDER), `OpenWeatherApiKey`
  - S3/DynamoDB not defined in template (created manually)
- [x] **SAM Stack Deployed** — `smart-rural-ai` (status: UPDATE_COMPLETE)
- [x] **All 8 Lambda Functions Deployed & Verified**:
  - `smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY`
  - `smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv`
  - `smart-rural-ai-WeatherFunction-dilSoHSLlXGN`
  - `smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO`
  - `smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM`
  - `smart-rural-ai-HealthCheckFunction-FQB8TfJ91HKs`
  - `smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV`
  - `smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt`

### 4. API Endpoints — ALL VERIFIED ✅
Base URL: `https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/`

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/health` | GET | ✅ 200 | Returns service health |
| `/weather?city=Chennai` | GET | ✅ 200 | Live weather + forecast + farming advisory |
| `/schemes` | GET | ✅ 200 | Returns all 9 schemes |
| `/schemes?search=kisan` | GET | ✅ 200 | Keyword search works |
| `/profile/{farmerId}` | GET/PUT | ✅ 200 | DynamoDB read/write works |
| `/chat` | POST | ⚠️ 500 | Returns error because BedrockAgentId is PLACEHOLDER — **expected until Bedrock setup** |
| `/image-analyze` | POST | ✅ 400 | Correct validation (no body = bad request) |
| `/transcribe` | POST | ✅ 400 | Correct validation (no body = bad request) |

### 5. IAM Roles for Bedrock — DONE ✅
- [x] **BedrockKBRole** — For Knowledge Base
  - Trust: `bedrock.amazonaws.com`
  - Permissions: S3 read on KB bucket, Titan Embeddings V2 model invocation
- [x] **BedrockAgentRole** — For Bedrock Agent
  - Trust: `bedrock.amazonaws.com`
  - Permissions: Claude Sonnet 4.5 + Titan Embeddings invoke, Lambda invoke (all 4 action group functions), KB retrieve, S3 read

### 6. Automation Script — DONE ✅ (v2 — Multi-Agent)
- [x] **`setup_bedrock_agent.py` (v2)** — Multi-agent system with SUPERVISOR architecture
  - Uses `boto3` directly (not subprocess/CLI) for reliable JSON handling
  - Creates **3 sub-agents** with their own action groups:
    - `rural-crop-advisor` → CropAdvisoryFunction (+ Knowledge Base)
    - `rural-weather-expert` → WeatherFunction
    - `rural-scheme-navigator` → GovtSchemesFunction
  - Creates **1 supervisor agent** (`smart-rural-supervisor`) with:
    - `agentCollaboration='SUPERVISOR'` mode
    - All 3 sub-agents linked as collaborators via `associate_agent_collaborator`
    - Direct Knowledge Base access for general farming queries
    - Conversation history relayed to sub-agents (`TO_COLLABORATOR`)
  - IAM: Adds `bedrock:InvokeAgent` permission for multi-agent calls
  - Updates `.env` and `bedrock_agentcore_config.json` with real IDs
  - Rebuilds and redeploys SAM stack with supervisor agent IDs
  - Includes `--cleanup` flag to delete all agents before re-running
  - Usage: `python setup_bedrock_agent.py <KB_ID>`
  - Cleanup: `python setup_bedrock_agent.py --cleanup`
- [x] **`setup_bedrock_agent_v1.py`** — Old single-agent version (kept as backup)

### 7. Bedrock Response Format Fix — DONE ✅
- [x] **`response_helper.py`** — Added 4 new Bedrock-specific helpers:
  - `is_bedrock_event(event)` — Detects if Lambda was invoked by Bedrock Agent
  - `parse_bedrock_params(event)` — Extracts params from both `parameters` and `requestBody`
  - `bedrock_response(data, event)` — Returns proper Bedrock action group response format
  - `bedrock_error_response(message, event)` — Returns error in Bedrock format
- [x] **`crop_advisory/handler.py`** — Returns Bedrock format when called by agent, API Gateway format otherwise
- [x] **`weather_lookup/handler.py`** — Dual format (Bedrock + API Gateway)
- [x] **`govt_schemes/handler.py`** — Dual format (Bedrock + API Gateway)
- [x] Updated `response_helper.py` copied to all 7 Lambda utils/ directories

---

## REMAINING TASKS ❌ (in priority order)

### CRITICAL — Must Do for /chat to Work

#### Task A: Install AgentCore SDK
```powershell
pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3
agentcore --help  # Verify installation
```

#### Task B: Create Bedrock Knowledge Base (via Console)
**Why Console?**: OpenSearch Serverless cannot be created via CLI (SubscriptionRequiredException). The Console auto-provisions it.

**Steps:**
1. Go to: https://ap-south-1.console.aws.amazon.com/bedrock/home?region=ap-south-1#/knowledge-bases
2. Click "Create knowledge base"
3. Name: `smart-rural-farming-kb`
4. Description: `Knowledge base for Indian farming advice including crop guides, pest patterns, irrigation, government schemes, and regional advisories`
5. IAM Role: Select existing → `BedrockKBRole`
6. Data source: S3 → `s3://smart-rural-ai-948809294205/knowledge_base/`
7. Embedding model: Titan Text Embeddings V2
8. Chunking: Fixed-size, 300 tokens, 20% overlap
9. Vector store: Quick create (auto-creates OpenSearch Serverless)
10. Create & Sync the data source
11. **Copy the KB ID** (e.g., `ABCDE12345`)

#### Task C: Run AgentCore Setup Script
```powershell
# Full setup (creates Gateway + Lambda targets + deploys agent)
python setup_agentcore.py

# Or step by step:
python setup_agentcore.py --gateway-only    # Step 1: Gateway + targets
python setup_agentcore.py --deploy-only     # Step 2: Deploy agent to Runtime
python setup_agentcore.py --status          # Check status
python setup_agentcore.py --test            # Test deployed agent
```

This will automatically:
- Create 3 IAM roles (Gateway, Invoke, Runtime)
- Create AgentCore Gateway with IAM auth
- Register 4 Lambda functions as MCP tool targets (6 tools total)
- Configure and deploy the Strands Agent to AgentCore Runtime
- Output the agent ARN for the next step

#### Task D: Redeploy SAM with AgentCore ARN
After `setup_agentcore.py` outputs the agent ARN:
```powershell
.\.venv313\Scripts\sam.exe build --template-file infrastructure/template.yaml
.\.\.venv313\Scripts\sam.exe deploy --stack-name smart-rural-ai --region ap-south-1 --s3-bucket smart-rural-ai-948809294205 --s3-prefix sam-artifacts --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "OpenWeatherApiKey=$env:OPENWEATHER_API_KEY BedrockAgentId=PLACEHOLDER BedrockAgentAliasId=PLACEHOLDER BedrockKBId=<KB_ID> AgentCoreRuntimeArn=<AGENT_ARN>"
```

#### Task E: Test /chat Endpoint
```powershell
$body = '{"message": "What crops should I plant in Tamil Nadu during kharif season?", "farmer_id": "farmer_001"}'
Invoke-RestMethod -Uri "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat" -Method POST -Body $body -ContentType "application/json"
```
- Link sub-agents as collaborators with conversation history relay
- Add Lambda permissions for each sub-agent
- Rebuild and redeploy SAM stack with supervisor agent IDs

If you need to re-run (error or changes):
```powershell
python setup_bedrock_agent.py --cleanup
python setup_bedrock_agent.py <KB_ID>
```

#### Task C: Test /chat Endpoint
```powershell
$body = '{"message": "What crops should I plant in Tamil Nadu during kharif season?", "farmer_id": "farmer_001"}'
Invoke-RestMethod -Uri "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat" -Method POST -Body $body -ContentType "application/json"
```

### IMPORTANT — Should Do Before Submission

#### Task F: Enable Amazon Translate (if not already enabled)
- Currently throws `SubscriptionRequiredException`
- Go to: https://ap-south-1.console.aws.amazon.com/translate/home?region=ap-south-1
- Accept terms of service / enable the service
- Test: `aws translate translate-text --text "Hello" --source-language-code en --target-language-code hi --region ap-south-1`

#### Task G: Test Multi-Language Flow
- After Translate is enabled, test /chat with Hindi input:
```json
{"message": "तमिलनाडु में खरीफ सीजन में कौन सी फसल लगाएं?", "farmer_id": "farmer_001"}
```

#### Task H: Test Image Analysis (Crop Doctor)
```powershell
# Encode a test image and send to /image-analyze
$bytes = [System.IO.File]::ReadAllBytes("path\to\crop_image.jpg")
$base64 = [Convert]::ToBase64String($bytes)
$body = @{ image = $base64; farmer_id = "farmer_001" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/image-analyze" -Method POST -Body $body -ContentType "application/json"
```

#### Task I: Test Speech Transcription
- Requires a base64-encoded audio file (WAV/MP3)
- POST to `/transcribe` with `{"audio": "<base64>", "farmer_id": "farmer_001"}`

### NICE TO HAVE — If Time Permits

#### Task H: Frontend Integration
- Update `frontend/src/config.js` with the API Gateway URL
- Sanjay (Frontend lead) handles this, but Manoj needs to provide the URL and test CORS

#### Task I: Demo & Documentation
- Verify demo video link in `demo/demo_video_link.md`
- Add screenshots to `demo/screenshots/`
- Final polish on `docs/PROJECT_SUMMARY.md` and `docs/Smart_Rural_AI_Advisor_Submission.md`

#### Task J: Cost Monitoring
- Check AWS Cost Explorer to stay within $100 budget
- Key cost drivers: Bedrock model invocations, OpenSearch Serverless, Lambda executions

---

## DEPLOYED LAMBDA FUNCTION NAMES

These are needed for any future reference or debugging:

```
smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY
smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv
smart-rural-ai-WeatherFunction-dilSoHSLlXGN
smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO
smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM
smart-rural-ai-HealthCheckFunction-FQB8TfJ91HKs
smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV
smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt
```

## IAM ROLES CREATED

| Role | ARN | Purpose |
|------|-----|---------|
| BedrockKBRole | `arn:aws:iam::948809294205:role/BedrockKBRole` | Knowledge Base (S3 + Titan Embeddings) |
| BedrockAgentRole | `arn:aws:iam::948809294205:role/BedrockAgentRole` | Bedrock Agent (Claude + Lambda + KB + S3) |

## KEY FILES REFERENCE

| File | Purpose |
|------|---------|
| `infrastructure/template.yaml` | SAM CloudFormation template (main infra definition) |
| `agentcore/agent.py` | **Strands Agent for AgentCore Runtime** (BedrockAgentCoreApp entrypoint) |
| `agentcore/tools.py` | **Tool wrappers** (@tool decorated) that invoke existing Lambdas |
| `agentcore/requirements.txt` | AgentCore + Strands SDK dependencies |
| `setup_agentcore.py` | **AgentCore setup**: Gateway + targets + IAM + deploy to Runtime |
| `setup_bedrock_agent.py` | v2: Multi-agent setup via Bedrock Agents API (alternative approach) |
| `setup_bedrock_agent_v1.py` | v1: Single-agent setup (backup) |
| `test_unit.py` | 108 unit tests for all Lambdas and utils |
| `test_all.py` | 92 smoke tests for syntax/import validation |
| `backend/utils/` | Shared utility modules (5 files) |
| `backend/lambdas/*/handler.py` | Lambda handler code (7 functions) |
| `data/knowledge_base/` | 6 farming knowledge docs (also uploaded to S3) |
| `data/govt_schemes.json` | Government schemes data |
| `data/crop_data.csv` | Crop data reference |
| `.env` | Environment variables (created, has PLACEHOLDERs for Bedrock IDs) |
| `PROGRESS_TRACKER.md` | THIS FILE — session continuity tracker |

## TEMP FILES (can be cleaned up)

These were created during IAM role setup and are no longer needed:
- `kb-trust-policy.json`, `kb-permissions-policy.json`
- `kb-config.json`, `kb-storage-config.json`
- `agent-trust-policy.json`, `agent-permissions-policy.json`
- `aoss-enc-policy.json`
- `validate_template.py`

---

## SESSION LOG

### Session 1 — February 26, 2026
- Read full implementation guide (9105 lines) and team workplan
- Implemented all 4 utility modules
- Implemented all 7 Lambda handlers
- All code passed Python syntax validation
- Configured AWS CLI (account 948809294205, region ap-south-1)
- Installed SAM CLI, resolved Python 3.14 incompatibility with .venv313
- Created S3 bucket with versioning + encryption, uploaded 6 KB docs
- Created both DynamoDB tables
- Created smoke tests (92/92 pass) and unit tests (108/108 pass)
- Copied utils/ into each Lambda directory, created requirements.txt for each
- Fixed SAM template (removed existing resources, fixed ARN refs)
- Validated SAM template (basic + lint)
- `sam build` succeeded, deployed with bundled dependencies
- All 8 endpoints tested and working
- Created IAM roles for Bedrock (BedrockKBRole + BedrockAgentRole)
- Hit OpenSearch Serverless SubscriptionRequiredException — KB must be created via Console
- Created `setup_bedrock_agent.py` automation script
- Verified all 8 Lambda functions exist in ap-south-1

**Session ended with:** All backend code deployed and working. Multi-agent setup script (v2) ready. Bedrock setup blocked on Console KB creation (Task A). Next step: Create KB in Console → run `python setup_bedrock_agent.py <KB_ID>` → test /chat.

### Session 2 — February 26, 2026 (continued)
- Upgraded from single-agent to **multi-agent architecture**:
  - Rewrote `setup_bedrock_agent.py` (v2) using boto3 for multi-agent setup
  - Architecture: 1 Supervisor + 3 Sub-agents (CropAdvisor, WeatherExpert, SchemeNavigator)
  - Supervisor uses `agentCollaboration='SUPERVISOR'` mode
  - Sub-agents linked via `associate_agent_collaborator` API with conversation history relay
- Fixed critical bug: Lambda handlers returned API Gateway format when called by Bedrock Agent
  - Added `is_bedrock_event()`, `parse_bedrock_params()`, `bedrock_response()` helpers
  - Updated `crop_advisory`, `weather_lookup`, `govt_schemes` handlers for dual-format responses
- Added `--cleanup` flag to setup script for idempotent re-runs
- All tests still passing: 108 unit tests + 92 smoke tests
- Old script preserved as `setup_bedrock_agent_v1.py`

**Session ended with:** Multi-agent system fully designed and scripted. Waiting for KB creation in Console (Task A). Next: Create KB → run script → test /chat.

### Session 3 — Amazon Bedrock AgentCore Integration
- **Key discovery:** Amazon Bedrock AgentCore is a SEPARATE platform from Amazon Bedrock Agents
  - Bedrock Agents: Fully-managed agent service with `create_agent()` API (what v2 script used)
  - Bedrock AgentCore: Newer agentic platform with Runtime, Gateway, Memory, Identity, Observability
  - AgentCore uses `strands-agents` SDK + `BedrockAgentCoreApp()` + `@app.entrypoint` pattern
  - Deployed via `agentcore configure` + `agentcore deploy` CLI (uses CodeBuild, no Docker needed)
  - Our project docs promise "AgentCore" throughout — so we need to actually use it

- **Approach chosen: Hybrid** — Keep all existing Lambda/SAM infrastructure, add AgentCore on top
  - All 8 Lambda functions stay as-is
  - AgentCore Gateway converts our Lambdas into MCP-compatible tools
  - AgentCore Runtime hosts our Strands Agent (replaces Bedrock Agents invoke)
  - `agent_orchestrator` Lambda calls `invoke_agent_runtime()` instead of `invoke_agent()`

- **New files created:**
  - `agentcore/agent.py` — Strands Agent with BedrockAgentCoreApp entrypoint
  - `agentcore/tools.py` — Tool wrappers (@tool decorated) that invoke our existing Lambdas
  - `agentcore/requirements.txt` — bedrock-agentcore, strands-agents, starter-toolkit
  - `setup_agentcore.py` — Automated setup: IAM → Gateway → Targets → Configure → Deploy

- **Updated files:**
  - `backend/lambdas/agent_orchestrator/handler.py` — Dual mode: AgentCore Runtime (preferred) or Bedrock Agents (fallback), auto-detected from env var `AGENTCORE_RUNTIME_ARN`
  - `infrastructure/template.yaml` — Added `AgentCoreRuntimeArn` parameter, `AGENTCORE_RUNTIME_ARN` env var, `bedrock-agentcore:InvokeAgentRuntime` permission

- **AgentCore architecture:**
  ```
  Farmer → API Gateway → Lambda Orchestrator → AgentCore Runtime (Strands Agent)
                                                    ├→ Gateway → CropAdvisory Lambda (MCP)
                                                    ├→ Gateway → WeatherLookup Lambda (MCP)
                                                    ├→ Gateway → GovtSchemes Lambda (MCP)
                                                    └→ AgentCore Memory (STM + LTM)
  ```

- **IAM roles created by setup_agentcore.py:**
  - `smart-rural-ai-AgentCoreGatewayRole` — Gateway execution (Lambda invoke)
  - `smart-rural-ai-AgentCoreInvokeRole` — Gateway invocation (for agents)
  - `smart-rural-ai-AgentCoreRuntimeRole` — Runtime execution (Bedrock + Lambda + S3 + DynamoDB)

**Session ended with:** AgentCore integration code complete. Next steps: install SDK → run setup → deploy.
