# Architecture Overview

## Smart Rural AI Advisor — Cognitive Multi-Agent Architecture

### Design Philosophy

Instead of traditional domain-specialist agents (Weather Agent, Crop Agent, etc.) that are just tool wrappers, we use **cognitive-role agents** that mirror how an expert thinks:

1. **Memory** — recall farmer context and seasonal awareness
2. **Understanding** — parse the query, detect language, extract intent
3. **Reasoning** — call tools, retrieve data, synthesize an answer
4. **Fact-Checking** — validate the response against tool outputs, detect hallucinations
5. **Communication** — adapt the response to the farmer's language and culture

Each agent is a separate Bedrock AgentCore runtime with its own role-specific system prompt.
Only the **Reasoning** agent has access to all 6 Lambda tools.
Only the **Memory** agent can read farmer profiles.
The others are pure cognitive (LLM-only, no tools).

---

### Cognitive Pipeline Flow

```
Farmer (Mobile/Desktop)
    │
    ▼
React Frontend (S3 + CloudFront)
    │  Voice: Web Speech API (Chrome/Edge)
    │         Amazon Transcribe fallback (Firefox)
    │
    ▼
API Gateway (REST, ap-south-1)
    │
    ├─ POST /chat ──────► Agent Orchestrator Lambda
    │                         │
    │      ┌─────────────────────────────────────────────────────────┐
    │      │              COGNITIVE PIPELINE (5 agents)              │
    │      │                                                         │
    │      │  ① Memory Agent ───────────────────────────────┐        │
    │      │     └─ get_farmer_profile tool                 │        │
    │      │     └─ Returns: farmer_context, season_info    │        │
    │      │                                                ▼        │
    │      │  ② Understanding Agent ────────────────────────┐        │
    │      │     └─ No tools (pure LLM reasoning)           │        │
    │      │     └─ Returns: {language, intents, entities,  │        │
    │      │                  confidence, enriched_query}    │        │
    │      │                                                ▼        │
    │      │  ③ Reasoning Agent ────────────────────────────┐        │
    │      │     └─ 6 Lambda tools (weather, crop, pest,    │        │
    │      │        schemes, irrigation, profile)           │        │
    │      │     └─ Returns: {result, tools_used,           │        │
    │      │                  tool_outputs}                  │        │
    │      │                                                ▼        │
    │      │  ④ Fact-Checking Agent ────────────────────────┐        │
    │      │     └─ No tools (pure LLM reasoning)           │        │
    │      │     └─ Compares advisory vs. tool_outputs      │        │
    │      │     └─ Returns: {validated, confidence,        │        │
    │      │                  corrections, warnings,        │        │
    │      │                  hallucinations_found}          │        │
    │      │                                                ▼        │
    │      │  ⑤ Communication Agent ────────────────────────┘        │
    │      │     └─ No tools (pure LLM reasoning)                    │
    │      │     └─ Adapts to farmer's language and culture          │
    │      │     └─ Returns: localized, farmer-friendly text         │
    │      └─────────────────────────────────────────────────────────┘
    │                         │
    │                         ├─ Amazon Translate (13 Indian languages)
    │                         ├─ Amazon Polly + gTTS (text-to-speech)
    │                         └─ DynamoDB (chat history)
    │
    ├─ POST /voice ─────► Agent Orchestrator Lambda (same pipeline)
    ├─ GET  /weather/{loc} ► Weather Lambda → OpenWeatherMap API
    ├─ GET  /schemes ────► Govt Schemes Lambda → Knowledge Base
    ├─ POST /image-analyze ► Image Analysis Lambda → Claude Sonnet 4.5 Vision
    ├─ GET  /profile/{id} ► Farmer Profile Lambda → DynamoDB
    ├─ PUT  /profile/{id} ► Farmer Profile Lambda → DynamoDB
    ├─ POST /transcribe ──► Transcribe Lambda → Amazon Transcribe
    └─ GET  /health ──────► Health Check (inline)
```

### Agent Role Matrix

| Agent | Runtime Name | Tools | Input | Output |
|---|---|---|---|---|
| **Memory** | SmartRuralMemory | `get_farmer_profile` | farmer_id, session_id | Enriched farmer context + seasonal awareness |
| **Understanding** | SmartRuralUnderstanding | None (LLM only) | Raw user query | `{language, intents[], entities{}, confidence, enriched_query}` |
| **Reasoning** | SmartRuralReasoning | All 6 Lambda tools | Understanding output | `{result, tools_used[], tool_outputs{}}` |
| **Fact-Checking** | SmartRuralFactChecking | None (LLM only) | Advisory + tool_outputs | `{validated, confidence, corrections[], warnings[]}` |
| **Communication** | SmartRuralCommunication | None (LLM only) | Validated advisory + target language | Localized, farmer-friendly response text |
| **Master** (legacy) | SmartRuralAdvisor | All 6 Lambda tools | Full query | Complete response (backward compatible) |

### Why Cognitive Roles Instead of Domain Specialists?

| Old Architecture (Domain Specialists) | New Architecture (Cognitive Roles) |
|---|---|
| Weather Agent, Crop Agent, Pest Agent, etc. | Understanding, Reasoning, Fact-Checking, etc. |
| Each agent is a tool wrapper with the same code | Each agent has a genuinely different capability |
| No validation — hallucinations unchecked | Fact-Checking agent verifies against tool data |
| Language handling mixed into every agent | Dedicated Communication agent for localization |
| No structured intent parsing | Understanding agent produces structured JSON |
| All agents have all tools | Only Reasoning agent has tools (principle of least privilege) |

### AWS Services Used

| Service | Purpose | Cost Impact |
|---------|---------|-------------|
| Bedrock AgentCore | AI orchestration with memory + guardrails | Per-invocation |
| Claude Sonnet 4.5 | Foundation model for reasoning | ~$3/1K input, ~$15/1K output |
| Bedrock Knowledge Base | RAG over farming documents | Per-query |
| Lambda (x7) | Serverless compute | Free tier covers most |
| API Gateway | REST API | Free tier: 1M calls/month |
| DynamoDB | Farmer profiles + chat sessions | Free tier: 25 GB |
| S3 | Knowledge base docs + audio files | ~$0.023/GB |
| CloudFront | Frontend CDN | Free tier: 1 TB/month |
| Polly | Text-to-speech (Indian voices) | $4/1M characters |
| Translate | Multilingual (en/hi/ta/te/kn) | $15/1M characters |
| Transcribe | Voice-to-text fallback | $0.024/min |
| SNS | Weather alerts (optional) | Free tier: 1M publishes |

### Region
**ap-south-1 (Mumbai)** — lowest latency for Indian users.

### Budget
**$100 AWS credits** — see Detailed Implementation Guide Section 22 for cost breakdown.
