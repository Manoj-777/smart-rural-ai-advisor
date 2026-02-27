# Demo Video

## Link
> **TODO:** Upload demo video to YouTube/Loom and paste link here.

`https://YOUR_DEMO_VIDEO_URL`

---

## Demo Walkthrough Script (2-3 minutes)

### Pre-Demo Setup
1. Run frontend: `cd frontend && npm run dev` → opens http://localhost:5173
2. Make sure browser is Chrome (for Web Speech API voice input)
3. Set language to Tamil in sidebar for the multilingual demo

---

### Scene 1: Dashboard Overview (15s)
**What to show:**
- Open the app → Dashboard loads with localized greeting ("காலை வணக்கம்" in Tamil)
- Point out: Daily farming tip in the user's language
- Season indicator showing current season (Rabi: Oct-Feb)
- Quick action cards (Chat, Weather, Schemes, Crop Doctor)

**Talking point:** *"The dashboard shows localized farming tips and season awareness for Indian agriculture."*

---

### Scene 2: AI Chat in English (30s)
**What to type:** `What is the weather in Chennai for the next 3 days?`

**What to show:**
- AI calls the `get_weather` tool → returns real-time data from OpenWeather API
- Response shows temperature, humidity, wind, rain probability
- Audio player appears → click play to hear the response spoken
- Mention: AI used real weather data, not hallucinated

**Talking point:** *"The AI doesn't guess — it calls real weather APIs and presents factual data with a farming advisory."*

---

### Scene 3: Voice Input in Tamil (30s)
**What to do:**
1. Switch language to **Tamil** in the sidebar
2. Click 🎤 mic button
3. Speak: "நெல் பயிரில் பழுப்பு நிற புள்ளிகள் உள்ளன" (Brown spots on paddy crop)
4. Voice is transcribed → sent to AI

**What to show:**
- Tamil text appears in chat
- AI detects pest/disease intent → calls `get_pest_alert`
- Response comes back in Tamil
- Audio plays in Tamil (gTTS)

**Talking point:** *"Farmers can speak in their native language. The AI understands Tamil, detects the pest query, and responds with treatment advice — all in Tamil."*

---

### Scene 4: Crop Doctor — Photo Analysis (30s)
**What to do:**
1. Navigate to **📸 Crop Doctor** in sidebar
2. Upload a photo of a diseased plant leaf
3. Select crop: **Rice**, State: **Tamil Nadu**
4. Click **🔍 Analyze**

**What to show:**
- Image uploads and compression happens automatically
- Claude Sonnet 4.5 Vision analyzes the image
- Structured diagnosis: Disease name, Severity, Confidence
- Organic + Chemical treatment options
- Prevention steps and urgency level

**Talking point:** *"Using Claude's vision capabilities, we analyze crop photos and give structured diagnoses with both organic and chemical treatment options."*

---

### Scene 5: Government Schemes (20s)
**What to do:**
1. Navigate to **📋 Schemes**
2. Browse the scheme list

**What to show:**
- PM-KISAN: ₹6,000/year, eligibility, how to apply
- PMFBY: Crop insurance, premium details
- Soil Health Card: Free testing, NPK analysis
- Search filter works

**Talking point:** *"Indian farmers often don't know which government schemes they qualify for. We surface all relevant schemes with eligibility and application steps."*

---

### Scene 6: Farmer Profile (15s)
**What to do:**
1. Navigate to **👤 Profile**
2. Fill in: Name, District (Thanjavur), Crops (Rice, Banana), Soil (Alluvial)
3. Click Save

**What to show:**
- Profile saves to DynamoDB
- Summary card appears
- Explain: Future chat responses will be personalized based on this profile

**Talking point:** *"Saving a profile means the AI remembers your farm details and gives personalized recommendations every time."*

---

### Scene 7: Multilingual UI (20s)
**What to do:**
1. Switch language in sidebar to **Telugu (తెలుగు)**
2. Watch entire UI change: sidebar labels, page headers, form labels
3. Type: "రైతులకు ప్రభుత్వ పథకాలు చెప్పండి" (Tell me government schemes for farmers)

**What to show:**
- UI is fully localized
- AI responds in Telugu
- Audio plays in Telugu

**Talking point:** *"The entire application supports 13 Indian languages — UI, AI responses, and voice output — all localized."*

---

## Demo Tips
- Keep Chrome DevTools closed (it slows voice recording)
- Use a microphone headset for cleaner voice capture
- If voice fails, type the Tamil/Telugu text directly — it still triggers multilingual AI
- Demo mode (`VITE_MOCK_AI=true`) available if backend is unavailable

## Screenshots

> Add screenshots to `demo/screenshots/` folder

### Suggested Screenshots
1. Dashboard with Tamil greeting
2. Weather page showing Chennai forecast
3. Chat with English weather query + audio player
4. Chat with Tamil voice input transcribed
5. Crop Doctor with uploaded leaf photo + AI diagnosis
6. Government Schemes list with PM-KISAN expanded
7. Profile page with filled form + summary
8. Sidebar showing Telugu language selected
