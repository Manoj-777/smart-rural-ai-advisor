# Postman Test Collection Setup Guide

## Collection: Smart Rural AI Advisor - API Tests

### Environment Variable
- `base_url`: Will be provided by Manoj on Day 3
- Example: `https://abc123.execute-api.ap-south-1.amazonaws.com/Prod`

---

## Test Requests to Create

### 1. Health Check
- **Method:** GET
- **URL:** `{{base_url}}/health`
- **Expected Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Chat - Basic Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Headers:** Content-Type: application/json (auto-added)
- **Body (raw JSON):**
```json
{
  "message": "What crop should I plant in Tamil Nadu?",
  "session_id": "test_session_1",
  "farmer_id": "farmer_001"
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "reply": "AI farming advice here...",
    "audio_url": "optional audio URL"
  },
  "message": "Success",
  "language": "en"
}
```

---

### 3. Chat - Tamil Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "என் நிலத்தில் என்ன பயிர் செய்வது?",
  "session_id": "test_session_2",
  "farmer_id": "farmer_001"
}
```
- **Expected:** Reply should be in Tamil
- **Translation:** "What crop should I plant in my land?"

---

### 3a. Chat - Hindi Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "मुझे अपनी जमीन पर कौन सी फसल लगानी चाहिए?",
  "session_id": "test_session_3a",
  "farmer_id": "farmer_002"
}
```
- **Expected:** Reply should be in Hindi
- **Translation:** "Which crop should I plant on my land?"

---

### 3b. Chat - Telugu Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "నా భూమిలో ఏ పంట పండించాలి?",
  "session_id": "test_session_3b",
  "farmer_id": "farmer_003"
}
```
- **Expected:** Reply should be in Telugu
- **Translation:** "Which crop should I grow in my land?"

---

### 3c. Chat - Kannada Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "ನನ್ನ ಭೂಮಿಯಲ್ಲಿ ಯಾವ ಬೆಳೆ ಬೆಳೆಯಬೇಕು?",
  "session_id": "test_session_3c",
  "farmer_id": "farmer_004"
}
```
- **Expected:** Reply should be in Kannada
- **Translation:** "Which crop should I grow in my land?"

---

### 3d. Chat - Malayalam Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "എന്റെ ഭൂമിയിൽ ഏത് വിളയാണ് നടേണ്ടത്?",
  "session_id": "test_session_3d",
  "farmer_id": "farmer_005"
}
```
- **Expected:** Reply should be in Malayalam
- **Translation:** "Which crop should I plant in my land?"

---

### 3e. Chat - Marathi Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "माझ्या जमिनीवर कोणते पीक लावावे?",
  "session_id": "test_session_3e",
  "farmer_id": "farmer_006"
}
```
- **Expected:** Reply should be in Marathi
- **Translation:** "Which crop should I plant on my land?"

---

### 3f. Chat - Gujarati Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "મારી જમીનમાં કયો પાક ઉગાડવો જોઈએ?",
  "session_id": "test_session_3f",
  "farmer_id": "farmer_007"
}
```
- **Expected:** Reply should be in Gujarati
- **Translation:** "Which crop should I grow in my land?"

---

### 3g. Chat - Punjabi Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "ਮੈਨੂੰ ਆਪਣੀ ਜ਼ਮੀਨ 'ਤੇ ਕਿਹੜੀ ਫਸਲ ਲਾਉਣੀ ਚਾਹੀਦੀ ਹੈ?",
  "session_id": "test_session_3g",
  "farmer_id": "farmer_008"
}
```
- **Expected:** Reply should be in Punjabi
- **Translation:** "Which crop should I plant on my land?"

---

