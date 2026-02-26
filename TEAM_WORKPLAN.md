# TEAM WORKPLAN — Smart Rural AI Advisor

> **Read this first.** This document tells you exactly what to do, which files are yours, and how to move forward. No guesswork.

**Repo:** https://github.com/Manoj-777/smart-rural-ai-advisor  
**Hackathon:** AWS AI for Bharat 2026  
**Deadline:** March 4, 2026 at 11:59 PM IST  
**Budget:** $100 AWS credits  
**Region:** ap-south-1 (Mumbai)

---

## Team & Authority

| Name | Role | Track | Days Most Active |
|------|------|-------|------------------|
| **Sanjay M** | Team Lead + Frontend | React UI, all 5 pages, voice, CSS, frontend deployment | All days |
| **Manoj RS** | Backend + Infrastructure | 7 Lambda functions, SAM template, Bedrock AgentCore, API Gateway, Polly/Translate | Day 1–4 |
| **Abhishek Reddy** | Data Curator / KB Specialist | Knowledge Base documents, crop_data.csv, govt_schemes.json, S3 upload, Bedrock KB setup | Day 1–2 (critical path) |
| **Jeevidha R** | QA + Documentation Lead | Testing all endpoints, bug logging, README polish, Project Summary, screenshots, demo video operation | Day 1 + Day 3–6 |

### Authority Structure

- **Sanjay + Manoj have EQUAL authority.** Sanjay owns frontend decisions, Manoj owns backend decisions. Architecture and final decisions are joint. "Team Lead" is the official hackathon title (Sanjay submitted the idea), not a hierarchy.
- Both Sanjay and Manoj approve final deliverables before submission.
- Use the Team's group for real-time updates: `"Backend Lambda #3 done ✅"`, `"Frontend weather page blocked — need API Gateway URL"`

---

## How to Clone & Set Up

### Step 1: Clone the repo

```bash
git clone https://github.com/Manoj-777/smart-rural-ai-advisor.git
cd smart-rural-ai-advisor
```

### Step 2: Understand the folder structure

