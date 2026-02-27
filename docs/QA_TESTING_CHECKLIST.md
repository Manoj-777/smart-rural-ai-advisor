# QA Testing Checklist - Smart Rural AI Advisor

**QA Lead:** Jeevidha R  
**Created:** February 26, 2026  
**Last Updated:** February 26, 2026

---

## Testing Schedule

| Day | Testing Phase | Focus Area |
|-----|--------------|------------|
| Day 1 | Setup | Postman collection created ✅ |
| Day 2 | Documentation Review | Review KB docs, finalize problem statement |
| Day 3 | API Testing - Phase 1 | Health, Weather, Schemes endpoints |
| Day 4 | API Testing - Phase 2 | Chat, Image, Profile, Transcribe endpoints |
| Day 5 | E2E Testing | Frontend + Backend integration, mobile testing |
| Day 6 | Final Testing | Edge cases, demo prep, bug verification |

---

## Day 1 Checklist ✅

- [x] Install Postman
- [x] Create API test collection (16+ test cases)
- [x] Set up environment variables
- [x] Create multilingual test cases (10 languages)
- [ ] Review PROBLEM_STATEMENT.md
- [ ] Review PROJECT_SUMMARY.md
- [ ] Suggest improvements to documentation
- [ ] Help Abhishek validate KB data (if time permits)

---

## Day 2 Checklist

### Documentation Tasks
- [ ] Review Abhishek's completed KB documents:
  - [ ] crop_guide_india.md - Check all 20 crops filled
  - [ ] pest_patterns.md - Verify disease info is accurate
  - [ ] govt_schemes.md - Cross-check scheme amounts with official websites
  - [ ] traditional_farming.md - Review for completeness
  - [ ] irrigation_guide.md - Check water requirement numbers
  - [ ] region_advisories.md - Verify state-specific info
- [ ] Finalize PROBLEM_STATEMENT.md wording
- [ ] Finalize PROJECT_SUMMARY.md wording
- [ ] Review README.md - suggest improvements

### Data Validation Tasks
- [ ] Verify government scheme amounts:
  - [ ] PM-KISAN: ₹6,000/year (not ₹10,000)
  - [ ] PM Fasal Bima Yojana: Premium rates correct
  - [ ] Other schemes match official sources
- [ ] Check crop data for realism:
  - [ ] Water requirements (e.g., wheat = 450mm, not 2000mm)
  - [ ] Growing seasons match regional calendars
  - [ ] Soil types are appropriate

---

## Day 3 Checklist - API Testing Phase 1

**Prerequisites:**
- [ ] Manoj shares API Gateway URL
- [ ] Update Postman environment variable `base_url`
- [ ] Confirm API is deployed and accessible

### Basic Endpoint Testing

#### Health Check
- [ ] GET /health returns 200 status
- [ ] Response format: `{"status": "healthy"}`
- [ ] Response time < 1 second

#### Weather Endpoint
- [ ] GET /weather/Chennai - Valid city
  - [ ] Returns 200 status
  - [ ] Contains temperature, humidity, description
  - [ ] Forecast array is present
  - [ ] Response time < 3 seconds
- [ ] GET /weather/Mumbai - Different city
- [ ] GET /weather/Thanjavur - Smaller city
- [ ] GET /weather/InvalidCity123 - Error handling
  - [ ] Returns appropriate error message
  - [ ] Status code is 400 or 404
  - [ ] Error message is user-friendly

#### Government Schemes Endpoint
- [ ] GET /schemes returns 200 status
- [ ] Response contains array of schemes
- [ ] At least 9 schemes present
- [ ] Each scheme has required fields:
  - [ ] id, name, amount, description
  - [ ] eligibility, how_to_apply
- [ ] Response time < 2 seconds

### Bug Logging
- [ ] Screenshot all errors
- [ ] Report bugs in WhatsApp group immediately
- [ ] Use bug report template

---

## Day 4 Checklist - API Testing Phase 2

### Chat Endpoint Testing

