"""Add loginNotFound* translation keys to all 13 language blocks."""
import re

FILE = 'frontend/src/i18n/translations.js'

# New keys to add after loginNotRegistered in each language
TRANSLATIONS = {
    'en-IN': {
        'loginNotFoundTitle': "Account Not Found",
        'loginNotFoundMsg': "We couldn\\'t find an account with phone number +91 {phone}. Would you like to create a new account?",
        'loginNotFoundCreate': "Create New Account",
        'loginNotFoundRetry': "Try Different Number",
    },
    'ta-IN': {
        'loginNotFoundTitle': "கணக்கு கிடைக்கவில்லை",
        'loginNotFoundMsg': "+91 {phone} எண்ணில் கணக்கு இல்லை. புதிய கணக்கு உருவாக்க விரும்புகிறீர்களா?",
        'loginNotFoundCreate': "புதிய கணக்கு உருவாக்கு",
        'loginNotFoundRetry': "வேறு எண் முயற்சிக்கவும்",
    },
    'hi-IN': {
        'loginNotFoundTitle': "खाता नहीं मिला",
        'loginNotFoundMsg': "+91 {phone} नंबर पर कोई खाता नहीं मिला। क्या आप नया खाता बनाना चाहते हैं?",
        'loginNotFoundCreate': "नया खाता बनाएं",
        'loginNotFoundRetry': "दूसरा नंबर आज़माएं",
    },
    'te-IN': {
        'loginNotFoundTitle': "ఖాతా కనుగొనబడలేదు",
        'loginNotFoundMsg': "+91 {phone} నంబర్‌తో ఖాతా కనుగొనబడలేదు. కొత్త ఖాతా సృష్టించాలా?",
        'loginNotFoundCreate': "కొత్త ఖాతా సృష్టించు",
        'loginNotFoundRetry': "వేరే నంబర్ ప్రయత్నించండి",
    },
    'kn-IN': {
        'loginNotFoundTitle': "ಖಾತೆ ಕಂಡುಬಂದಿಲ್ಲ",
        'loginNotFoundMsg': "+91 {phone} ನಂಬರ್‌ನಲ್ಲಿ ಖಾತೆ ಕಂಡುಬಂದಿಲ್ಲ. ಹೊಸ ಖಾತೆ ರಚಿಸಬೇಕೇ?",
        'loginNotFoundCreate': "ಹೊಸ ಖಾತೆ ರಚಿಸಿ",
        'loginNotFoundRetry': "ಬೇರೆ ನಂಬರ್ ಪ್ರಯತ್ನಿಸಿ",
    },
    'ml-IN': {
        'loginNotFoundTitle': "അക്കൗണ്ട് കണ്ടെത്തിയില്ല",
        'loginNotFoundMsg': "+91 {phone} നമ്പറിൽ അക്കൗണ്ട് ഇല്ല. പുതിയ അക്കൗണ്ട് സൃഷ്ടിക്കണോ?",
        'loginNotFoundCreate': "പുതിയ അക്കൗണ്ട് സൃഷ്ടിക്കുക",
        'loginNotFoundRetry': "മറ്റൊരു നമ്പർ ശ്രമിക്കുക",
    },
    'bn-IN': {
        'loginNotFoundTitle': "অ্যাকাউন্ট পাওয়া যায়নি",
        'loginNotFoundMsg': "+91 {phone} নম্বরে কোনো অ্যাকাউন্ট নেই। নতুন অ্যাকাউন্ট তৈরি করতে চান?",
        'loginNotFoundCreate': "নতুন অ্যাকাউন্ট তৈরি করুন",
        'loginNotFoundRetry': "অন্য নম্বর চেষ্টা করুন",
    },
    'mr-IN': {
        'loginNotFoundTitle': "खाते सापडले नाही",
        'loginNotFoundMsg': "+91 {phone} नंबरवर खाते सापडले नाही. नवीन खाते तयार करायचे आहे का?",
        'loginNotFoundCreate': "नवीन खाते तयार करा",
        'loginNotFoundRetry': "दुसरा नंबर प्रयत्न करा",
    },
    'gu-IN': {
        'loginNotFoundTitle': "એકાઉન્ટ મળ્યું નથી",
        'loginNotFoundMsg': "+91 {phone} નંબર પર એકાઉન્ટ મળ્યું નથી. નવું એકાઉન્ટ બનાવવું છે?",
        'loginNotFoundCreate': "નવું એકાઉન્ટ બનાવો",
        'loginNotFoundRetry': "બીજો નંબર અજમાવો",
    },
    'pa-IN': {
        'loginNotFoundTitle': "ਖਾਤਾ ਨਹੀਂ ਮਿਲਿਆ",
        'loginNotFoundMsg': "+91 {phone} ਨੰਬਰ ਤੇ ਕੋਈ ਖਾਤਾ ਨਹੀਂ ਮਿਲਿਆ। ਨਵਾਂ ਖਾਤਾ ਬਣਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
        'loginNotFoundCreate': "ਨਵਾਂ ਖਾਤਾ ਬਣਾਓ",
        'loginNotFoundRetry': "ਹੋਰ ਨੰਬਰ ਅਜ਼ਮਾਓ",
    },
    'or-IN': {
        'loginNotFoundTitle': "ଆକାଉଣ୍ଟ ମିଳିଲା ନାହିଁ",
        'loginNotFoundMsg': "+91 {phone} ନମ୍ବରରେ ଆକାଉଣ୍ଟ ନାହିଁ। ନୂଆ ଆକାଉଣ୍ଟ ସୃଷ୍ଟି କରିବେ କି?",
        'loginNotFoundCreate': "ନୂଆ ଆକାଉଣ୍ଟ ସୃଷ୍ଟି କରନ୍ତୁ",
        'loginNotFoundRetry': "ଅନ୍ୟ ନମ୍ବର ଚେଷ୍ଟା କରନ୍ତୁ",
    },
    'as-IN': {
        'loginNotFoundTitle': "একাউণ্ট পোৱা নগ'ল",
        'loginNotFoundMsg': "+91 {phone} নম্বৰত একাউণ্ট পোৱা নগ'ল। নতুন একাউণ্ট সৃষ্টি কৰিব বিচাৰে নে?",
        'loginNotFoundCreate': "নতুন একাউণ্ট সৃষ্টি কৰক",
        'loginNotFoundRetry': "আন নম্বৰ চেষ্টা কৰক",
    },
    'ur-IN': {
        'loginNotFoundTitle': "اکاؤنٹ نہیں ملا",
        'loginNotFoundMsg': "+91 {phone} نمبر پر کوئی اکاؤنٹ نہیں ملا۔ نیا اکاؤنٹ بنانا چاہتے ہیں؟",
        'loginNotFoundCreate': "نیا اکاؤنٹ بنائیں",
        'loginNotFoundRetry': "دوسرا نمبر آزمائیں",
    },
}

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

count = 0
for lang, keys in TRANSLATIONS.items():
    # Find loginNotRegistered line for this language block and add after it
    lines = []
    for k, v in keys.items():
        lines.append(f"        {k}: '{v}',")
    insert_text = '\n'.join(lines)

    # Match the loginNotRegistered line (unique per block due to different translations)
    pattern = re.compile(
        r"(        loginNotRegistered: '" + re.escape(keys.get('_anchor', '')) + r"[^']*',)"
        if '_anchor' in keys else
        r"(        loginNotRegistered: '[^']*',)",
    )

    # We need to replace them one at a time in order
    # Find the Nth occurrence (by language order)
    matches = list(pattern.finditer(content))
    if count < len(matches):
        m = matches[count]
        old = m.group(0)
        new = old + '\n' + insert_text
        # Replace only this specific occurrence by position
        content = content[:m.start()] + new + content[m.end():]
        count += 1
        print(f'  ✓ {lang}')
    else:
        print(f'  ✗ {lang} — could not find match #{count}')

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nDone — {count} language blocks updated')