```
smart-rural-ai-advisor/
├── .env.example                    ← Copy to .env, fill your values
├── .gitignore                      ← Already configured, don't edit
├── README.md                       ← Project README (Jeevidha polishes)
│
├── architecture/
│   └── architecture.md             ← System design overview
│
├── infrastructure/
│   ├── template.yaml               ← SAM template — ALL AWS resources
│   ├── deploy.sh                   ← Build + deploy script
│   └── bedrock_agentcore_config.json ← Bedrock Agent config reference
│
├── backend/
│   ├── requirements.txt            ← Python dependencies
│   ├── lambdas/
│   │   ├── agent_orchestrator/handler.py   ← POST /chat + POST /voice
│   │   ├── crop_advisory/handler.py        ← AgentCore tool (called by agent)
│   │   ├── weather_lookup/handler.py       ← GET /weather/{location}
│   │   ├── govt_schemes/handler.py         ← GET /schemes
│   │   ├── image_analysis/handler.py       ← POST /image-analyze
│   │   ├── farmer_profile/handler.py       ← GET+PUT /profile/{farmerId}
│   │   └── transcribe_speech/handler.py    ← POST /transcribe
│   └── utils/
│       ├── response_helper.py      ← ✅ DONE — standard API response envelope
│       ├── error_handler.py        ← Error decorator for Lambda handlers
│       ├── dynamodb_helper.py      ← DynamoDB read/write operations
│       ├── polly_helper.py         ← Text-to-speech helper
│       └── translate_helper.py     ← Language detection + translation
│
├── frontend/
│   ├── package.json                ← npm install dependencies
│   ├── vite.config.js              ← Vite bundler config
│   ├── index.html                  ← HTML entry point
│   ├── .env.example                ← Frontend env vars (VITE_API_URL)
│   └── src/
│       ├── main.jsx                ← React entry point
│       ├── App.jsx                 ← Router + layout
│       ├── App.css                 ← Full CSS (sidebar, chat, cards, mic)
│       ├── config.js               ← API URL + language config
│       ├── components/
│       │   ├── Sidebar.jsx         ← Navigation sidebar
│       │   ├── ChatMessage.jsx     ← Chat bubble component
│       │   └── VoiceInput.jsx      ← Mic button + recording UI
│       ├── hooks/
│       │   └── useSpeechRecognition.js  ← Web Speech API + Transcribe fallback
│       └── pages/
│           ├── ChatPage.jsx        ← 💬 Main chat with voice
│           ├── WeatherPage.jsx     ← 🌤️ Weather dashboard
│           ├── SchemesPage.jsx     ← 📋 Govt schemes browser
│           ├── CropDoctorPage.jsx  ← 📸 Image upload + AI diagnosis
│           └── ProfilePage.jsx     ← 👤 Farmer profile form
│
├── data/
│   ├── crop_data.csv               ← 20 crops × 21 columns (Abhishek fills)
│   ├── govt_schemes.json           ← 9 schemes structured data (Abhishek fills)
│   └── knowledge_base/             ← 6 KB docs for Bedrock RAG (Abhishek fills)
│       ├── crop_guide_india.md
│       ├── traditional_farming.md
│       ├── pest_patterns.md
│       ├── irrigation_guide.md
│       ├── govt_schemes.md
│       └── region_advisories.md
│
├── demo/
│   ├── demo_video_link.md          ← YouTube/Loom link (Jeevidha adds)
│   └── screenshots/                ← App screenshots (Jeevidha + Abhishek)
│
└── docs/
    ├── Detailed_Implementation_Guide.md  ← 📖 THE guide (9000+ lines, everything)
    ├── PROJECT_SUMMARY.md           ← Hackathon submission summary
    ├── PROBLEM_STATEMENT.md         ← Problem + impact statement
    └── Smart_Rural_AI_Advisor_Submission.md ← Original submission doc
```

### Step 3: Set up your environment

**Everyone:**
```bash
# Copy the env template
cp .env.example .env
# Fill in values as they become available (Manoj will share AWS keys/IDs)
```

**Sanjay (Frontend):**
```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL once Manoj deploys backend
npm run dev          # Starts local dev server at http://localhost:5173
```

**Manoj (Backend):**
```bash
pip install boto3 requests Pillow python-dotenv
aws configure        # Set region: ap-south-1
# Then implement Lambdas → sam build → sam deploy
```

**Abhishek (Data):**
```bash
# No code setup needed — you edit files in data/ folder
# Use VS Code or any text editor
# Reference: docs/Detailed_Implementation_Guide.md
```

**Jeevidha (QA):**
```bash
# Install Postman (https://www.postman.com/downloads/)
# Or use curl / Thunder Client VS Code extension
# You'll test endpoints once Manoj deploys
```

---

## Git Workflow — How to Push Your Changes

### Golden rules:
1. **Always pull before you work:** `git pull origin main`
2. **Commit often** with meaningful messages
3. **Only edit YOUR files** (see ownership table below)
4. **Never force push:** `git push` only (no `--force`)

### Daily workflow:

```bash
# 1. Start of day — get latest
git pull origin main

# 2. Do your work (edit files)

# 3. Stage your changes
git add -A

# 4. Commit with clear message
git commit -m "Sanjay: ChatPage connected to /chat API"
# or
git commit -m "Abhishek: Completed crop_guide_india.md — all 20 crops filled"
# or
git commit -m "Manoj: weather_lookup Lambda implemented + tested"
# or
git commit -m "Jeevidha: Added screenshots for chat and weather pages"

# 5. Push
git push origin main
```

### If you get a merge conflict:
1. Don't panic — this means two people edited the same file
2. Git will show `<<<<<<<` markers in the file
3. Call Manoj or Sanjay on WhatsApp — they'll resolve it in 2 minutes
4. **Prevention:** Stick to your own files (see ownership table below)