#### Basic Chat Tests
- [ ] POST /chat - English message
  - [ ] Returns 200 status
  - [ ] Reply contains farming advice
  - [ ] Response format matches expected structure
  - [ ] Response time < 10 seconds
- [ ] POST /chat - Empty message
  - [ ] Returns error (400 status)
  - [ ] Error message: "Message cannot be empty"
- [ ] POST /chat - Very long message (500+ chars)
  - [ ] Handles without error
  - [ ] Response is relevant
- [ ] POST /chat - Special characters
  - [ ] Sanitizes input properly
  - [ ] No XSS vulnerabilities

#### Multilingual Chat Tests
- [ ] Hindi message - Reply in Hindi
- [ ] Tamil message - Reply in Tamil
- [ ] Telugu message - Reply in Telugu
- [ ] Kannada message - Reply in Kannada
- [ ] Malayalam message - Reply in Malayalam
- [ ] Marathi message - Reply in Marathi
- [ ] Gujarati message - Reply in Gujarati
- [ ] Punjabi message - Reply in Punjabi
- [ ] Bengali message - Reply in Bengali
- [ ] Mixed language (Hinglish) - Handles appropriately

#### Chat Context & Session Tests
- [ ] Multiple messages in same session maintain context
- [ ] Different sessions are isolated
- [ ] Session IDs work correctly

### Image Analysis Endpoint
- [ ] POST /image-analyze - Valid image
  - [ ] Returns disease diagnosis
  - [ ] Provides treatment recommendations
  - [ ] Response time < 15 seconds
- [ ] POST /image-analyze - Missing image
  - [ ] Returns appropriate error
- [ ] POST /image-analyze - Invalid image format
  - [ ] Handles gracefully with error message
- [ ] POST /image-analyze - Very large image
  - [ ] Either processes or returns size limit error

### Farmer Profile Endpoint
- [ ] GET /profile/farmer_test_123 - Non-existent
  - [ ] Returns empty profile or 404
- [ ] PUT /profile/farmer_test_123 - Create profile
  - [ ] Returns success message
  - [ ] All fields saved correctly
- [ ] GET /profile/farmer_test_123 - After creation
  - [ ] Returns saved profile data
  - [ ] All fields match what was saved
- [ ] PUT /profile/farmer_test_123 - Update profile
  - [ ] Updates existing profile
  - [ ] Doesn't create duplicate

### Transcribe Endpoint
- [ ] POST /transcribe - Valid audio
  - [ ] Returns transcribed text
  - [ ] Language detection works
- [ ] POST /transcribe - Missing audio
  - [ ] Returns appropriate error

---

## Day 5 Checklist - E2E & Mobile Testing

### Frontend Integration Testing

#### Chat Page
- [ ] Open ChatPage at live URL
- [ ] Type message and press Enter
  - [ ] Message appears in chat
  - [ ] AI reply appears within 10 seconds
  - [ ] Reply is relevant to question
- [ ] Click mic button
  - [ ] Recording indicator shows
  - [ ] Speak a question
  - [ ] Transcript appears
  - [ ] Message sent to AI
  - [ ] Reply received
- [ ] Test voice output
  - [ ] Audio plays automatically (if enabled)
  - [ ] Audio is in correct language
- [ ] Test multiple messages
  - [ ] Chat history displays correctly
  - [ ] Scroll works properly

#### Weather Page
- [ ] Open WeatherPage
- [ ] Search for "Chennai"
  - [ ] Weather cards display
  - [ ] Temperature, humidity shown
  - [ ] Forecast is visible
- [ ] Search for different city
  - [ ] Updates correctly
- [ ] Search for invalid city
  - [ ] Shows error message

#### Schemes Page
- [ ] Open SchemesPage
- [ ] All schemes load and display
- [ ] Each scheme card shows:
  - [ ] Scheme name
  - [ ] Amount/benefit
  - [ ] Description
  - [ ] Eligibility
  - [ ] How to apply
- [ ] Search/filter works (if implemented)

#### Crop Doctor Page
- [ ] Open CropDoctorPage
- [ ] Click upload button
- [ ] Select crop image
  - [ ] Image preview shows
