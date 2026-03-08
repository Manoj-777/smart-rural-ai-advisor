# Project Summary

## Smart Rural AI Advisor

**Team:** Creative Intelligence (CI)  
**Hackathon:** AWS AI for Bharat  
**Deadline:** March 4, 2026, 11:59 PM IST

### What It Does

An AI-powered agricultural advisor that helps Indian farmers with crop guidance, disease diagnosis, weather advisories, and government scheme navigation — all in their native language (Tamil, Hindi, Telugu, English) via voice or text.

### Key Features

| Feature | How It Works |
| --- | --- |
| **AI Chat** | Amazon Nova Pro via Bedrock with tool-calling + RAG knowledge base |
| **Voice I/O** | Web Speech API + Amazon Polly (TTS) + Transcribe fallback |
| **Crop Doctor** | Upload photo → Amazon Nova Pro Vision → disease diagnosis + treatment |
| **Weather** | OpenWeatherMap API → farming-specific advisories |
| **Govt Schemes** | Knowledge base of 9+ schemes with eligibility matching |
| **Farmer Profile** | DynamoDB storage for personalized recommendations |
| **Multilingual** | Amazon Translate (en ↔ hi ↔ ta ↔ te ↔ kn) |

### Tech Stack

- **AI**: Amazon Bedrock (Nova Pro + Nova Lite) + Knowledge Bases
- **Backend**: 7 AWS Lambda functions + API Gateway (REST)
- **Frontend**: React 18 + Vite (S3 + CloudFront)
- **Database**: DynamoDB (profiles + chat sessions)
- **Voice**: Web Speech API (primary) + Amazon Transcribe (fallback)
- **Region**: ap-south-1 (Mumbai)

### Team

| Name | Role | Track |
| --- | --- | --- |
| Sanjay M | Team Lead + Frontend | React UI, components, pages |
| Manoj RS | Backend + Infrastructure | Lambdas, SAM, Bedrock, API Gateway |
| Abhishek Reddy | Data + Knowledge Base | Crop data, scheme data, KB documents |
| Jeevidha R | QA + Documentation | Testing, README, demo video |

### Repository Structure

```text
smart-rural-ai-advisor/
├── infrastructure/        # SAM template + deploy scripts
├── backend/lambdas/       # 7 Lambda functions
├── backend/utils/         # Shared helpers
├── frontend/src/          # React app (5 pages, 3 components)
├── docs/                  # Submission docs + architecture diagram
└── archive/               # Local archival backup (gitignored)
```