---

## File Ownership — Who Edits What

> **Rule:** Only edit files in your column. If you need a change in someone else's file, message them on WhatsApp.

### Sanjay M (Frontend)

| File | What to Do | Status |
|------|-----------|--------|
| `frontend/src/pages/ChatPage.jsx` | Already has full code — connect to real API, test, polish | 📝 Ready to customize |
| `frontend/src/pages/WeatherPage.jsx` | Already has full code — connect to real API | 📝 Ready to customize |
| `frontend/src/pages/SchemesPage.jsx` | Already has full code — connect to real API | 📝 Ready to customize |
| `frontend/src/pages/CropDoctorPage.jsx` | Already has full code — connect to real API | 📝 Ready to customize |
| `frontend/src/pages/ProfilePage.jsx` | Already has full code — connect to real API | 📝 Ready to customize |
| `frontend/src/components/Sidebar.jsx` | Navigation — done, tweak if needed | ✅ Done |
| `frontend/src/components/ChatMessage.jsx` | Chat bubble — done, tweak if needed | ✅ Done |
| `frontend/src/components/VoiceInput.jsx` | Mic button — done, tweak if needed | ✅ Done |
| `frontend/src/hooks/useSpeechRecognition.js` | Voice hook — fully implemented | ✅ Done |
| `frontend/src/App.jsx` | Router — done | ✅ Done |
| `frontend/src/App.css` | Full CSS with sidebar, chat, cards, mic — customize as needed | ✅ Done |
| `frontend/src/config.js` | Update `VITE_API_URL` once Manoj gives you the API Gateway URL | ⏳ Waiting |
| `frontend/package.json` | Add packages if needed (e.g., `npm install axios`) | 📝 Ready |

**Sanjay's workflow:**
1. **Day 1:** Run `npm install` + `npm run dev`. All 5 pages load with static/empty data. Explore the code.
2. **Day 1–2:** Build with **mock data** — hardcode sample API responses to test UI without backend.
3. **Day 3:** Manoj shares `API_URL` → update `frontend/.env` → connect all pages to real API.
4. **Day 4:** Deploy frontend to S3 + CloudFront (or App Runner). Test on phone.
5. **Day 5–6:** Bug fixes, polish, responsive testing.

**How to run locally:**
```bash
cd frontend
npm install        # First time only
npm run dev        # Opens http://localhost:5173
```

**How to use mock data while backend isn't ready:**
In any page (e.g., `ChatPage.jsx`), temporarily replace the API call:
```jsx
// TEMPORARY — remove when real API is ready
const mockReply = {
    status: 'success',
    data: { reply: 'Mock: Plant rice in June for Tamil Nadu Kharif season.' }
};
// Use mockReply instead of actual fetch response
```

---

### Manoj RS (Backend + Infrastructure)

| File | What to Do | Status |
|------|-----------|--------|
| `backend/lambdas/agent_orchestrator/handler.py` | Implement: receive message → Bedrock AgentCore → translate → Polly → return | 🔴 TODO |
| `backend/lambdas/crop_advisory/handler.py` | Implement: AgentCore tool — crop advisory + pest alert + irrigation | 🔴 TODO |
| `backend/lambdas/weather_lookup/handler.py` | Implement: OpenWeatherMap API call → format response | 🔴 TODO |
| `backend/lambdas/govt_schemes/handler.py` | Implement: load schemes from S3/JSON → search → return | 🔴 TODO |
| `backend/lambdas/image_analysis/handler.py` | Implement: base64 image → Bedrock Nova Lite → diagnosis | 🔴 TODO |
| `backend/lambdas/farmer_profile/handler.py` | Implement: GET/PUT farmer profile in DynamoDB | 🔴 TODO |
| `backend/lambdas/transcribe_speech/handler.py` | Implement: audio → S3 → Amazon Transcribe → text | 🔴 TODO |
| `backend/utils/response_helper.py` | Standard response envelope — **already done** | ✅ Done |
| `backend/utils/error_handler.py` | Error decorator — has skeleton, flesh out | 🟡 Skeleton |
| `backend/utils/dynamodb_helper.py` | DynamoDB CRUD — has skeleton, implement functions | 🟡 Skeleton |
| `backend/utils/polly_helper.py` | Polly TTS — has skeleton, implement | 🟡 Skeleton |
| `backend/utils/translate_helper.py` | Translate — has skeleton, implement | 🟡 Skeleton |
| `infrastructure/template.yaml` | SAM template — **fully done**, deploy when ready | ✅ Done |
| `infrastructure/deploy.sh` | Deploy script — done | ✅ Done |
| `infrastructure/bedrock_agentcore_config.json` | Reference config — fill IDs after console setup | ⏳ After setup |

