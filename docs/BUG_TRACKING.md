# Bug Tracking Log - Smart Rural AI Advisor

**QA Lead:** Jeevidha R  
**Project:** Smart Rural AI Advisor  
**Hackathon:** AWS AI for Bharat 2026

---

## How to Use This Document

1. When you find a bug, add it to the "Open Bugs" section
2. Report it immediately in WhatsApp group
3. When Manoj/Sanjay fixes it, move it to "Fixed Bugs" section
4. Retest and mark as "Verified Fixed"

---

## Bug Status Legend

- 🔴 **OPEN** - Bug found, not yet fixed
- 🟡 **IN PROGRESS** - Developer is working on fix
- 🟢 **FIXED** - Developer claims it's fixed, needs verification
- ✅ **VERIFIED** - Retested and confirmed fixed
- ❌ **WONTFIX** - Not fixing (out of scope, low priority, etc.)

---

## Open Bugs

### BUG #1
- **Status:** 🔴 OPEN
- **Priority:** HIGH
- **Found:** Day 3, Feb 28, 2026
- **Endpoint/Page:** POST /chat
- **Description:** Chat endpoint returns 500 error for Tamil messages
- **Input:** `{"message": "என் நிலத்தில் என்ன பயிர் செய்வது?", "session_id": "test1", "farmer_id": "f1"}`
- **Expected:** Reply in Tamil with farming advice
- **Got:** 500 Internal Server Error
- **Response:** `{"status": "error", "message": "Internal server error"}`
- **Screenshot:** [Link or attach]
- **Assigned to:** Manoj
- **Notes:** English messages work fine, only Tamil fails

---

### BUG #2
- **Status:** 🔴 OPEN
- **Priority:** MEDIUM
- **Found:** Day 4, Mar 1, 2026
- **Endpoint/Page:** WeatherPage (Frontend)
- **Description:** Weather cards don't display on mobile
- **Steps to Reproduce:**
  1. Open WeatherPage on mobile Chrome
  2. Search for "Chennai"
  3. Weather data loads but cards are invisible
- **Expected:** Weather cards display properly on mobile
- **Got:** Blank screen, but data is in console
- **Screenshot:** [Link or attach]
- **Device:** Samsung Galaxy A52, Chrome Android
- **Assigned to:** Sanjay
- **Notes:** Works fine on desktop

---

### BUG #3
- **Status:** 🔴 OPEN
- **Priority:** LOW
- **Found:** Day 5, Mar 2, 2026
- **Endpoint/Page:** ProfilePage
- **Description:** Phone number field accepts letters
- **Steps to Reproduce:**
  1. Open ProfilePage
  2. Type "abcd" in phone number field
  3. Form accepts it
- **Expected:** Only numbers allowed, validation error shown
- **Got:** Accepts any input
- **Screenshot:** [Link or attach]
- **Assigned to:** Sanjay
- **Notes:** Should add input type="tel" and validation

---

## Fixed Bugs (Awaiting Verification)

### BUG #4
- **Status:** 🟢 FIXED
- **Priority:** HIGH
- **Found:** Day 3, Feb 28, 2026
- **Fixed:** Day 4, Mar 1, 2026
- **Endpoint/Page:** GET /weather/{location}
- **Description:** Weather endpoint returns 404 for valid cities
- **Input:** GET /weather/Chennai
- **Expected:** Weather data for Chennai
- **Got:** 404 Not Found
- **Fix Applied:** Manoj fixed API Gateway route configuration
- **Assigned to:** Jeevidha (to verify)
- **Verification Status:** ⏳ Pending retest

---

## Verified Fixed Bugs ✅

### BUG #5
- **Status:** ✅ VERIFIED
- **Priority:** HIGH
- **Found:** Day 3, Feb 28, 2026
- **Fixed:** Day 3, Feb 28, 2026
- **Verified:** Day 4, Mar 1, 2026
- **Endpoint/Page:** GET /health
- **Description:** Health check endpoint not responding
- **Input:** GET /health
- **Expected:** `{"status": "healthy"}`
- **Got:** Connection timeout
- **Fix Applied:** Manoj redeployed Lambda with correct handler
- **Verified by:** Jeevidha
- **Verification Notes:** Works perfectly now, response time < 500ms

---

## Won't Fix / Out of Scope

### BUG #6
- **Status:** ❌ WONTFIX
- **Priority:** LOW
- **Found:** Day 5, Mar 2, 2026
- **Endpoint/Page:** ChatPage
- **Description:** Chat doesn't support voice messages in Odia language
- **Reason:** Odia not in scope for MVP, only 8 languages supported
- **Decision by:** Sanjay + Manoj
- **Notes:** Can add in future version if needed

---

## Bug Statistics

### By Priority
- **HIGH:** 2 open, 1 fixed, 1 verified
- **MEDIUM:** 1 open, 0 fixed, 0 verified
- **LOW:** 1 open, 0 fixed, 0 verified

### By Status
- **🔴 OPEN:** 3
- **🟡 IN PROGRESS:** 0
- **🟢 FIXED:** 1
- **✅ VERIFIED:** 1
- **❌ WONTFIX:** 1

### By Component
- **Backend API:** 2 bugs
- **Frontend:** 2 bugs
- **Integration:** 0 bugs

### By Day
- **Day 3:** 3 bugs found
- **Day 4:** 2 bugs found
- **Day 5:** 1 bug found

---

## Critical Issues Blocking Submission

List any bugs that MUST be fixed before submission:

1. ~~BUG #5 - Health check not working~~ ✅ FIXED
2. BUG #1 - Tamil language chat not working (HIGH priority)
3. [Add more as needed]

---

## Testing Notes

### Day 3 Notes
- API Gateway URL received: `https://abc123.execute-api.ap-south-1.amazonaws.com/Prod`
- Basic endpoints (health, weather, schemes) working
- Chat endpoint has issues with non-English languages
- Need to test more edge cases tomorrow

### Day 4 Notes
- Most backend bugs fixed
- Frontend responsive issues on mobile
- Image upload works but slow (15+ seconds)
- Profile page needs validation improvements

### Day 5 Notes
- E2E testing mostly successful
- Voice input works great on desktop
- Mobile testing revealed UI issues
- Performance is acceptable for demo

### Day 6 Notes
- All critical bugs fixed
- Medium priority bugs addressed
- Low priority bugs documented for future
- Ready for demo and submission

---

## Lessons Learned

### What Went Well
- Postman collection setup saved time
- Early testing caught critical bugs
- Good communication with Manoj and Sanjay
- Systematic approach helped track everything

### What Could Be Improved
- Should have tested mobile earlier
- Need more edge case testing
- Could use automated testing tools
- Better bug prioritization needed

### For Next Hackathon
- Set up testing environment on Day 0
- Create test data sets in advance
- Test mobile and desktop in parallel
- Use bug tracking tool (Jira/Trello) instead of markdown

---

*Last updated: February 26, 2026*
