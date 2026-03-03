"""Patch translations.js with delete-profile keys for all 13 languages."""
import re

KEYS = {
    "deleteProfileTitle": {
        "en": "Delete Account",
        "ta": "கணக்கை நீக்கு",
        "hi": "खाता हटाएं",
        "te": "ఖాతా తొలగించు",
        "kn": "ಖಾತೆ ಅಳಿಸಿ",
        "ml": "അക്കൗണ്ട് ഡിലീറ്റ് ചെയ്യുക",
        "bn": "অ্যাকাউন্ট মুছুন",
        "mr": "खाते हटवा",
        "gu": "એકાઉન્ટ કાઢી નાખો",
        "pa": "ਖਾਤਾ ਮਿਟਾਓ",
        "or": "ଆକାଉଣ୍ଟ ବିଲୋପ କରନ୍ତୁ",
        "as": "একাউণ্ট মচি পেলাওক",
        "ur": "اکاؤنٹ حذف کریں"
    },
    "deleteProfileWarning": {
        "en": "This will permanently delete your profile, farm data, and login. This action cannot be undone.",
        "ta": "இது உங்கள் சுயவிவரம், பண்ணை தரவு மற்றும் உள்நுழைவை நிரந்தரமாக நீக்கும். இதை மீட்டெடுக்க முடியாது.",
        "hi": "यह आपकी प्रोफ़ाइल, खेत डेटा और लॉगिन को स्थायी रूप से हटा देगा। यह क्रिया पूर्ववत नहीं की जा सकती।",
        "te": "ఇది మీ ప్రొఫైల్, వ్యవసాయ డేటా మరియు లాగిన్‌ను శాశ్వతంగా తొలగిస్తుంది. ఈ చర్యను రద్దు చేయలేరు.",
        "kn": "ಇದು ನಿಮ್ಮ ಪ್ರೊಫೈಲ್, ಕೃಷಿ ಡೇಟಾ ಮತ್ತು ಲಾಗಿನ್ ಅನ್ನು ಶಾಶ್ವತವಾಗಿ ಅಳಿಸುತ್ತದೆ. ಈ ಕ್ರಿಯೆಯನ್ನು ರದ್ದುಗೊಳಿಸಲಾಗದು.",
        "ml": "ഇത് നിങ്ങളുടെ പ്രൊഫൈൽ, കൃഷി ഡാറ്റ, ലോഗിൻ എന്നിവ ശാശ്വതമായി ഡിലീറ്റ് ചെയ്യും. ഈ പ്രവൃത്തി പഴയപടിയാക്കാൻ കഴിയില്ല.",
        "bn": "এটি আপনার প্রোফাইল, কৃষি ডেটা এবং লগইন স্থায়ীভাবে মুছে ফেলবে। এই কাজ পূর্বাবস্থায় ফেরানো যাবে না।",
        "mr": "हे तुमचे प्रोफाइल, शेती डेटा आणि लॉगिन कायमस्वरूपी हटवेल. ही कृती पूर्ववत करता येणार नाही.",
        "gu": "આ તમારી પ્રોફાઈલ, ખેતી ડેટા અને લોગિન કાયમ માટે ડિલીટ કરશે. આ ક્રિયા પૂર્વવત કરી શકાશે નહીં.",
        "pa": "ਇਹ ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ, ਖੇਤੀ ਡੇਟਾ ਅਤੇ ਲੌਗਇਨ ਨੂੰ ਸਥਾਈ ਤੌਰ 'ਤੇ ਮਿਟਾ ਦੇਵੇਗਾ। ਇਸ ਕਾਰਵਾਈ ਨੂੰ ਵਾਪਸ ਨਹੀਂ ਕੀਤਾ ਜਾ ਸਕਦਾ।",
        "or": "ଏହା ଆପଣଙ୍କ ପ୍ରୋଫାଇଲ୍, କୃଷି ଡାଟା ଏବଂ ଲଗଇନ୍ ସ୍ଥାୟୀ ଭାବରେ ବିଲୋପ କରିବ। ଏହି କାର୍ଯ୍ୟକୁ ପୂର୍ବାବସ୍ଥାକୁ ଆଣି ହେବ ନାହିଁ।",
        "as": "এইটোৱে আপোনাৰ প্ৰ'ফাইল, কৃষি ডাটা আৰু লগইন স্থায়ীভাৱে মচি পেলাব। এই কাৰ্য্য পূৰ্বাৱস্থালৈ ঘূৰাব নোৱাৰি।",
        "ur": "یہ آپ کی پروفائل، زرعی ڈیٹا اور لاگ ان کو مستقل طور پر حذف کر دے گا۔ یہ عمل واپس نہیں کیا جا سکتا۔"
    },
    "deleteProfileBtn": {
        "en": "Delete My Account",
        "ta": "என் கணக்கை நீக்கு",
        "hi": "मेरा खाता हटाएं",
        "te": "నా ఖాతా తొలగించు",
        "kn": "ನನ್ನ ಖಾತೆ ಅಳಿಸಿ",
        "ml": "എന്റെ അക്കൗണ്ട് ഡിലീറ്റ് ചെയ്യുക",
        "bn": "আমার অ্যাকাউন্ট মুছুন",
        "mr": "माझे खाते हटवा",
        "gu": "મારું એકાઉન્ટ કાઢી નાખો",
        "pa": "ਮੇਰਾ ਖਾਤਾ ਮਿਟਾਓ",
        "or": "ମୋ ଆକାଉଣ୍ଟ ବିଲୋପ କରନ୍ତୁ",
        "as": "মোৰ একাউণ্ট মচি পেলাওক",
        "ur": "میرا اکاؤنٹ حذف کریں"
    },
    "deleteProfileConfirmText": {
        "en": "Type DELETE to confirm permanent deletion:",
        "ta": "நிரந்தர நீக்கத்தை உறுதிப்படுத்த DELETE என தட்டச்சு செய்யவும்:",
        "hi": "स्थायी रूप से हटाने की पुष्टि के लिए DELETE टाइप करें:",
        "te": "శాశ్వత తొలగింపును నిర్ధారించడానికి DELETE టైప్ చేయండి:",
        "kn": "ಶಾಶ್ವತ ಅಳಿಸುವಿಕೆಯನ್ನು ಖಚಿತಪಡಿಸಲು DELETE ಟೈಪ್ ಮಾಡಿ:",
        "ml": "ശാശ്വത ഡിലീഷൻ സ്ഥിരീകരിക്കാൻ DELETE ടൈപ്പ് ചെയ്യുക:",
        "bn": "স্থায়ী মুছে ফেলা নিশ্চিত করতে DELETE টাইপ করুন:",
        "mr": "कायमस्वरूपी हटवणे पुष्टी करण्यासाठी DELETE टाइप करा:",
        "gu": "કાયમી ડિલીશન ની પુષ્ટિ કરવા DELETE ટાઈપ કરો:",
        "pa": "ਸਥਾਈ ਮਿਟਾਉਣ ਦੀ ਪੁਸ਼ਟੀ ਲਈ DELETE ਟਾਈਪ ਕਰੋ:",
        "or": "ସ୍ଥାୟୀ ବିଲୋପ ନିଶ୍ଚିତ କରିବାକୁ DELETE ଟାଇପ୍ କରନ୍ତୁ:",
        "as": "স্থায়ী মচি পেলোৱা নিশ্চিত কৰিবলৈ DELETE টাইপ কৰক:",
        "ur": "مستقل حذف کی تصدیق کے لیے DELETE ٹائپ کریں:"
    },
    "deleteProfileTypePlaceholder": {
        "en": "Type DELETE here",
        "ta": "இங்கே DELETE என தட்டச்சு செய்யவும்",
        "hi": "यहां DELETE टाइप करें",
        "te": "ఇక్కడ DELETE టైప్ చేయండి",
        "kn": "ಇಲ್ಲಿ DELETE ಟೈಪ್ ಮಾಡಿ",
        "ml": "ഇവിടെ DELETE ടൈപ്പ് ചെയ്യുക",
        "bn": "এখানে DELETE টাইপ করুন",
        "mr": "येथे DELETE टाइप करा",
        "gu": "અહીં DELETE ટાઈપ કરો",
        "pa": "ਇੱਥੇ DELETE ਟਾਈਪ ਕਰੋ",
        "or": "ଏଠାରେ DELETE ଟାଇପ୍ କରନ୍ତୁ",
        "as": "ইয়াত DELETE টাইপ কৰক",
        "ur": "یہاں DELETE ٹائپ کریں"
    },
    "deleteProfileTypeMismatch": {
        "en": "Please type DELETE exactly to confirm",
        "ta": "உறுதிப்படுத்த DELETE என சரியாக தட்டச்சு செய்யவும்",
        "hi": "पुष्टि के लिए कृपया DELETE सही टाइप करें",
        "te": "నిర్ధారించడానికి దయచేసి DELETE సరిగ్గా టైప్ చేయండి",
        "kn": "ಖಚಿತಪಡಿಸಲು ದಯವಿಟ್ಟು DELETE ನಿಖರವಾಗಿ ಟೈಪ್ ಮಾಡಿ",
        "ml": "സ്ഥിരീകരിക്കാൻ ദയവായി DELETE കൃത്യമായി ടൈപ്പ് ചെയ്യുക",
        "bn": "নিশ্চিত করতে অনুগ্রহ করে DELETE সঠিকভাবে টাইপ করুন",
        "mr": "पुष्टीसाठी कृपया DELETE अचूक टाइप करा",
        "gu": "પુષ્ટિ કરવા કૃપા DELETE ચોક્કસ ટાઈપ કરો",
        "pa": "ਪੁਸ਼ਟੀ ਲਈ ਕਿਰਪਾ ਕਰਕੇ DELETE ਸਹੀ ਟਾਈਪ ਕਰੋ",
        "or": "ନିଶ୍ଚିତ କରିବାକୁ ଦୟାକରି DELETE ସଠିକ୍ ଟାଇପ୍ କରନ୍ତୁ",
        "as": "নিশ্চিত কৰিবলৈ অনুগ্ৰহ কৰি DELETE সঠিকভাৱে টাইপ কৰক",
        "ur": "تصدیق کے لیے براہ کرم DELETE صحیح ٹائپ کریں"
    },
    "deleteProfileCancel": {
        "en": "Cancel",
        "ta": "ரத்து செய்",
        "hi": "रद्द करें",
        "te": "రద్దు చేయి",
        "kn": "ರದ್ದುಮಾಡಿ",
        "ml": "റദ്ദാക്കുക",
        "bn": "বাতিল",
        "mr": "रद्द करा",
        "gu": "રદ કરો",
        "pa": "ਰੱਦ ਕਰੋ",
        "or": "ବାତିଲ କରନ୍ତୁ",
        "as": "বাতিল কৰক",
        "ur": "منسوخ کریں"
    },
    "deleteProfileConfirmBtn": {
        "en": "Permanently Delete",
        "ta": "நிரந்தரமாக நீக்கு",
        "hi": "स्थायी रूप से हटाएं",
        "te": "శాశ్వతంగా తొలగించు",
        "kn": "ಶಾಶ್ವತವಾಗಿ ಅಳಿಸಿ",
        "ml": "ശാശ്വതമായി ഡിലീറ്റ് ചെയ്യുക",
        "bn": "স্থায়ীভাবে মুছুন",
        "mr": "कायमस्वरूपी हटवा",
        "gu": "કાયમ માટે ડિલીટ કરો",
        "pa": "ਸਥਾਈ ਤੌਰ ਤੇ ਮਿਟਾਓ",
        "or": "ସ୍ଥାୟୀ ଭାବରେ ବିଲୋପ କରନ୍ତୁ",
        "as": "স্থায়ীভাৱে মচি পেলাওক",
        "ur": "مستقل طور پر حذف کریں"
    },
}