**Manoj's workflow:**
1. **Day 1:** AWS setup — IAM roles, create S3 bucket, DynamoDB tables. Implement `dynamodb_helper.py`, `translate_helper.py`, `polly_helper.py`. Start with `weather_lookup` Lambda (easiest — just OpenWeatherMap API call).
2. **Day 2:** Implement remaining Lambdas: `farmer_profile` → `govt_schemes` → `image_analysis` → `agent_orchestrator` → `transcribe_speech`. **Review Abhishek's KB docs by end of day.**
3. **Day 3:** Set up Bedrock AgentCore + Knowledge Base in AWS Console. Connect action groups to Lambdas. Run `sam build && sam deploy`. **Share API Gateway URL with Sanjay immediately.**
4. **Day 4:** Test all endpoints. Fix bugs reported by Jeevidha. Final deploy.

**Key reference:** `docs/Detailed_Implementation_Guide.md` — every Lambda has complete code in Sections 7–12. Copy the code from there and adapt.

**Build & deploy commands:**
```bash
cd C:\Users\RSManoj\Desktop\smart-rural-ai-advisor
sam build
sam deploy --guided    # First time (answers prompts)
sam build && sam deploy # Subsequent deploys
```

**After deploying, share these with the team:**
- API Gateway URL (e.g., `https://abc123.execute-api.ap-south-1.amazonaws.com/Prod/`)
- Bedrock Agent ID + Alias ID (for reference)

---

### Abhishek Reddy (Data Curator / Knowledge Base)

> **Your work is the critical path.** The AI is only as good as the data you write. Day 1–2 is your most important window.

| File | What to Do | Status |
|------|-----------|--------|
| `data/knowledge_base/crop_guide_india.md` | Fill ALL 20 crops (Rice is done as example) | 🔴 Fill template |
| `data/knowledge_base/traditional_farming.md` | Fill all 10 traditional farming topics | 🔴 Fill template |
| `data/knowledge_base/pest_patterns.md` | Fill all diseases + pests + seasonal calendar | 🔴 Fill template |
| `data/knowledge_base/irrigation_guide.md` | Fill water needs table + 5 irrigation methods | 🔴 Fill template |
| `data/knowledge_base/govt_schemes.md` | Fill all 9 schemes (PM-KISAN is done as example) | 🔴 Fill template |
| `data/knowledge_base/region_advisories.md` | Fill all 10 state advisories | 🔴 Fill template |
| `data/govt_schemes.json` | Fill all 9 scheme JSON objects (PM-KISAN is done) | 🔴 Fill template |
| `data/crop_data.csv` | Fill all 20 crop rows (Rice row is done) | 🔴 Fill template |

**Abhishek's workflow:**
1. **Day 1 (FULL DAY — most critical):**
   - Open each file in `data/knowledge_base/` — they already have templates with headers and structure
   - **Rice / PM-KISAN are filled as examples** — follow the exact same format for other entries
   - Start with: `crop_guide_india.md` → `pest_patterns.md` → `govt_schemes.md` (these 3 are highest impact)
   - Use Google, farmer.gov.in, ICAR publications, Wikipedia for accurate data
   - **Don't worry about perfection — accuracy > polish.** The AI uses this as context, not exact quotes.