### 3h. Chat - Bengali Language Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "আমার জমিতে কোন ফসল চাষ করা উচিত?",
  "session_id": "test_session_3h",
  "farmer_id": "farmer_009"
}
```
- **Expected:** Reply should be in Bengali
- **Translation:** "Which crop should I cultivate in my land?"

---

### 3i. Chat - Mixed Language Test (Code-Switching)
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "मेरे पास 5 acre जमीन है और मैं rice लगाना चाहता हूं। क्या यह सही है?",
  "session_id": "test_session_3i",
  "farmer_id": "farmer_010"
}
```
- **Expected:** Reply should handle Hindi-English mix (common in rural India)
- **Translation:** "I have 5 acre land and I want to plant rice. Is this correct?"

---

### 3j. Chat - Regional Dialect Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "எங்க ஊர்ல என்ன பயிர் போடலாம்? மழை நல்லா வருது.",
  "session_id": "test_session_3j",
  "farmer_id": "farmer_011"
}
```
- **Expected:** Reply should handle colloquial Tamil
- **Translation:** "What crop can we plant in our village? Rain is coming well."

---

### 4. Chat - Empty Message (Error Test)
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "",
  "session_id": "test_session_3",
  "farmer_id": "farmer_001"
}
```
- **Expected Response:**
```json
{
  "status": "error",
  "data": null,
  "message": "Message cannot be empty",
  "language": "en"
}
```

---

### 5. Chat - Long Message Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "I have a 5 acre farm in Tamil Nadu near Thanjavur district. The soil is clay loam and I have access to canal irrigation. Last year I planted rice during Kharif season and got good yield. This year I want to try something different. What crop would you recommend considering the current market prices and water availability? Also, are there any government schemes I can apply for? I am particularly interested in organic farming methods and want to know about pest management without using chemical pesticides. Can you provide detailed guidance?",
  "session_id": "test_session_4",
  "farmer_id": "farmer_001"
}
```
- **Expected:** Should handle long messages without error

---

### 6. Chat - Special Characters Test
- **Method:** POST
- **URL:** `{{base_url}}/chat`
- **Body (raw JSON):**
```json
{
  "message": "<script>alert('test')</script> What crop to plant?",
  "session_id": "test_session_5",
  "farmer_id": "farmer_001"
}
```
- **Expected:** Should sanitize and respond safely

---

### 7. Weather - Valid City
- **Method:** GET
- **URL:** `{{base_url}}/weather/Chennai`
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "location": "Chennai",
    "temperature": 32,
    "humidity": 75,
    "description": "Partly cloudy",
    "forecast": [...]
  },
  "message": "Success",
  "language": "en"
}
```

---

### 8. Weather - Invalid City
- **Method:** GET
- **URL:** `{{base_url}}/weather/InvalidCity123`
- **Expected:** Graceful error message

---

### 9. Weather - Multiple Cities (Test Different Locations)
Create separate requests for:
- `{{base_url}}/weather/Mumbai`
- `{{base_url}}/weather/Thanjavur`
- `{{base_url}}/weather/Bangalore`

---

