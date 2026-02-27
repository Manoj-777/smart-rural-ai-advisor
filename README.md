# Smart Rural AI Advisor 🌾

> AI-powered agricultural advisory system for Indian farmers — voice-first, multilingual, 13 Indian languages, explainable.

**Team:** Creative Intelligence (CI)  
**Hackathon:** AWS AI for Bharat 2026  
**Region:** ap-south-1 (Mumbai)  
**API Gateway:** `https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod`  
**Frontend:** Run `cd frontend && npm run dev` → opens at http://localhost:5173

---

## What It Does

Smart Rural AI Advisor helps Indian farmers get personalized, explainable farming advice through a conversational AI interface. Farmers can speak or type in **13 Indian languages** — the AI understands, calls specialized tools for real data, and responds in the same language with voice output.

### Key Features

| Feature | What It Does | How It Works |
|---|---|---|
| 💬 **AI Chat** | Conversational farming advisor | Claude Sonnet 4.5 via Bedrock AgentCore with tool-use |
| 🌤️ **Weather** | Real-time weather + 5-day forecast + farming advisory | OpenWeather API via Lambda |
| 🌾 **Crop Advisory** | Season/soil/region-aware crop recommendations | Curated Indian crop database |
| 🐛 **Pest & Disease** | Symptom detection + organic & chemical treatments | Disease database + AI reasoning |
| 📋 **Govt Schemes** | Eligibility, benefits, application steps for 10+ schemes | PM-KISAN, PMFBY, Soil Health Card, etc. |
| 📸 **Crop Doctor** | Upload leaf/crop photo → AI diagnoses disease | Claude Sonnet 4.5 Vision |
| 👤 **Farmer Profile** | Save farm details for personalized advice | DynamoDB-backed persistence |
| 🎤 **Voice Input** | Speak in any language → text | Web Speech API + Amazon Transcribe fallback |
| 🔊 **Voice Output** | Hear AI responses spoken aloud | Amazon Polly (en/hi) + gTTS (all Indic) |
| 🌐 **13 Languages** | Tamil, Hindi, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, Urdu, English | Amazon Translate + script detection |

### Supported Languages
Tamil • Hindi • Telugu • Kannada • Malayalam • Bengali • Marathi • Gujarati • Punjabi • Odia • Assamese • Urdu • English

---

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────────────────────────┐
│   React UI  │───▶│ API Gateway  │───▶│  Lambda Orchestrator             │
│  (Vite SPA) │    │  9 routes    │    │  ├─ Intent classification        │
│  13 langs   │    │  CORS-enabled│    │  ├─ Policy & hallucination guard │
└─────────────┘    └──────────────┘    │  ├─ AgentCore (Claude 4.5)       │
                                       │  ├─ Translate (13 languages)     │
                                       │  └─ TTS (Polly + gTTS)          │
                                       └────────────┬─────────────────────┘
                                                    │ Tools
                              ┌──────────┬──────────┼──────────┬──────────┐
                              ▼          ▼          ▼          ▼          ▼
                         get_weather  get_crop  get_pest  search_   get_farmer
                         (OpenWeather) advisory   alert   schemes   profile
                              │          │          │          │          │
                              ▼          ▼          ▼          ▼          ▼
                         OpenWeather  crop_data  disease   govt_     DynamoDB
                           API        .csv       DB       schemes
                                                          .json