- [ ] Click "Analyze" button
  - [ ] Loading indicator shows
  - [ ] Analysis result appears
  - [ ] Diagnosis is readable
  - [ ] Treatment recommendations shown

#### Profile Page
- [ ] Open ProfilePage
- [ ] Fill all fields:
  - [ ] Name, phone, location
  - [ ] Land size, soil type
  - [ ] Irrigation method
  - [ ] Crops grown
  - [ ] Language preference
- [ ] Click "Save"
  - [ ] Success message appears
- [ ] Refresh page
  - [ ] Profile data persists

### Mobile Testing (Chrome Android)
- [ ] Open live URL on mobile phone
- [ ] Test all 5 pages on mobile
- [ ] Check responsive design:
  - [ ] Sidebar works on mobile
  - [ ] Text is readable
  - [ ] Buttons are tappable
  - [ ] No horizontal scroll
- [ ] Test voice input on mobile
- [ ] Test image upload on mobile
- [ ] Take screenshots of all pages

### Edge Cases
- [ ] No internet connection - Shows appropriate error
- [ ] Slow internet - Loading indicators work
- [ ] Browser back button - Navigation works
- [ ] Refresh page - State is maintained (if applicable)
- [ ] Multiple tabs - Sessions are independent

---

## Day 6 Checklist - Final Testing & Demo Prep

### Bug Verification
- [ ] Retest all bugs reported on Day 3-5
- [ ] Verify all fixes work correctly
- [ ] Close resolved bugs in tracking

### Performance Testing
- [ ] Test concurrent requests (send 5 messages quickly)
- [ ] Check response times under load
- [ ] Verify no memory leaks (long session)

### Security Testing
- [ ] SQL injection attempts (if applicable)
- [ ] XSS attempts in chat input
- [ ] Invalid tokens/IDs
- [ ] CORS is configured correctly

### Demo Preparation
- [ ] Take screenshots of all 5 pages
  - [ ] ChatPage with conversation
  - [ ] WeatherPage with data
  - [ ] SchemesPage with schemes
  - [ ] CropDoctorPage with analysis
  - [ ] ProfilePage filled out
- [ ] Save screenshots in `demo/screenshots/`
- [ ] Prepare demo script for video
- [ ] Test demo flow end-to-end

### Documentation Final Review
- [ ] README.md is complete and accurate
- [ ] All links work
- [ ] Setup instructions are clear
- [ ] Live URL is added
- [ ] Screenshots are embedded

---

## Bug Report Template

Use this format when reporting bugs:

```
BUG #[number]
Endpoint/Page: [e.g., POST /chat or ChatPage]
Input: [what you sent/did]
Expected: [what should happen]
Got: [what actually happened]
Status Code: [if API]
Screenshot: [attach]
Priority: [HIGH/MEDIUM/LOW]
Browser/Device: [if frontend]
```

### Priority Levels
- **HIGH**: Blocks core functionality, crashes, data loss
- **MEDIUM**: Feature doesn't work as expected, poor UX
- **LOW**: Minor UI issues, typos, nice-to-have improvements

---

## Test Results Summary

### Day 3 Results
- Total Tests: ___
- Passed: ___
- Failed: ___
- Bugs Found: ___

### Day 4 Results
- Total Tests: ___
- Passed: ___
- Failed: ___
- Bugs Found: ___

### Day 5 Results
- Total Tests: ___
- Passed: ___
- Failed: ___
- Bugs Found: ___

### Final Status (Day 6)
- All Critical Bugs Fixed: [ ]
- All Medium Bugs Fixed: [ ]
- Low Priority Bugs: [ ] Fixed / [ ] Documented for future
- Ready for Submission: [ ]

---

## Sign-off

- [ ] Jeevidha (QA Lead) - All testing complete
- [ ] Manoj (Backend) - All backend bugs fixed
- [ ] Sanjay (Frontend) - All frontend bugs fixed
- [ ] Team - Ready to submit

---

*Last updated: February 26, 2026*
