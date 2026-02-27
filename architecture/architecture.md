# Architecture Overview

## Smart Rural AI Advisor — System Architecture

### High-Level Flow

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
    │                         ├─ Amazon Bedrock AgentCore
    │                         │    ├─ Claude Sonnet 4.5 (reasoning)
    │                         │    ├─ Knowledge Base (S3 → Titan Embed → OpenSearch)
    │                         │    └─ Action Groups → Tool Lambdas
    │                         │         ├─ crop_advisory
    │                         │         ├─ weather_lookup (OpenWeatherMap)
    │                         │         ├─ govt_schemes
    │                         │         └─ farmer_profile (DynamoDB)
    │                         │
    │                         ├─ Amazon Translate (multilingual)
    │                         ├─ Amazon Polly (text-to-speech)
    │                         └─ DynamoDB (chat history)
    │
    ├─ POST /voice ─────► Agent Orchestrator Lambda (same)
    ├─ GET  /weather/{loc} ► Weather Lambda → OpenWeatherMap API
    ├─ GET  /schemes ────► Govt Schemes Lambda → Knowledge Base
    ├─ POST /image-analyze ► Image Analysis Lambda → Claude Sonnet 4.5 Vision
    ├─ GET  /profile/{id} ► Farmer Profile Lambda → DynamoDB
    ├─ PUT  /profile/{id} ► Farmer Profile Lambda → DynamoDB
    ├─ POST /transcribe ──► Transcribe Lambda → Amazon Transcribe
    └─ GET  /health ──────► Health Check (inline)
```

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
