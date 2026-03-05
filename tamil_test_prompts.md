# Tamil Test Prompts for Smart Rural AI Advisor

## 🌤️ Weather Queries

### Simple Weather
```tamil
சென்னையில் இன்றைய வானிலை என்ன?
```
**Translation:** What is today's weather in Chennai?

### Weather Forecast
```tamil
கோவையில் அடுத்த 3 நாட்களுக்கு மழை பெய்யுமா?
```
**Translation:** Will it rain in Coimbatore for the next 3 days?

### Farming Weather
```tamil
தஞ்சாவூரில் இந்த வாரம் வானிலை எப்படி இருக்கும்? விவசாயத்திற்கு ஏற்றதா?
```
**Translation:** How will the weather be in Thanjavur this week? Is it suitable for farming?

---

## 🌾 Crop Advisory

### Crop Recommendation
```tamil
கரூர் மாவட்டத்தில் கார் பருவத்தில் என்ன பயிர் செய்யலாம்?
```
**Translation:** What crop can I grow in Karur district during Kharif season?

### Paddy Cultivation
```tamil
நெல் பயிரிட சிறந்த நேரம் எப்போது? என்ன மண் தேவை?
```
**Translation:** When is the best time to cultivate paddy? What soil is needed?

### Fertilizer Advice
```tamil
தக்காளி பயிருக்கு என்ன உரம் போட வேண்டும்?
```
**Translation:** What fertilizer should I apply for tomato crop?

### Soil Type Query
```tamil
சிவகங்கை மாவட்டத்தில் எந்த மண்ணில் பருத்தி நன்றாக வளரும்?
```
**Translation:** In which soil will cotton grow well in Sivagangai district?

---

## 🐛 Pest & Disease

### Yellow Leaves
```tamil
என் நெல் பயிரில் இலைகள் மஞ்சள் நிறமாக மாறுகிறது. என்ன செய்வது?
```
**Translation:** The leaves of my paddy crop are turning yellow. What should I do?

### Brown Spots
```tamil
தக்காளி இலைகளில் பழுப்பு நிற புள்ளிகள் தெரிகிறது. இது என்ன நோய்?
```
**Translation:** Brown spots are appearing on tomato leaves. What disease is this?

### Pest Attack
```tamil
பருத்தி பயிரில் பூச்சி தாக்குதல் உள்ளது. என்ன மருந்து தெளிக்க வேண்டும்?
```
**Translation:** There is a pest attack on cotton crop. What medicine should I spray?

### Wilting Problem
```tamil
என் வாழை செடிகள் வாடி போகிறது. காரணம் என்ன?
```
**Translation:** My banana plants are wilting. What is the reason?

---

## 💧 Irrigation

### Water Requirements
```tamil
நெல் பயிருக்கு எவ்வளவு தண்ணீர் தேவை?
```
**Translation:** How much water is needed for paddy crop?

### Drip Irrigation
```tamil
சொட்டு நீர் பாசனம் பற்றி சொல்லுங்கள். எப்படி செய்வது?
```
**Translation:** Tell me about drip irrigation. How to do it?

### Watering Schedule
```tamil
தக்காளி பயிருக்கு எத்தனை நாட்களுக்கு ஒரு முறை தண்ணீர் விட வேண்டும்?
```
**Translation:** How many days once should I water tomato crop?

---

## 📋 Government Schemes

### PM-KISAN
```tamil
பிரதமர் கிசான் திட்டம் பற்றி சொல்லுங்கள். எப்படி விண்ணப்பிப்பது?
```
**Translation:** Tell me about PM-KISAN scheme. How to apply?

### Crop Insurance
```tamil
பயிர் காப்பீடு திட்டம் என்ன? எனக்கு தகுதி உண்டா?
```
**Translation:** What is crop insurance scheme? Am I eligible?

### Subsidy
```tamil
விவசாயிகளுக்கு என்ன மானியங்கள் கிடைக்கும்?
```
**Translation:** What subsidies are available for farmers?