```

| Layer | Service |
|---|---|
| **Frontend** | React 18 + Vite + React Router (13 language i18n) |
| **API** | Amazon API Gateway (9 endpoints, CORS) |
| **Compute** | 7 AWS Lambda functions + 1 inline health check |
| **AI Model** | Claude Sonnet 4.5 (`anthropic.claude-sonnet-4-5-20250929-v1:0`) |
| **AI Runtime** | Amazon Bedrock AgentCore (6 specialist runtimes) |
| **Knowledge** | Bedrock Knowledge Base (RAG over curated farming docs) |
| **Database** | Amazon DynamoDB (farmer profiles + chat sessions) |
| **Voice In** | Web Speech API (Chrome) + Amazon Transcribe (Firefox, 12 languages) |
| **Voice Out** | Amazon Polly (en/hi) + gTTS (ta/te/kn/ml/mr/bn/gu/pa/or/as/ur) |
| **Translation** | Amazon Translate (auto-detect, 13 Indian languages) |
| **Storage** | Amazon S3 (audio files, KB documents) |

---

## Quick Start

### Prerequisites
- AWS CLI configured with ap-south-1 credentials
- Node.js 18+ (frontend)
- Python 3.11+ (Lambda development)

### Run Frontend Locally
```bash
cd frontend
npm install
npm run dev          # Opens http://localhost:5173
```

The frontend is pre-configured to use the live API Gateway endpoint. No `.env` changes needed.

### Deploy Backend (SAM)
```bash
cd infrastructure
sam build
sam deploy --guided   # Stack name: smart-rural-ai
```

### Deploy Orchestrator Lambda (Direct)
```bash
python _deploy_orchestrator.py   # Bundles gTTS + handler → deploys to Lambda
```

---

## API Endpoints

| Method | Path | Lambda | Description |
|---|---|---|---|
| POST | `/chat` | AgentOrchestratorFunction | Main AI chat (text + voice response) |
| POST | `/voice` | AgentOrchestratorFunction | Same as /chat, voice-optimized |
| POST | `/image-analyze` | ImageAnalysisFunction | Crop disease photo diagnosis |
| POST | `/transcribe` | TranscribeSpeechFunction | Speech-to-text (Transcribe) |
| GET | `/weather/{location}` | WeatherLookupFunction | Weather + farming advisory |
| GET | `/schemes` | GovtSchemesFunction | Government scheme directory |
| GET/PUT | `/profile/{farmerId}` | FarmerProfileFunction | Read/update farmer profile |
| GET | `/health` | Inline | Stack health check |

---

## Demo Script (2-3 minutes)

### Scene 1: Dashboard (15s)
- Open app → show localized dashboard with daily farming tip
- Point out season indicator, quick action cards, helpline info

### Scene 2: Chat in English (30s)
- Type: **"What is the weather in Chennai for next 3 days?"**
- Show: Real weather data response with temperature, humidity, forecast
- Click audio player → hear response spoken aloud

### Scene 3: Voice Input in Tamil (30s)
- Switch language to **Tamil (தமிழ்)**
- Click 🎤 mic button → speak: **"நெல் பயிரில் பழுப்பு நிற புள்ளிகள் தெரிகிறது"**
- Show: Tamil transcription → AI pest diagnosis in Tamil → Tamil audio

### Scene 4: Crop Doctor (30s)
- Navigate to **📸 Crop Doctor**
- Upload a photo of a diseased leaf
- Select crop: Rice, State: Tamil Nadu
- Click Analyze → show AI diagnosis with disease name, severity, treatments

### Scene 5: Government Schemes (20s)
- Navigate to **📋 Schemes**
- Browse PM-KISAN, PMFBY, Soil Health Card
- Show eligibility, benefit amount (₹6,000/year), application steps

### Scene 6: Farmer Profile (15s)
- Navigate to **👤 Profile**
- Fill: Name, District, Crops (Rice, Banana), Soil type
- Save → show profile summary
- Mention: Chat responses will now be personalized to this profile

### Scene 7: Multilingual (20s)
- Switch sidebar language to **Telugu (తెలుగు)**
- Entire UI switches to Telugu
- Type a question → response comes in Telugu with Telugu audio

---

## Project Structure

```
smart-rural-ai-advisor/
├── frontend/               # React + Vite SPA
│   ├── src/
│   │   ├── pages/          # ChatPage, WeatherPage, CropDoctorPage, etc.
│   │   ├── components/     # Sidebar, VoiceInput, ChatMessage, SkeletonLoader
│   │   ├── hooks/          # useSpeechRecognition (Web Speech + Transcribe)
│   │   ├── contexts/       # LanguageContext (13 languages)
│   │   ├── i18n/           # translations.js (13 language packs)
│   │   └── services/       # mockApi.js (demo mode)
│   └── dist/               # Production build
├── backend/
│   └── lambdas/
│       ├── agent_orchestrator/  # Main AI orchestrator (666 lines)
│       ├── weather_lookup/      # OpenWeather integration
│       ├── crop_advisory/       # Crop recommendation engine
│       ├── govt_schemes/        # Scheme eligibility + search
│       ├── farmer_profile/      # DynamoDB profile CRUD
│       ├── image_analysis/      # Claude Vision crop diagnosis
│       └── transcribe_speech/   # Amazon Transcribe STT
├── agentcore/              # Bedrock AgentCore runtime
│   └── agent.py            # Tool execution + model interaction
├── infrastructure/
│   └── template.yaml       # SAM template (all resources)
├── data/
│   ├── crop_data.csv       # Indian crop database
│   ├── govt_schemes.json   # Government scheme details
│   └── knowledge_base/     # RAG documents
└── docs/                   # System guide, implementation guide
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Claude Sonnet 4.5** over Nova Pro | Superior tool-use, multilingual quality, vision capability |
| **gTTS** for Indic TTS (free) | Amazon Polly only supports 2 Indian languages; gTTS covers all 13 for free |
| **Web Speech API** primary STT | Zero-latency client-side recognition in Chrome/Edge (80%+ of users) |
| **Amazon Transcribe** fallback | Firefox/Safari users get server-side STT with 12 Indian languages |
| **AgentCore** for orchestration | Managed tool-calling loop, session memory, model fallback |
| **Intent classification** | Route to specialist tools before AI, reducing hallucination |
| **Policy guard** | Double-layer: code-level topic gate + grounding requirement |

---

## Team

| Name | Role |
|---|---|
| Sanjay M | Team Lead + Frontend |
| Manoj RS | Backend + Infrastructure |
| Abhishek Reddy | Data Curator + Knowledge Base |
| Jeevidha R | QA + Documentation |

---

## AWS Services Used

Amazon Bedrock (Claude Sonnet 4.5) • Bedrock AgentCore • Bedrock Knowledge Base • API Gateway • Lambda • DynamoDB • S3 • Translate • Polly • Transcribe • IAM • CloudWatch

---

*Built for AWS AI for Bharat Hackathon 2026*
