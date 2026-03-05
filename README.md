# 🌾 Smart Rural AI Advisor

### AI-Powered Agricultural Advisory for Bharat's Farmers

> **Hackathon:** AWS AI for Bharat 2026  
> **Team:** Creative Intelligence (CI)  
> **Live Prototype:** [https://d80ytlzsrax1n.cloudfront.net](https://d80ytlzsrax1n.cloudfront.net)  
> **Demo Video:** [Watch on YouTube](#) <!-- TODO: replace with actual link -->  
> **Repository:** [github.com/Manoj-777/smart-rural-ai-advisor](https://github.com/Manoj-777/smart-rural-ai-advisor)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Our Solution](#our-solution)
3. [Why AI Is Required](#why-ai-is-required)
4. [Key Features](#key-features)
5. [Architecture](#architecture)
6. [AWS Services & How They're Used](#aws-services--how-theyre-used)
7. [Generative AI on AWS — Deep Dive](#generative-ai-on-aws--deep-dive)
8. [Supported Languages](#supported-languages)
9. [Live Prototype](#live-prototype)
10. [Demo Walkthrough](#demo-walkthrough)
11. [Tech Stack](#tech-stack)
12. [Project Structure](#project-structure)
13. [Local Development](#local-development)
14. [API Reference](#api-reference)
15. [Impact & Metrics](#impact--metrics)
16. [Team](#team)

---

## Problem Statement

**70 % of India's population depends on agriculture**, yet small-scale farmers face critical information gaps:

| Challenge | Scale |
|---|---|
| **No access to expert advice** | Agricultural extension officers cover 1 000+ farmers each |
| **Language barriers** | Most resources are in English; farmers speak Tamil, Hindi, Telugu, Kannada, and 9 more languages |
| **Delayed pest / disease response** | By the time a disease is identified, significant crop loss has already occurred |
| **Unawareness of government schemes** | ₹2+ lakh crore in benefits go unclaimed every year |
| **Weather unpredictability** | Climate change makes traditional farming calendars unreliable |

**Target users:** Small and marginal farmers (< 5 acres) across India — primarily Tamil Nadu, Andhra Pradesh, Telangana, Karnataka — ages 25–65, often with limited English literacy, using an Android smartphone with basic internet.

---

## Our Solution

**Smart Rural AI Advisor** is a fully serverless, voice-first, multilingual AI assistant that gives Indian farmers instant, personalised agricultural guidance — in their own language — through a simple web interface.

Farmers can **speak or type** in any of **13 Indian languages**. The AI:

1. **Understands** the query (intent, language, entities)
2. **Retrieves real data** — live weather, curated crop advisories, government scheme details
3. **Reasons** over the data to produce actionable, grounded advice
4. **Validates** the response against tool outputs to prevent hallucination
5. **Responds** in the farmer's language with **audio playback** so even low-literacy users benefit

---

## Why AI Is Required

Traditional information systems (static FAQs, IVR hotlines, PDFs) fail rural farmers for three reasons:

| Limitation | How Generative AI Solves It |
|---|---|
| **One language only** | Amazon Bedrock (Nova Pro) + Amazon Translate handle 13 Indian languages natively — no separate content for each language |
| **Generic, not contextual** | The AI reasons across a farmer's profile (crops, soil, location, season) to deliver **personalised** advice in real time |
| **No expert reasoning** | Foundation models perform multi-step reasoning: correlate symptoms → retrieve pest data → cross-check weather → suggest treatment — mimicking an agricultural scientist |
| **Crop disease diagnosis** | Nova Pro Vision analyses uploaded crop/leaf photos and returns a diagnosis with treatment steps — no lab visit needed |
| **Voice accessibility** | Voice input (Web Speech API + Amazon Transcribe) and voice output (Amazon Polly + gTTS) make the system usable for farmers who cannot read or type comfortably |

**Bottom line:** Without Generative AI, building a system that reasons across weather + crop science + pest databases + government policy — in 13 languages, with voice — would be infeasible for a small team.

---

## Key Features

| Feature | Description | AWS Service |
|---|---|---|
| 💬 **AI Chat** | Conversational farming advisor with tool-calling and grounded responses | Amazon Bedrock (Nova Pro) |
| 🌤️ **Weather** | Real-time weather + 5-day forecast + farming-specific advisory | AWS Lambda + OpenWeather API |
| 🌾 **Crop Advisory** | Season-, soil-, and region-aware crop recommendations | Lambda + Bedrock Knowledge Base |
| 🐛 **Pest & Disease** | Symptom-based diagnosis with organic & chemical treatments; cautious, confirmation-first framing | Bedrock (Nova Pro) reasoning |
| 📋 **Govt Schemes** | Eligibility, benefits, and application steps for 10+ central/state schemes (PM-KISAN, PMFBY, etc.) | Lambda + curated knowledge base |
| 📸 **Crop Doctor** | Upload a leaf/crop photo → AI diagnoses the disease with severity and treatment plan | Bedrock (Nova Pro Vision) |
| 👤 **Farmer Profile** | Persistent farm details (crops, soil, district) for personalised responses | Amazon DynamoDB |
| 🎤 **Voice Input** | Speak in any supported language → converted to text | Web Speech API + Amazon Transcribe |
| 🔊 **Voice Output** | Hear AI responses spoken aloud in your language | Amazon Polly + gTTS |
| 🌐 **13 Languages** | Full UI + chat + voice in Tamil, Hindi, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, Urdu, English | Amazon Translate |
| 🔒 **Guardrails** | Topic gating, hallucination prevention, rate limiting, Bedrock Guardrails | Bedrock Guardrails + code-level policy |
| 🗺️ **Interactive Weather Map** | Leaflet-based map with city quick-select and forecast overlays | React-Leaflet + Lambda |

---

## Architecture

### High-Level Flow

```
 ┌────────────────────┐
 │  Farmer (Mobile /   │
 │  Desktop Browser)   │
 └────────┬───────────┘
          │  HTTPS
          ▼
 ┌────────────────────┐        ┌──────────────────────────────────────────────────┐
 │  React 18 + Vite   │        │  Amazon CloudFront (CDN)                         │
 │  Single-Page App   │◄──────►│  S3 Static Hosting                               │
 │  13-language i18n   │        └──────────────────────────────────────────────────┘
 └────────┬───────────┘
          │  REST API
          ▼
 ┌────────────────────┐
 │  Amazon API Gateway │  ── 9 routes, CORS-enabled, ap-south-1
 └────────┬───────────┘
          │
          ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                     AWS Lambda Functions (Python 3.13)                       │
 │                                                                              │
 │  ┌─────────────────────────────────────────────────────────────────────┐     │
 │  │  Agent Orchestrator (the brain)                                     │     │
 │  │                                                                     │     │
 │  │  1. Amazon Translate  ─ detect language, translate to English        │     │
 │  │  2. Amazon Bedrock    ─ Nova Pro: intent + tool-calling + reasoning  │     │
 │  │  3. Tool Execution    ─ invoke child Lambdas for real data           │     │
 │  │  4. Post-Processing   ─ fact-check, format, translate back           │     │
 │  │  5. Amazon Polly/gTTS ─ generate audio in farmer's language          │     │
 │  │  6. DynamoDB          ─ persist chat history + session context        │     │
 │  └────────────┬────────────────────────────────────────────────────────┘     │
 │               │ invoke                                                       │
 │    ┌──────────┼──────────┬──────────────┬───────────────┐                    │
 │    ▼          ▼          ▼              ▼               ▼                    │
 │  Weather   Crop       Govt          Farmer          Image                   │
 │  Lookup    Advisory   Schemes       Profile         Analysis                │
 │  Lambda    Lambda     Lambda        Lambda          Lambda                  │
 │    │         │          │              │               │                     │
 │    ▼         ▼          ▼              ▼               ▼                     │
 │ OpenWeather Bedrock KB Curated      DynamoDB       Bedrock                  │
 │ API         (RAG)      JSON Data    (profiles)     Nova Pro Vision          │
 │                                                                              │
 │  + Transcribe Speech Lambda (Amazon Transcribe — voice-to-text fallback)     │
 │  + Health Check Lambda (inline — stack health)                               │
 └──────────────────────────────────────────────────────────────────────────────┘
```

### What Makes This Architecture Different

| Design Choice | Rationale |
|---|---|
| **Single orchestrator with tool-calling** | Amazon Bedrock Nova Pro decides which tools to invoke; no hard-coded routing — the model reasons about the farmer's intent |
| **Fact-checking & hallucination prevention** | Every AI response is grounded against real tool data; code-level policy + Bedrock Guardrails catch unsupported claims |
| **Cautious pest diagnosis** | The system never hard-asserts a single disease from symptoms alone — it lists probable causes and recommends confirmation |
| **Only the Reasoning layer has tools** | Principle of least privilege — translation, fact-checking, and communication are handled without tool access |
| **gTTS for Indic TTS** | Amazon Polly supports 2 Indian languages; gTTS covers all 13 for free, ensuring full voice coverage |
| **Web Speech API + Transcribe dual-path** | Chrome/Edge get zero-latency client-side recognition; Firefox/Safari fall back to Amazon Transcribe (12 Indian languages) |
| **Fully serverless on AWS** | Lambda + API Gateway + DynamoDB + S3 + CloudFront — zero server management, scales to zero, stays within free-tier for demos |

---

## AWS Services & How They're Used

| AWS Service | Purpose in This Project | Why This Service |
|---|---|---|
| **Amazon Bedrock** | Foundation model access (Nova Pro) for chat reasoning, tool-calling, and crop image diagnosis | Managed Gen AI — no model hosting, pay-per-use, supports tool-use natively |
| **Amazon Bedrock Knowledge Base** | RAG (Retrieval-Augmented Generation) over curated farming documents for crop advisories | Grounded answers from verified agricultural data instead of hallucinated responses |
| **Amazon Bedrock Guardrails** | Content filtering, topic gating, grounding checks | Enterprise-grade safety for farmer-facing AI |
| **AWS Lambda** | 7 serverless functions + 1 inline health check — all backend compute | Zero idle cost, auto-scaling, Python 3.13 runtime |
| **Amazon API Gateway** | REST API with 9 routes, CORS, regional deployment | Managed API layer with throttling and monitoring |
| **Amazon DynamoDB** | Farmer profiles, chat session history, rate-limit counters, OTP codes | Serverless NoSQL — millisecond latency, free-tier friendly |
| **Amazon S3** | Static frontend hosting, audio file storage, knowledge-base documents | Durable object storage integrated with CloudFront |
| **Amazon CloudFront** | CDN for the React frontend — low-latency delivery across India | Edge locations in Mumbai, Chennai, Bangalore, Delhi |
| **Amazon Translate** | Auto-detect language and translate between English and 13 Indian languages | Native support for Indian languages with auto-detection |
| **Amazon Polly** | Text-to-speech for English and Hindi responses | Neural voices (Kajal for Hindi, Joanna for English) |
| **Amazon Transcribe** | Speech-to-text fallback for Firefox/Safari users in 12 Indian languages | Covers browsers where Web Speech API is unavailable |
| **Amazon Cognito** | User authentication for farmer profile management | Managed auth with phone-number-based OTP |
| **Amazon SNS** | OTP delivery via SMS for farmer sign-up / profile verification | Reliable SMS delivery across Indian carriers |
| **AWS IAM** | Least-privilege policies for every Lambda function | Security best practice — each function only accesses what it needs |
| **Amazon CloudWatch** | Logging, metrics, and alarms for all Lambda functions | Operational visibility and debugging |

---

## Generative AI on AWS — Deep Dive

### Foundation Model: Amazon Nova Pro (`apac.amazon.nova-pro-v1:0`)

We use **Amazon Nova Pro** via the **Amazon Bedrock Converse API** for:

1. **Conversational reasoning** — The orchestrator sends the farmer's query along with tool definitions; Nova Pro decides which tools to call, interprets the results, and composes a natural-language advisory.

2. **Tool-use (function calling)** — Nova Pro receives 6 tool schemas (weather, crop, pest, schemes, irrigation, profile) and autonomously decides which to invoke based on intent. The orchestrator executes the tool, feeds results back, and the model synthesises a final answer.

3. **Crop disease vision** — When a farmer uploads a photo, Nova Pro Vision analyses the image and returns a structured diagnosis (disease name, confidence, severity, treatment steps).

4. **Multilingual output** — Nova Pro generates responses in English; Amazon Translate converts to/from the farmer's language. The model's system prompt includes India-specific agricultural context (Kharif/Rabi seasons, local crop varieties, Indian government schemes).

### Fallback Model: Amazon Nova Lite (`global.amazon.nova-2-lite-v1:0`)

If Nova Pro hits a throttle or timeout, the system automatically retries with Nova Lite for faster, cost-efficient responses.

### RAG with Bedrock Knowledge Base

Crop advisory queries are augmented with a **Bedrock Knowledge Base** containing curated Indian agricultural documents (crop calendars, soil maps, best practices). This ensures recommendations are grounded in verified data rather than model priors.

### Bedrock Guardrails

An optional Bedrock Guardrail layer provides:
- **Topic gating** — blocks non-agricultural queries
- **Grounding checks** — ensures responses are supported by tool data
- **Content filtering** — prevents harmful or irrelevant content

### Value the AI Layer Adds

| Without AI | With AI |
|---|---|
| Farmer must search multiple websites in English | Ask one question in their language, get a complete answer |
| Generic crop advice (same for everyone) | Personalised to farmer's location, soil, crops, and season |
| No disease diagnosis without a lab visit | Upload a photo → instant AI diagnosis with treatment plan |
| Government scheme PDFs are dense and confusing | AI explains eligibility, benefits, and step-by-step application |
| No after-hours help | 24/7 availability, zero cost to the farmer |

---

## Supported Languages

| # | Language | Script | Voice In | Voice Out |
|---|---|---|---|---|
| 1 | English | Latin | ✅ Web Speech | ✅ Amazon Polly |
| 2 | Hindi | Devanagari | ✅ Web Speech | ✅ Amazon Polly (Kajal) |
| 3 | Tamil | Tamil | ✅ Web Speech / Transcribe | ✅ gTTS |
| 4 | Telugu | Telugu | ✅ Web Speech / Transcribe | ✅ gTTS |
| 5 | Kannada | Kannada | ✅ Web Speech / Transcribe | ✅ gTTS |
| 6 | Malayalam | Malayalam | ✅ Web Speech / Transcribe | ✅ gTTS |
| 7 | Bengali | Bengali | ✅ Web Speech / Transcribe | ✅ gTTS |
| 8 | Marathi | Devanagari | ✅ Web Speech / Transcribe | ✅ gTTS |
| 9 | Gujarati | Gujarati | ✅ Web Speech / Transcribe | ✅ gTTS |
| 10 | Punjabi | Gurmukhi | ✅ Web Speech / Transcribe | ✅ gTTS |
| 11 | Odia | Odia | ✅ Web Speech / Transcribe | ✅ gTTS |
| 12 | Assamese | Bengali | ✅ Web Speech / Transcribe | ✅ gTTS |
| 13 | Urdu | Nastaliq | ✅ Web Speech / Transcribe | ✅ gTTS |

---

## Live Prototype

| Resource | URL |
|---|---|
| **Frontend (CloudFront)** | [https://d80ytlzsrax1n.cloudfront.net](https://d80ytlzsrax1n.cloudfront.net) |
| **API Gateway** | `https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/` |
| **Health Check** | [/health](https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/health) |

> Evaluators can open the CloudFront URL on any modern browser (Chrome recommended for voice input). No installation required.

---

## Demo Walkthrough

> 🎬 **Full demo video:** [Watch on YouTube](#) <!-- TODO: replace with actual link -->

### Scene 1 — Dashboard (15 s)
Open the app → localised dashboard with daily farming tip, season indicator (Rabi/Kharif), quick-action cards.

### Scene 2 — AI Chat in English (30 s)
Type: *"What is the weather in Chennai for the next 3 days?"*  
→ AI calls `get_weather` tool → real OpenWeather data → temperature, humidity, forecast + farming advisory → audio playback.

### Scene 3 — Voice Input in Tamil (30 s)
Switch to Tamil → click 🎤 → speak: *"நெல் பயிரில் பழுப்பு நிற புள்ளிகள் தெரிகிறது"*  
→ Transcribed → AI pest diagnosis in Tamil → Tamil audio response.

### Scene 4 — Crop Doctor (30 s)
Upload a diseased leaf photo → select crop (Rice) and state (Tamil Nadu) → AI returns disease name, severity, and treatment steps.

### Scene 5 — Government Schemes (20 s)
Browse PM-KISAN, PMFBY, Soil Health Card → eligibility, ₹6,000/year benefit, application steps.

### Scene 6 — Farmer Profile (15 s)
Save name, district, crops, soil type → future chat responses automatically personalised.

### Scene 7 — Multilingual (20 s)
Switch to Telugu → entire UI and chat switch to Telugu with Telugu audio output.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, React Router, React-Leaflet, DOMPurify, Marked |
| **Backend** | Python 3.13, AWS Lambda (7 functions), boto3 |
| **AI / Gen AI** | Amazon Bedrock (Nova Pro + Nova Lite), Bedrock Knowledge Base, Bedrock Guardrails |
| **API** | Amazon API Gateway (REST, 9 routes, CORS) |
| **Database** | Amazon DynamoDB (farmer profiles, chat sessions, rate limits) |
| **Storage** | Amazon S3 (audio, KB docs), Amazon CloudFront (CDN) |
| **Translation** | Amazon Translate (13 Indian languages, auto-detect) |
| **Voice** | Amazon Polly, gTTS, Web Speech API, Amazon Transcribe |
| **Auth** | Amazon Cognito, SNS (OTP) |
| **Infra-as-Code** | AWS SAM (CloudFormation) |
| **Region** | ap-south-1 (Mumbai) — lowest latency for Indian users |

---

## Project Structure

```
smart-rural-ai-advisor/
├── frontend/                        # React 18 + Vite SPA
│   ├── src/
│   │   ├── pages/                   # ChatPage, WeatherPage, CropDoctorPage,
│   │   │                            #   SchemesPage, ProfilePage, DashboardPage
│   │   ├── components/              # Sidebar, VoiceInput, ChatMessage, SkeletonLoader
│   │   ├── hooks/                   # useSpeechRecognition (Web Speech + Transcribe)
│   │   ├── contexts/                # LanguageContext (13 languages)
│   │   ├── i18n/                    # translations.js (13 language packs)
│   │   └── services/                # API helpers
│   └── index.html
│
├── backend/
│   ├── lambdas/
│   │   ├── agent_orchestrator/      # Main AI orchestrator — tool-calling, translation, TTS
│   │   ├── weather_lookup/          # OpenWeather API integration
│   │   ├── crop_advisory/           # Crop recommendation engine (Bedrock KB / RAG)
│   │   ├── govt_schemes/            # Government scheme search
│   │   ├── farmer_profile/          # DynamoDB profile CRUD + OTP auth
│   │   ├── image_analysis/          # Crop disease diagnosis (Nova Pro Vision)
│   │   └── transcribe_speech/       # Amazon Transcribe STT
│   └── utils/                       # Shared helpers (response, translate, polly, dynamo, error)
│
├── infrastructure/
│   ├── template.yaml                # AWS SAM template (all resources)
│   ├── samconfig.toml               # SAM deployment config
│   └── deploy.sh                    # One-click deployment script
│
├── data/
│   ├── crop_data.csv                # Indian crop database (seasons, soil, regions)
│   ├── govt_schemes.json            # 10+ government schemes with eligibility
│   └── knowledge_base/              # RAG documents for Bedrock KB
│
├── agentcore/
│   └── agent.py                     # Bedrock AgentCore runtime definitions
│
├── architecture/
│   └── architecture.md              # Detailed architecture documentation
│
├── docs/
│   ├── COMPLETE_SYSTEM_GUIDE.md     # Full technical deep-dive
│   ├── PROBLEM_STATEMENT.md         # Problem statement
│   ├── PROJECT_SUMMARY.md           # Project summary
│   └── Detailed_Implementation_Guide.md
│
└── demo/
    └── demo_video_link.md           # Demo video URL and walkthrough script
```

---

## Local Development

### Prerequisites

- **Node.js 18+** (frontend)
- **Python 3.11+** (Lambda development)
- **AWS CLI** configured with `ap-south-1` credentials
- **AWS SAM CLI** (for infrastructure deployment)

### Run Frontend Locally

```bash
cd frontend
npm install
npm run dev          # Opens http://localhost:5173
```

The frontend is pre-configured to call the live API Gateway endpoint. No `.env` changes needed for testing.

### Deploy Full Stack (SAM)

Set secrets in your shell (never commit secrets in config files):

```bash
export OPENWEATHER_API_KEY='<your-real-key>'
```

```bash
bash infrastructure/deploy.sh
```

### Deploy Full Stack (Windows / CloudFormation)

```powershell
$env:OPENWEATHER_API_KEY = "<your-real-key>"
./infrastructure/deploy_cfn.ps1
```

### Deploy Individual Lambda

```bash
python _deploy_fixes.py --only orchestrator   # Deploy orchestrator only
```

---

## API Reference

| Method | Endpoint | Lambda | Description |
|---|---|---|---|
| `POST` | `/chat` | AgentOrchestrator | AI chat — text in, text + audio out |
| `POST` | `/voice` | AgentOrchestrator | Voice-optimised chat |
| `POST` | `/image-analyze` | ImageAnalysis | Crop photo → disease diagnosis |
| `POST` | `/transcribe` | TranscribeSpeech | Audio → text (Amazon Transcribe) |
| `GET` | `/weather/{location}` | WeatherLookup | Real-time weather + forecast |
| `GET` | `/schemes` | GovtSchemes | Government scheme directory |
| `GET/PUT/DELETE` | `/profile/{farmerId}` | FarmerProfile | Farmer profile CRUD |
| `POST` | `/otp/send` | FarmerProfile | Send OTP for phone verification |
| `POST` | `/otp/verify` | FarmerProfile | Verify OTP |
| `GET` | `/health` | HealthCheck (inline) | Stack health check |

Base URL: `https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod`

---

## Impact & Metrics

| Metric | Target |
|---|---|
| Reduce crop loss from undiagnosed diseases | **30 %** — instant AI diagnosis from photo or symptom description |
| Increase government scheme enrolment | **50 %** — AI explains eligibility and application steps in the farmer's language |
| 24/7 expert-level agricultural advice | **Zero cost** to the farmer — fully serverless, within AWS free-tier for moderate usage |
| Language accessibility | **13 Indian languages** — covers 95 %+ of India's farming population |
| Voice accessibility | **Full voice I/O** — usable by farmers who cannot read or type comfortably |

---

## Team

| Name | Role | Contribution |
|---|---|---|
| **Sanjay M** | Team Lead + Frontend | React UI, all pages, voice components, i18n, CSS, CloudFront deployment |
| **Manoj RS** | Backend + Infrastructure | 7 Lambda functions, SAM template, Bedrock integration, API Gateway, Polly/Translate |
| **Abhishek Reddy** | Data + Knowledge Base | Crop data curation, government schemes, Bedrock KB documents, S3 upload |
| **Jeevidha R** | QA + Documentation | End-to-end testing, documentation, demo video, project submission |

---

## Submission Checklist

| Deliverable | Status | Link |
|---|---|---|
| **Project PPT** | 📋 Ready | *Uploaded to dashboard* |
| **GitHub Repository** | ✅ Public | [github.com/Manoj-777/smart-rural-ai-advisor](https://github.com/Manoj-777/smart-rural-ai-advisor) |
| **Working Prototype** | ✅ Live | [https://d80ytlzsrax1n.cloudfront.net](https://d80ytlzsrax1n.cloudfront.net) |
| **Demo Video** | 🎬 Ready | [Watch on YouTube](#) <!-- TODO: replace with actual link --> |
| **Project Summary** | ✅ Complete | See [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) |

---

<p align="center">
  Built with ❤️ for Bharat's farmers — <strong>AWS AI for Bharat Hackathon 2026</strong>
</p>
