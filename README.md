# Smart Rural AI Advisor 🌾

> AI-powered agricultural advisory system for Indian farmers — voice-first, multilingual, explainable.

**Team:** Creative Intelligence (CI)  
**Hackathon:** AWS AI for Bharat 2026  
**Live URL:** _[To be added after deployment]_  
**Demo Video:** _[To be added]_

---

## What It Does

Smart Rural AI Advisor helps Indian farmers get personalized, explainable farming advice through a conversational AI interface. Farmers can speak in **Tamil, English, Telugu, or Hindi** — the AI understands, reasons through multiple data sources, and responds in the same language with voice output.

### Features
- 🌾 AI Crop Planning — soil + season + region-aware recommendations
- 🐛 Pest & Disease Alerts — symptom detection + treatment advice
- 💧 Smart Irrigation — weather-aware water management
- 🏛️ Government Schemes — eligibility check + application steps
- 📸 Crop Doctor — upload photo → AI diagnoses disease (Claude Vision)
- 🗣️ Voice Input/Output — speak naturally, hear advice back
- 🌐 Auto Language Detection — Tamil, English, Telugu, Hindi
- 🧠 Explainable AI — every recommendation includes "why"

---

## Architecture

<!-- TODO: Add architecture_diagram.png -->

| Layer | Service |
|---|---|
| Frontend | React + Vite (S3 + CloudFront) |
| API | Amazon API Gateway |
| Compute | AWS Lambda (7 functions) |
| AI | Amazon Bedrock AgentCore + Claude Sonnet 4.5 |
| Knowledge | Bedrock Knowledge Base (RAG over curated farming data) |
| Database | Amazon DynamoDB |
| Voice | Amazon Polly (output) + Web Speech API (input) |
| Translation | Amazon Translate |
| Storage | Amazon S3 |

---

## Setup Instructions

### Prerequisites
- AWS account with $100 credits
- Node.js 18+ (for frontend)
- Python 3.11+ (for Lambda development)
- AWS CLI + SAM CLI installed

### Backend
```bash
cd infrastructure
sam build
sam deploy --guided
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # Fill in your API Gateway URL
npm run dev            # Local development
npm run build          # Production build → deploy dist/ to S3
```

---

## Team

| Name | Role |
|---|---|
| Sanjay M | Team Lead + Frontend |
| Manoj RS | Backend + Infrastructure |
| Abhishek Reddy | Data Curator + Knowledge Base |
| Jeevidha R | QA + Documentation |

---

## License

Built for AWS AI for Bharat Hackathon 2026.