### 10. Government Schemes - Get All
- **Method:** GET
- **URL:** `{{base_url}}/schemes`
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "schemes": [
      {
        "id": "pm-kisan",
        "name": "PM-KISAN",
        "amount": "₹6,000/year",
        "description": "...",
        "eligibility": "...",
        "how_to_apply": "..."
      }
      // ... 8 more schemes
    ]
  },
  "message": "Success",
  "language": "en"
}
```

---

### 11. Image Analysis - Valid Request
- **Method:** POST
- **URL:** `{{base_url}}/image-analyze`
- **Body (raw JSON):**
```json
{
  "image": "base64_encoded_image_string_here",
  "crop_name": "Rice",
  "farmer_id": "farmer_001"
}
```
- **Note:** You'll need to convert an actual crop image to base64. Use online tools or this approach:
  1. Find a crop disease image online
  2. Use https://www.base64-image.de/ to convert to base64
  3. Copy the base64 string (without the data:image prefix)

---

### 12. Image Analysis - Missing Image (Error Test)
- **Method:** POST
- **URL:** `{{base_url}}/image-analyze`
- **Body (raw JSON):**
```json
{
  "crop_name": "Rice",
  "farmer_id": "farmer_001"
}
```
- **Expected:** Error message about missing image

---

### 13. Farmer Profile - Get Non-Existent
- **Method:** GET
- **URL:** `{{base_url}}/profile/farmer_test_123`
- **Expected:** Empty profile or 404

---

### 14. Farmer Profile - Create/Update
- **Method:** PUT
- **URL:** `{{base_url}}/profile/farmer_test_123`
- **Body (raw JSON):**
```json
{
  "name": "Test Farmer",
  "phone": "9876543210",
  "location": "Thanjavur, Tamil Nadu",
  "land_size": "5 acres",
  "soil_type": "Clay loam",
  "irrigation": "Canal",
  "crops_grown": ["Rice", "Sugarcane"],
  "language_preference": "ta"
}
```
- **Expected:** Success message

---

### 15. Farmer Profile - Get After Update
- **Method:** GET
- **URL:** `{{base_url}}/profile/farmer_test_123`
- **Expected:** Returns the profile data you just saved

---

### 16. Transcribe Speech
- **Method:** POST
- **URL:** `{{base_url}}/transcribe`
- **Body (raw JSON):**
```json
{
  "audio": "base64_encoded_audio_string",
  "language": "en-IN",
  "farmer_id": "farmer_001"
}
```
- **Note:** This is complex to test. You can skip this initially and test it through the frontend voice feature instead.

---

## How to Test Each Request

1. **Select the request** from your collection
2. **Click "Send"** button
3. **Check the response:**
   - Status code (200 = success, 400 = bad request, 500 = server error)
   - Response body (JSON data)
   - Response time
4. **Take a screenshot** if there's an error
5. **Log bugs** in WhatsApp group

---

## Bug Report Template

When you find a bug, report it like this in WhatsApp:

```
BUG #1
Endpoint: POST /chat
Input: {"message": "hello", "session_id": "test1", "farmer_id": "f1"}
Expected: AI reply with farming advice
Got: 500 Internal Server Error
Response: {"status": "error", "message": "Internal server error"}
Screenshot: [attach]
Priority: HIGH
```

---

## Testing Checklist

Use this checklist as you test:

### Day 3 Testing (When API is deployed)
- [ ] Health check works
- [ ] Weather endpoint - valid city
- [ ] Weather endpoint - invalid city
- [ ] Government schemes endpoint
- [ ] Chat - basic English message
- [ ] Chat - Tamil message
- [ ] Chat - empty message (should error)

### Day 4 Testing (Full endpoint testing)
- [ ] Chat - long message
- [ ] Chat - special characters
- [ ] Image analysis - valid image
- [ ] Image analysis - missing image
- [ ] Profile - GET non-existent
- [ ] Profile - PUT create new
- [ ] Profile - GET after update
- [ ] All endpoints return correct status codes
- [ ] All error messages are clear and helpful

### Day 5 Testing (Edge cases + E2E)
- [ ] Test all endpoints with missing required fields
- [ ] Test with very large payloads
- [ ] Test concurrent requests (send multiple at once)
- [ ] Test from mobile browser
- [ ] Test frontend integration with all pages

---

## Tips for Effective Testing

1. **Test in order:** Start with simple endpoints (health, weather) before complex ones (chat, image)
2. **Save responses:** Postman saves response history - review them to spot patterns
3. **Use folders:** Organize requests into folders like "Chat Tests", "Weather Tests", etc.
4. **Duplicate requests:** Right-click a request → Duplicate to create variations
5. **Add descriptions:** Add notes to each request explaining what it tests
6. **Response validation:** Check not just that it works, but that data format matches expected structure

---

*Created for Jeevidha R - QA Lead*
*Last updated: February 26, 2026*