2. **Day 1 END — CHECKPOINT:** Manoj reviews your KB docs (30 minutes). Fix any issues immediately.

3. **Day 2:**
   - Finish remaining docs: `traditional_farming.md`, `irrigation_guide.md`, `region_advisories.md`
   - Fill `govt_schemes.json` (structured data for the API)
   - Fill `crop_data.csv` (open in Excel/Google Sheets — fill all 20 rows)
   - Help Manoj upload files to S3 bucket

4. **Day 3+:** Help Jeevidha with testing. Take mobile screenshots for the demo.

**How to edit the templates:**

Each template file has a structure like this:
```markdown
## 2. Wheat (Triticum aestivum)
- **Seasons:** [Fill: e.g., Rabi (Oct–Mar)]
- **Soil type:** [Fill: e.g., Loamy, Clay loam]
- **Water needs:** [Fill: e.g., 4-6 irrigations, 450mm total]
...
```

Replace `[Fill: ...]` with actual data. Keep the markdown format intact.

**Where to find information:**
| Topic | Source |
|-------|--------|
| Crop data | ICAR crop guides, agrifarming.in, farmer.gov.in |
| Pest/disease | agrifarming.in, plantvillage.psu.edu, ICAR pest management guides |
| Government schemes | pmkisan.gov.in, pmfby.gov.in, mkisan.gov.in, farmer.gov.in |
| Traditional farming | nhm.nic.in, ZBNF references, Subhash Palekar ZBNF website |
| Regional advisories | State agriculture department websites, seasonal crop calendars |
| Irrigation | NABARD, CWC guidelines, state irrigation department sites |

