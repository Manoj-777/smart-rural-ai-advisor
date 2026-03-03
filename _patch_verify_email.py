"""Patch translations.js: Add verify-email keys + loginEmailRequired for all 13 languages."""

TRANS_FILE = r"frontend\src\i18n\translations.js"

NEW_KEYS = {
    'en-IN': {
        'verifyEmailTitle': 'Verify Your Email',
        'verifyEmailSubtitle': 'We sent a 6-digit code to your email. Enter it below to verify your identity.',
        'verifyEmailBtn': 'Verify Email',
        'verifyEmailResend': 'Resend Code',
        'verifyEmailSkip': 'Skip for now',
        'verifyEmailSuccess': 'Email verified successfully! Entering the app...',
        'loginEmailRequired': 'Please enter a valid email for identity verification.',
        'signupEmailLabel': 'Email',
    },
    'ta-IN': {
        'verifyEmailTitle': 'உங்கள் மின்னஞ்சலை சரிபார்க்கவும்',
        'verifyEmailSubtitle': 'உங்கள் மின்னஞ்சலுக்கு 6 இலக்க குறியீடு அனுப்பப்பட்டது. அதை கீழே உள்ளிடவும்.',
        'verifyEmailBtn': 'மின்னஞ்சல் சரிபார்',
        'verifyEmailResend': 'குறியீட்டை மீண்டும் அனுப்பு',
        'verifyEmailSkip': 'பிறகு செய்யலாம்',
        'verifyEmailSuccess': 'மின்னஞ்சல் வெற்றிகரமாக சரிபார்க்கப்பட்டது!',
        'loginEmailRequired': 'சரிபார்ப்புக்கு சரியான மின்னஞ்சலை உள்ளிடவும்.',
        'signupEmailLabel': 'மின்னஞ்சல்',
    },
    'hi-IN': {
        'verifyEmailTitle': 'अपना ईमेल सत्यापित करें',
        'verifyEmailSubtitle': 'आपके ईमेल पर 6 अंकों का कोड भेजा गया है। नीचे दर्ज करें।',
        'verifyEmailBtn': 'ईमेल सत्यापित करें',
        'verifyEmailResend': 'कोड दोबारा भेजें',
        'verifyEmailSkip': 'बाद में करें',
        'verifyEmailSuccess': 'ईमेल सफलतापूर्वक सत्यापित हो गया!',
        'loginEmailRequired': 'सत्यापन के लिए वैध ईमेल दर्ज करें।',
        'signupEmailLabel': 'ईमेल',
    },
    'te-IN': {
        'verifyEmailTitle': 'మీ ఈమెయిల్ ధృవీకరించండి',
        'verifyEmailSubtitle': 'మీ ఈమెయిల్‌కు 6 అంకెల కోడ్ పంపబడింది. క్రింద నమోదు చేయండి.',
        'verifyEmailBtn': 'ఈమెయిల్ ధృవీకరించండి',
        'verifyEmailResend': 'కోడ్ మళ్ళీ పంపండి',
        'verifyEmailSkip': 'తర్వాత చేయండి',
        'verifyEmailSuccess': 'ఈమెయిల్ విజయవంతంగా ధృవీకరించబడింది!',
        'loginEmailRequired': 'ధృవీకరణ కోసం చెల్లుబాటు అయ్యే ఈమెయిల్ నమోదు చేయండి.',
        'signupEmailLabel': 'ఈమెయిల్',
    },
    'kn-IN': {
        'verifyEmailTitle': 'ನಿಮ್ಮ ಇಮೇಲ್ ಪರಿಶೀಲಿಸಿ',
        'verifyEmailSubtitle': 'ನಿಮ್ಮ ಇಮೇಲ್‌ಗೆ 6 ಅಂಕಿಯ ಕೋಡ್ ಕಳುಹಿಸಲಾಗಿದೆ. ಕೆಳಗೆ ನಮೂದಿಸಿ.',
        'verifyEmailBtn': 'ಇಮೇಲ್ ಪರಿಶೀಲಿಸಿ',
        'verifyEmailResend': 'ಕೋಡ್ ಮತ್ತೆ ಕಳುಹಿಸಿ',
        'verifyEmailSkip': 'ನಂತರ ಮಾಡಿ',
        'verifyEmailSuccess': 'ಇಮೇಲ್ ಯಶಸ್ವಿಯಾಗಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ!',
        'loginEmailRequired': 'ಪರಿಶೀಲನೆಗಾಗಿ ಮಾನ್ಯ ಇಮೇಲ್ ನಮೂದಿಸಿ.',
        'signupEmailLabel': 'ಇಮೇಲ್',
    },
    'ml-IN': {
        'verifyEmailTitle': 'നിങ്ങളുടെ ഇമെയിൽ പരിശോധിക്കുക',
        'verifyEmailSubtitle': 'നിങ്ങളുടെ ഇമെയിലിലേക്ക് 6 അക്ക കോഡ് അയച്ചു. ചുവടെ നൽകുക.',
        'verifyEmailBtn': 'ഇമെയിൽ പരിശോധിക്കുക',
        'verifyEmailResend': 'കോഡ് വീണ്ടും അയയ്ക്കുക',
        'verifyEmailSkip': 'പിന്നീട് ചെയ്യാം',
        'verifyEmailSuccess': 'ഇമെയിൽ വിജയകരമായി പരിശോധിച്ചു!',
        'loginEmailRequired': 'പരിശോധനയ്ക്ക് സാധുവായ ഇമെയിൽ നൽകുക.',
        'signupEmailLabel': 'ഇമെയിൽ',
    },
    'bn-IN': {
        'verifyEmailTitle': 'আপনার ইমেইল যাচাই করুন',
        'verifyEmailSubtitle': 'আপনার ইমেইলে 6 সংখ্যার কোড পাঠানো হয়েছে। নিচে দিন।',
        'verifyEmailBtn': 'ইমেইল যাচাই করুন',
        'verifyEmailResend': 'কোড আবার পাঠান',
        'verifyEmailSkip': 'পরে করব',
        'verifyEmailSuccess': 'ইমেইল সফলভাবে যাচাই হয়েছে!',
        'loginEmailRequired': 'যাচাইয়ের জন্য সঠিক ইমেইল দিন।',
        'signupEmailLabel': 'ইমেইল',
    },
    'mr-IN': {
        'verifyEmailTitle': 'तुमचा ईमेल सत्यापित करा',
        'verifyEmailSubtitle': 'तुमच्या ईमेलवर 6 अंकी कोड पाठवला. खाली टाका.',
        'verifyEmailBtn': 'ईमेल सत्यापित करा',
        'verifyEmailResend': 'कोड पुन्हा पाठवा',
        'verifyEmailSkip': 'नंतर करा',
        'verifyEmailSuccess': 'ईमेल यशस्वीरित्या सत्यापित झाला!',
        'loginEmailRequired': 'सत्यापनासाठी वैध ईमेल टाका.',
        'signupEmailLabel': 'ईमेल',
    },
    'gu-IN': {
        'verifyEmailTitle': 'તમારો ઈમેલ ચકાસો',
        'verifyEmailSubtitle': 'તમારા ઈમેલ પર 6 અંકનો કોડ મોકલ્યો. નીચે દાખલ કરો.',
        'verifyEmailBtn': 'ઈમેલ ચકાસો',
        'verifyEmailResend': 'કોડ ફરીથી મોકલો',
        'verifyEmailSkip': 'પછી કરો',
        'verifyEmailSuccess': 'ઈમેલ સફળતાપૂર્વક ચકાસાયો!',
        'loginEmailRequired': 'ચકાસણી માટે માન્ય ઈમેલ દાખલ કરો.',
        'signupEmailLabel': 'ઈમેલ',
    },
    'pa-IN': {
        'verifyEmailTitle': 'ਆਪਣਾ ਈਮੇਲ ਪੁਸ਼ਟੀ ਕਰੋ',
        'verifyEmailSubtitle': 'ਤੁਹਾਡੇ ਈਮੇਲ ਤੇ 6 ਅੰਕਾਂ ਦਾ ਕੋਡ ਭੇਜਿਆ। ਹੇਠਾਂ ਦਾਖਲ ਕਰੋ।',
        'verifyEmailBtn': 'ਈਮੇਲ ਪੁਸ਼ਟੀ ਕਰੋ',
        'verifyEmailResend': 'ਕੋਡ ਦੁਬਾਰਾ ਭੇਜੋ',
        'verifyEmailSkip': 'ਬਾਅਦ ਵਿੱਚ ਕਰੋ',
        'verifyEmailSuccess': 'ਈਮੇਲ ਸਫਲਤਾਪੂਰਵਕ ਪੁਸ਼ਟੀ ਹੋ ਗਈ!',
        'loginEmailRequired': 'ਪੁਸ਼ਟੀ ਲਈ ਸਹੀ ਈਮੇਲ ਦਾਖਲ ਕਰੋ।',
        'signupEmailLabel': 'ਈਮੇਲ',
    },
    'or-IN': {
        'verifyEmailTitle': 'ଆପଣଙ୍କ ଇମେଲ ଯାଞ୍ଚ କରନ୍ତୁ',
        'verifyEmailSubtitle': 'ଆପଣଙ୍କ ଇମେଲରେ 6 ସଂଖ୍ୟାର କୋଡ ପଠାଗଲା। ତଳେ ଦିଅନ୍ତୁ।',
        'verifyEmailBtn': 'ଇମେଲ ଯାଞ୍ଚ କରନ୍ତୁ',
        'verifyEmailResend': 'କୋଡ ପୁଣି ପଠାନ୍ତୁ',
        'verifyEmailSkip': 'ପରେ କରିବୁ',
        'verifyEmailSuccess': 'ଇମେଲ ସଫଳତାର ସହ ଯାଞ୍ଚ ହୋଇଗଲା!',
        'loginEmailRequired': 'ଯାଞ୍ଚ ପାଇଁ ବୈଧ ଇମେଲ ଦିଅନ୍ତୁ।',
        'signupEmailLabel': 'ଇମେଲ',
    },
    'as-IN': {
        'verifyEmailTitle': 'আপোনাৰ ইমেইল পৰীক্ষা কৰক',
        'verifyEmailSubtitle': 'আপোনাৰ ইমেইলত 6 সংখ্যাৰ কোড পঠিওৱা হৈছে। তলত দিয়ক।',
        'verifyEmailBtn': 'ইমেইল পৰীক্ষা কৰক',
        'verifyEmailResend': 'কোড পুনৰ পঠিয়াওক',
        'verifyEmailSkip': 'পিছত কৰিম',
        'verifyEmailSuccess': 'ইমেইল সফলভাৱে পৰীক্ষিত!',
        'loginEmailRequired': 'পৰীক্ষাৰ বাবে সঠিক ইমেইল দিয়ক।',
        'signupEmailLabel': 'ইমেইল',
    },
    'ur-IN': {
        'verifyEmailTitle': 'اپنا ای میل تصدیق کریں',
        'verifyEmailSubtitle': 'آپ کے ای میل پر 6 ہندسوں کا کوڈ بھیجا گیا۔ نیچے درج کریں۔',
        'verifyEmailBtn': 'ای میل تصدیق کریں',
        'verifyEmailResend': 'کوڈ دوبارہ بھیجیں',
        'verifyEmailSkip': 'بعد میں کریں',
        'verifyEmailSuccess': 'ای میل کامیابی سے تصدیق ہو گیا!',
        'loginEmailRequired': 'تصدیق کے لیے درست ای میل درج کریں۔',
        'signupEmailLabel': 'ای میل',
    },
}

with open(TRANS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

for lang_code, keys in NEW_KEYS.items():
    lines = []
    for key, val in keys.items():
        escaped_val = val.replace("'", "\\'")
        lines.append(f"        {key}: '{escaped_val}',")
    insert_text = "\n".join(lines)

    lang_pos = content.find(f"'{lang_code}':")
    if lang_pos == -1:
        print(f"WARNING: Could not find {lang_code}")
        continue

    marker = "changePinTooShort:"
    marker_pos = content.find(marker, lang_pos)
    if marker_pos == -1:
        print(f"WARNING: Could not find changePinTooShort for {lang_code}")
        continue

    line_end = content.find("\n", marker_pos)
    content = content[:line_end+1] + insert_text + "\n" + content[line_end+1:]
    print(f"Patched {lang_code}: {len(keys)} keys")

# Also update signupEmailLabel in English to remove "(optional)" since it's now required
content = content.replace(
    "signupEmailLabel: 'Email (optional \\u2014 for PIN recovery)',",
    "signupEmailLabel: 'Email',",
    1
)

with open(TRANS_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