### Soil Health Card
```tamil
மண் ஆரோக்கிய அட்டை எப்படி பெறுவது?
```
**Translation:** How to get Soil Health Card?

---

## 🌱 Mixed/Complex Queries

### Multi-topic Query
```tamil
திருச்சியில் கார் பருவத்தில் நெல் பயிரிட விரும்புகிறேன். வானிலை எப்படி இருக்கும்? என்ன உரம் போட வேண்டும்?
```
**Translation:** I want to cultivate paddy in Trichy during Kharif season. How will the weather be? What fertilizer should I apply?

### Seasonal Planning
```tamil
இந்த மாதம் மதுரை மாவட்டத்தில் என்ன பயிர் செய்யலாம்? மழை வருமா?
```
**Translation:** What crop can I grow this month in Madurai district? Will it rain?

### Problem Diagnosis
```tamil
என் பருத்தி பயிரில் இலைகள் சுருண்டு போகிறது. மழை இல்லாததால் தானா? என்ன செய்வது?
```
**Translation:** The leaves of my cotton crop are curling. Is it because of no rain? What should I do?

---

## 🎤 Conversational/Follow-up

### Greeting
```tamil
வணக்கம். நான் ஒரு விவசாயி. எனக்கு உதவி செய்ய முடியுமா?
```
**Translation:** Hello. I am a farmer. Can you help me?

### Thank You
```tamil
நன்றி. மிகவும் பயனுள்ளதாக இருந்தது.
```
**Translation:** Thank you. It was very helpful.

### Follow-up Question
```tamil
இன்னும் கொஞ்சம் விளக்கமாக சொல்ல முடியுமா?
```
**Translation:** Can you explain a bit more?

---

## 🧪 Test Categories

### Category 1: Simple Queries (Single Intent)
- Weather only
- Crop only
- Pest only
- Schemes only

### Category 2: Complex Queries (Multiple Intents)
- Weather + Crop
- Crop + Pest
- Crop + Irrigation
- Weather + Schemes

### Category 3: Conversational
- Greetings
- Follow-ups
- Clarifications

### Category 4: Location-specific
- With district name
- With village name
- With state name

---

## 📝 Expected Behavior

1. **Language Detection:** Should detect Tamil (ta)
2. **Translation:** Should translate to English internally
3. **Tool Calling:** Should call appropriate Lambda tools
4. **Response:** Should respond in Tamil
5. **Audio:** Should generate Tamil TTS audio

---

## 🚀 Quick Test Script

```python
import requests
import json

API_URL = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat"

test_prompts = [
    "சென்னையில் இன்றைய வானிலை என்ன?",
    "நெல் பயிரில் இலைகள் மஞ்சள் நிறமாக மாறுகிறது",
    "பிரதமர் கிசான் திட்டம் பற்றி சொல்லுங்கள்"
]

for prompt in test_prompts:
    payload = {
        "message": prompt,
        "session_id": "test-tamil-session",
        "farmer_id": "test-farmer",
        "language": "ta"
    }
    
    response = requests.post(API_URL, json=payload)
    result = response.json()
    
    print(f"\n{'='*60}")
    print(f"Query: {prompt}")
    print(f"Response: {result.get('reply', 'No response')}")
    print(f"Tools Used: {result.get('tools_used', [])}")
    print(f"Audio URL: {result.get('audio_url', 'No audio')}")
```

---

## 💡 Tips for Testing

1. **Start Simple:** Test single-intent queries first
2. **Check Tools:** Verify correct tools are called
3. **Verify Translation:** Check if response is in Tamil
4. **Test Audio:** Ensure Tamil TTS works
5. **Follow-ups:** Test conversation memory
6. **Edge Cases:** Test with typos, mixed languages

---

**Note:** All these prompts are designed to test different aspects of your AI advisor:
- Language detection (Tamil)
- Intent classification
- Tool calling (weather, crop, pest, schemes)
- Response generation
- Tamil TTS audio generation