# Language code mapping (translations.js uses short codes)
LANG_MAP = {
    "en": "en", "ta": "ta", "hi": "hi", "te": "te", "kn": "kn",
    "ml": "ml", "bn": "bn", "mr": "mr", "gu": "gu", "pa": "pa",
    "or": "or", "as": "as", "ur": "ur"
}

file_path = "frontend/src/i18n/translations.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

count = 0
for key, langs in KEYS.items():
    for lang_short, text in langs.items():
        # Find the language block and insert before the closing }
        # Pattern: look for the language section header and add at the end
        # For each language block that looks like:  lang: { ... key: 'value', ... }
        # We need to find the right spot. Let's find the LAST key in each lang block
        # and add after it

        # Strategy: find  `key:` already exists? skip. Otherwise insert before
        # the closing of that language's object.
        # Simpler: search for an existing known key in each language block and add after it
        
        # Find pattern like:  verifyEmailSkip: '...'  in the lang block and add after
        # Actually let's just search-replace for a known key that exists in all blocks
        pass

# Better approach: just add all keys at once using a simpler pattern
# Find each language block by looking for the pattern: `  LANG: {` 
# and insert the new keys right before profileTip (which exists in all blocks)

for key, langs in KEYS.items():
    for lang_code, text in langs.items():
        # Escape single quotes in the text
        escaped = text.replace("'", "\\'")
        line = f"    {key}: '{escaped}',"
        
        # Check if key already exists for this language
        # Pattern: within the lang block, look for the key
        check = f"    {key}:"
        if check in content:
            # Already there for at least one language; skip if this lang's block already has it
            continue
        
    # If key not found at all, insert before profileTip in each lang block
    if f"    {key}:" not in content:
        for lang_code, text in langs.items():
            escaped = text.replace("'", "\\'")
            new_line = f"    {key}: '{escaped}',\n"
            # Find profileTip in this language's block
            # We know profileTip exists. Find it and insert before it
            # But we need to find the RIGHT profileTip (in the right lang block)
            # Better: use a unique anchor per language
            pass

# Simplest reliable approach: find each `profileTip:` line and insert before it
lines = content.split('\n')
new_lines = []
keys_to_add = list(KEYS.keys())

# Track which language block we're in
current_lang = None
lang_pattern = re.compile(r'^  (\w{2}): \{')
added_keys = set()

i = 0
while i < len(lines):
    line = lines[i]
    
    # Detect language block start
    m = lang_pattern.match(line)
    if m:
        current_lang = m.group(1)
    
    # Insert before profileTip line in each language block
    if current_lang and '    profileTip:' in line and current_lang not in added_keys:
        # Add all delete profile keys before profileTip
        for key in keys_to_add:
            if current_lang in KEYS[key]:
                text = KEYS[key][current_lang]
                escaped = text.replace("'", "\\'")
                new_lines.append(f"    {key}: '{escaped}',")
        added_keys.add(current_lang)
    
    new_lines.append(line)
    i += 1

content = '\n'.join(new_lines)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done! Added {len(keys_to_add)} keys x {len(added_keys)} languages = {len(keys_to_add) * len(added_keys)} entries")