**Quality checklist before committing:**
- [ ] Every `[Fill: ...]` placeholder is replaced with real data
- [ ] Numbers are realistic (don't say wheat needs 2000mm water — it needs 450mm)
- [ ] Government scheme amounts match official websites (PM-KISAN = ₹6,000/year, not ₹10,000)
- [ ] Each crop entry has ALL fields filled (no blank fields)
- [ ] Markdown formatting is preserved (headers, bullet points, tables)

---

### Jeevidha R (QA + Documentation Lead)

| File | What to Do | Status |
|------|-----------|--------|
| `README.md` | Polish: add architecture diagram link, update live URL, add setup details | 📝 Improve |
| `docs/PROJECT_SUMMARY.md` | Review and finalize for submission | 📝 Review |
| `docs/PROBLEM_STATEMENT.md` | Review and finalize for submission | 📝 Review |
| `demo/demo_video_link.md` | Add YouTube/Loom link after recording | ⏳ After recording |
| `demo/screenshots/` | Take screenshots of all 5 pages in working app | ⏳ After app works |

**Jeevidha's workflow:**

1. **Day 1:**
   - Read the full `docs/PROBLEM_STATEMENT.md` and `docs/PROJECT_SUMMARY.md` — suggest improvements
   - Install Postman (or Thunder Client for VS Code)
   - Prepare test scenarios (see test matrix below)
   - Help Abhishek cross-check some KB data for accuracy

2. **Day 2:**
   - Review Abhishek's completed KB docs for obvious errors / missing fields
   - Finalize PROBLEM_STATEMENT.md and PROJECT_SUMMARY.md wording

3. **Day 3–4 (Testing begins — Manoj deploys backend):**
   - Test every endpoint using Postman (see test matrix below)
   - Log bugs in WhatsApp group: `"BUG: /weather/Chennai returns 500 — screenshot attached"`
   - Retest after Manoj fixes

4. **Day 5:**
   - Full end-to-end testing on the live URL (frontend + backend together)
   - Test on mobile phone (Chrome Android)
   - Take screenshots of all 5 pages (save in `demo/screenshots/`)
   - Test edge cases: empty input, very long message, non-existent city, wrong image format

5. **Day 6:**
   - Help record demo video (Sanjay narrates, Jeevidha operates the app)
   - Final README polish
   - Submit all 5 deliverables before deadline

**Test Matrix — What to Test:**

| # | Endpoint | Test | Expected Result |
|---|----------|------|-----------------|
| 1 | GET /health | Hit endpoint | `{"status": "healthy"}` |
| 2 | POST /chat | `{"message": "What crop for Tamil Nadu?", "session_id": "test1", "farmer_id": "f1"}` | Success response with farming advice |
| 3 | POST /chat | `{"message": "என் நிலத்தில் என்ன பயிர் செய்வது?"}` (Tamil) | Reply in Tamil |
| 4 | POST /chat | Empty message `{"message": ""}` | Error: "Message cannot be empty" |
| 5 | GET /weather/Chennai | Hit endpoint | Weather data with temp, humidity, forecast |
| 6 | GET /weather/InvalidCity123 | Bad city name | Graceful error message |
| 7 | GET /schemes | Hit endpoint | Array of 9 government schemes |
| 8 | POST /image-analyze | Send base64 image + crop name | Disease analysis text |
| 9 | POST /image-analyze | Send without image | Error message |
| 10 | GET /profile/f_test123 | Non-existent farmer | Empty profile or 404 |
| 11 | PUT /profile/f_test123 | Save profile with all fields | Success message |
| 12 | GET /profile/f_test123 | After PUT | Returns saved profile data |
| 13 | POST /transcribe | Send audio base64 | Transcribed text |
| 14 | POST /chat | Very long message (500+ chars) | Should still work |
| 15 | POST /chat | Special characters `<script>alert(1)</script>` | Should not break, returns safe response |
| 16 | Frontend | Open ChatPage, type message, press Enter | Message appears, AI replies |
| 17 | Frontend | Click mic button, speak | Transcript appears, sent to AI |
| 18 | Frontend | Upload crop photo in CropDoctor | Image preview shown, analysis returned |
| 19 | Frontend | Weather page — search "Thanjavur" | Weather cards displayed |
| 20 | Frontend | Profile page — fill and save | "Profile saved" confirmation |

**How to test with Postman:**

1. Open Postman → New Request
2. Set method (GET/POST) and URL: `https://API_GATEWAY_URL/prod/health`
3. For POST requests: Body → raw → JSON → paste the test payload
4. Click Send → check response
5. Screenshot the result

**Bug report format (WhatsApp):**
```
BUG #3
Endpoint: POST /chat
Input: {"message": "hello"}
Expected: AI reply
Got: 500 Internal Server Error
Screenshot: [attach]
Priority: HIGH
```

---

## Parallel Timeline — Who Does What Each Day

```
Day 1 (Feb 26):
  Abhishek: Fill crop_guide_india.md + pest_patterns.md + govt_schemes.md
  Sanjay:   npm install → run frontend locally → explore mock data
  Manoj:    AWS setup → IAM, S3 bucket, DynamoDB tables → weather_lookup Lambda
  Jeevidha: Read docs → prepare test scenarios → install Postman

Day 2 (Feb 27):
  Abhishek: Finish remaining 3 KB docs + fill JSON + CSV → Manoj reviews KB
  Sanjay:   Build all 5 pages with mock data → polish CSS
  Manoj:    Implement all Lambdas → review Abhishek's KB docs
  Jeevidha: Review Abhishek's data → finalize Problem Statement + Summary

Day 3 (Feb 28):
  Abhishek: Help test → fix KB doc issues Manoj found
  Sanjay:   GET API_URL from Manoj → connect all pages to real API
  Manoj:    Bedrock AgentCore setup → sam deploy → SHARE API URL with team
  Jeevidha: Start API testing (health → weather → schemes → chat)

Day 4 (Mar 1):
  Abhishek: Mobile testing → take screenshots on phone
  Sanjay:   Deploy frontend to S3+CloudFront → test live URL
  Manoj:    Fix bugs from Jeevidha's testing → redeploy
  Jeevidha: Full endpoint testing → log all bugs

Day 5 (Mar 2):
  Abhishek: Help with screenshots → demo prep
  Sanjay:   Fix frontend bugs → responsive polish → prep for demo
  Manoj:    Fix remaining bugs → final deploy → verify live URL
  Jeevidha: E2E testing on live URL → edge cases → polish README + docs

Day 6 (Mar 3):
  ALL:      Record demo video (Sanjay narrates, Jeevidha operates)
  ALL:      Final review of all 5 deliverables
  Jeevidha: Submit everything before 11:59 PM IST on March 4

Day 7 (Mar 4 — DEADLINE):
  ALL:      Emergency fixes only → final submission by 11:59 PM IST
```

---

## The Single Source of Truth

**Everything** you need to implement is in `docs/Detailed_Implementation_Guide.md` (9000+ lines). Here's where to find your section:

| What | Guide Section | Who Reads It |
|------|--------------|--------------|
| Architecture overview | Section A4–A11 | Everyone |
| Lambda functions (full code) | Sections 7–12 | Manoj |
| SAM template | Section 6A | Manoj |
| API endpoints & contracts | Section 6C | Manoj + Sanjay + Jeevidha |
| React pages (full code) | Sections 15R–17R | Sanjay |
| CSS styling | Section 15R | Sanjay |
| Voice input | Section 16R | Sanjay |
| Knowledge Base data | Section 5 | Abhishek |
| Environment variables | Section 18R | Everyone |
| Deployment | Sections 19, 19R | Manoj + Sanjay |
| Budget & cost tips | Section A8 | Manoj |
| Testing checklist | Section 27 | Jeevidha |
| Submission deliverables | Section A9 | Jeevidha |

---

## Communication Plan

### Team's Group: "CI Hackathon"

**Daily check-in format (post by 10 AM):**
```
Sanjay: Yesterday — connected ChatPage to API. Today — WeatherPage + SchemesPage. Blocker — none.
Manoj: Yesterday — deployed 5 Lambdas. Today — AgentCore setup. Blocker — Abhishek's KB docs not done yet.
Abhishek: Yesterday — finished 4/6 KB docs. Today — finish remaining 2 + CSV. Blocker — none.
Jeevidha: Yesterday — tested /health and /weather. Today — test /chat and /schemes. Blocker — /chat returns 500.
```

### Key handoff moments:

| When | From | To | What |
|------|------|----|------|
| End of Day 1 | Abhishek | Manoj | KB docs ready for review |
| End of Day 2 | Manoj | Abhishek | Review feedback on KB docs |
| Day 3 | Manoj | Sanjay | API Gateway URL for frontend |
| Day 3 | Manoj | Jeevidha | API URL + endpoints list for testing |
| Day 4 | Sanjay | Jeevidha | Live frontend URL for E2E testing |
| Day 5 | Jeevidha | Manoj + Sanjay | Bug report list |
| Day 6 | Jeevidha | Everyone | Final docs for review before submit |

---

## Review Checkpoints

| Checkpoint | When | Reviewer(s) | What's Reviewed |
|-----------|------|-------------|----------------|
| **KB Doc Review** | End of Day 1 | Manoj | Abhishek's 6 knowledge base docs — accuracy, completeness, formatting |
| **API Review** | Day 3 | Jeevidha | All 8 endpoints — correct responses, error handling |
| **Frontend Review** | Day 4 | Manoj + Sanjay | All 5 pages working with real data, no console errors |
| **Docs Review** | Day 5 | Sanjay + Manoj | Jeevidha's README, Project Summary, Problem Statement |
| **Final Review** | Day 6 | ALL | All 5 submission deliverables — everyone signs off |

---

## What's Already Done for You

The scaffold includes **working starter code**, not blank files. Here's what's pre-built:

| Item | Status | Notes |
|------|--------|-------|
| All 5 React pages with complete JSX | ✅ Full code | Sanjay: tweak and connect to real API |
| CSS with agricultural green theme, sidebar, chat bubbles, cards | ✅ Full code | Sanjay: customize to taste |
| Voice input hook (Web Speech + Transcribe fallback) | ✅ Full code | Sanjay: just works — no edits needed |
| SAM template with all 7 Lambdas + DynamoDB + S3 | ✅ Full code | Manoj: `sam deploy` when ready |
| response_helper.py with standard envelope | ✅ Full code | Manoj: import and use in all Lambdas |
| 6 KB doc templates with headers + 1 example each | ✅ Templates | Abhishek: fill in the data |
| crop_data.csv with 20 crop names + Rice filled | ✅ Template | Abhishek: fill remaining 19 rows |
| govt_schemes.json with PM-KISAN filled | ✅ Template | Abhishek: fill remaining 8 schemes |
| Problem Statement + Project Summary docs | ✅ Drafts | Jeevidha: review and polish |
| .gitignore, .env.example, README | ✅ Done | Shared |

---

## 5 Submission Deliverables — Checklist

| # | Deliverable | Owner | Status |
|---|------------|-------|--------|
| 1 | **GitHub Repository** — full source code + README + architecture | Manoj (code) + Jeevidha (README) | 🟡 In progress |
| 2 | **Live Working Prototype URL** — judges can test in browser | Sanjay (frontend) + Manoj (backend) | ❌ Not yet |
| 3 | **Video Demo** — 5–7 min: problem → architecture → live demo → impact | Sanjay (narrate) + Jeevidha (operate) | ❌ Not yet |
| 4 | **Project Summary** — 500–800 words | Jeevidha (write) + Sanjay+Manoj (review) | 🟡 Draft done |
| 5 | **Problem Statement** — farming advisory gap description | Jeevidha (write) + Sanjay+Manoj (review) | 🟡 Draft done |

---

## Quick Reference — API Endpoints

| Method | Endpoint | Purpose | Lambda |
|--------|----------|---------|--------|
| POST | /chat | Send message, get AI reply | agent_orchestrator |
| POST | /voice | Send voice message (same Lambda) | agent_orchestrator |
| GET | /weather/{location} | Get weather for a city | weather_lookup |
| GET | /schemes | Get all government schemes | govt_schemes |
| POST | /image-analyze | Upload crop photo, get diagnosis | image_analysis |
| GET | /profile/{farmerId} | Get farmer profile | farmer_profile |
| PUT | /profile/{farmerId} | Save/update farmer profile | farmer_profile |
| POST | /transcribe | Convert audio to text (Firefox fallback) | transcribe_speech |
| GET | /health | Health check | inline (SAM template) |

**Standard Response Format (ALL endpoints):**
```json
{
    "status": "success",
    "data": { ... },
    "message": "Success",
    "language": "en"
}
```

**Error Response:**
```json
{
    "status": "error",
    "data": null,
    "message": "Error description",
    "language": "en"
}
```

---

## Emergency Contacts & Resources

| Resource | Link/Info |
|----------|-----------|
| Repo | https://github.com/Manoj-777/smart-rural-ai-advisor |
| Full Guide | `docs/Detailed_Implementation_Guide.md` |
| AWS Console | https://console.aws.amazon.com (ap-south-1) |
| Bedrock Console | https://ap-south-1.console.aws.amazon.com/bedrock/ |
| OpenWeatherMap API Key | https://openweathermap.org/api (free tier) |
| Kisan Helpline | 1800-180-1551 (reference for the app) |

---

*Last updated: February 26, 2026*  
*This document lives at: `TEAM_WORKPLAN.md` in the repo root*
