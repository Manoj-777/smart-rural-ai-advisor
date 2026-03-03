"""
Patch translations.js & cognitoAuth.js:
  - Add Change PIN keys + email keys + updated forgot-pin hints for all 13 languages
"""
import re, json

TRANS_FILE = r"frontend\src\i18n\translations.js"

# New keys to add to each language block (after the last forgotPin key)
NEW_KEYS = {
    'en-IN': {
        'changePinTitle': 'Change PIN',
        'changePinSubtitle': 'Update your login PIN for security.',
        'changePinOldLabel': 'Current PIN',
        'changePinOldPlaceholder': 'Enter current PIN',
        'changePinNewLabel': 'New PIN',
        'changePinNewPlaceholder': 'Enter new 6-digit PIN',
        'changePinConfirmLabel': 'Confirm New PIN',
        'changePinConfirmPlaceholder': 'Re-enter new PIN',
        'changePinBtn': 'Update PIN',
        'changePinSuccess': 'PIN changed successfully!',
        'changePinMismatch': 'New PINs do not match.',
        'changePinWrongOld': 'Current PIN is incorrect.',
        'changePinTooShort': 'PIN must be at least 6 characters.',
        'profileEmailLabel': 'Email (optional)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'Adding email enables easy PIN recovery.',
        'signupEmailLabel': 'Email (optional — for PIN recovery)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'Enter your registered phone number. We will send an OTP to your email to reset your PIN.',
        'forgotPinOtpSentEmail': 'We sent an OTP to your registered email. Enter it below with your new PIN.',
    },
    'ta-IN': {
        'changePinTitle': 'PIN மாற்று',
        'changePinSubtitle': 'பாதுகாப்பிற்காக உங்கள் உள்நுழைவு PIN-ஐ புதுப்பிக்கவும்.',
        'changePinOldLabel': 'தற்போதைய PIN',
        'changePinOldPlaceholder': 'தற்போதைய PIN உள்ளிடவும்',
        'changePinNewLabel': 'புதிய PIN',
        'changePinNewPlaceholder': 'புதிய 6 இலக்க PIN உள்ளிடவும்',
        'changePinConfirmLabel': 'புதிய PIN உறுதிப்படுத்து',
        'changePinConfirmPlaceholder': 'புதிய PIN மீண்டும் உள்ளிடவும்',
        'changePinBtn': 'PIN புதுப்பிக்கவும்',
        'changePinSuccess': 'PIN வெற்றிகரமாக மாற்றப்பட்டது!',
        'changePinMismatch': 'புதிய PIN-கள் பொருந்தவில்லை.',
        'changePinWrongOld': 'தற்போதைய PIN தவறானது.',
        'changePinTooShort': 'PIN குறைந்தது 6 எழுத்துகள் இருக்க வேண்டும்.',
        'profileEmailLabel': 'மின்னஞ்சல் (விருப்பத்தேர்வு)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'மின்னஞ்சல் சேர்ப்பது எளிய PIN மீட்புக்கு உதவுகிறது.',
        'signupEmailLabel': 'மின்னஞ்சல் (விருப்பம் — PIN மீட்புக்கு)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'உங்கள் பதிவு செய்யப்பட்ட தொலைபேசி எண்ணை உள்ளிடவும். PIN மீட்டமைக்க உங்கள் மின்னஞ்சலுக்கு OTP அனுப்புவோம்.',
        'forgotPinOtpSentEmail': 'உங்கள் பதிவு செய்யப்பட்ட மின்னஞ்சலுக்கு OTP அனுப்பப்பட்டது. கீழே உள்ளிடவும்.',
    },
    'hi-IN': {
        'changePinTitle': 'PIN बदलें',
        'changePinSubtitle': 'सुरक्षा के लिए अपना लॉगिन PIN अपडेट करें।',
        'changePinOldLabel': 'वर्तमान PIN',
        'changePinOldPlaceholder': 'वर्तमान PIN दर्ज करें',
        'changePinNewLabel': 'नया PIN',
        'changePinNewPlaceholder': 'नया 6 अंकों का PIN दर्ज करें',
        'changePinConfirmLabel': 'नया PIN पुष्टि करें',
        'changePinConfirmPlaceholder': 'नया PIN दोबारा दर्ज करें',
        'changePinBtn': 'PIN अपडेट करें',
        'changePinSuccess': 'PIN सफलतापूर्वक बदला गया!',
        'changePinMismatch': 'नए PIN मेल नहीं खाते।',
        'changePinWrongOld': 'वर्तमान PIN गलत है।',
        'changePinTooShort': 'PIN कम से कम 6 अक्षर होना चाहिए।',
        'profileEmailLabel': 'ईमेल (वैकल्पिक)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ईमेल जोड़ने से आसान PIN रिकवरी संभव होती है।',
        'signupEmailLabel': 'ईमेल (वैकल्पिक — PIN रिकवरी के लिए)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'अपना पंजीकृत फोन नंबर दर्ज करें। PIN रीसेट करने के लिए हम आपके ईमेल पर OTP भेजेंगे।',
        'forgotPinOtpSentEmail': 'आपके पंजीकृत ईमेल पर OTP भेजा गया है। नीचे दर्ज करें।',
    },
    'te-IN': {
        'changePinTitle': 'PIN మార్చు',
        'changePinSubtitle': 'భద్రత కోసం మీ లాగిన్ PIN అప్‌డేట్ చేయండి.',
        'changePinOldLabel': 'ప్రస్తుత PIN',
        'changePinOldPlaceholder': 'ప్రస్తుత PIN నమోదు చేయండి',
        'changePinNewLabel': 'కొత్త PIN',
        'changePinNewPlaceholder': 'కొత్త 6 అంకెల PIN నమోదు చేయండి',
        'changePinConfirmLabel': 'కొత్త PIN నిర్ధారించండి',
        'changePinConfirmPlaceholder': 'కొత్త PIN మళ్ళీ నమోదు చేయండి',
        'changePinBtn': 'PIN అప్‌డేట్ చేయండి',
        'changePinSuccess': 'PIN విజయవంతంగా మార్చబడింది!',
        'changePinMismatch': 'కొత్త PINలు సరిపోలలేదు.',
        'changePinWrongOld': 'ప్రస్తుత PIN తప్పు.',
        'changePinTooShort': 'PIN కనీసం 6 అక్షరాలు ఉండాలి.',
        'profileEmailLabel': 'ఈమెయిల్ (ఐచ్ఛికం)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ఈమెయిల్ చేర్చడం సులభంగా PIN రికవరీ చేయడానికి అనుమతిస్తుంది.',
        'signupEmailLabel': 'ఈమెయిల్ (ఐచ్ఛికం — PIN రికవరీ కోసం)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'మీ రిజిస్టర్ చేసిన ఫోన్ నంబర్ నమోదు చేయండి. PIN రీసెట్ చేయడానికి మీ ఈమెయిల్‌కు OTP పంపుతాము.',
        'forgotPinOtpSentEmail': 'మీ రిజిస్టర్ చేసిన ఈమెయిల్‌కు OTP పంపబడింది. క్రింద నమోదు చేయండి.',
    },
    'kn-IN': {
        'changePinTitle': 'PIN ಬದಲಾಯಿಸಿ',
        'changePinSubtitle': 'ಭದ್ರತೆಗಾಗಿ ನಿಮ್ಮ ಲಾಗಿನ್ PIN ನವೀಕರಿಸಿ.',
        'changePinOldLabel': 'ಪ್ರಸ್ತುತ PIN',
        'changePinOldPlaceholder': 'ಪ್ರಸ್ತುತ PIN ನಮೂದಿಸಿ',
        'changePinNewLabel': 'ಹೊಸ PIN',
        'changePinNewPlaceholder': 'ಹೊಸ 6 ಅಂಕಿಯ PIN ನಮೂದಿಸಿ',
        'changePinConfirmLabel': 'ಹೊಸ PIN ದೃಢೀಕರಿಸಿ',
        'changePinConfirmPlaceholder': 'ಹೊಸ PIN ಮತ್ತೆ ನಮೂದಿಸಿ',
        'changePinBtn': 'PIN ನವೀಕರಿಸಿ',
        'changePinSuccess': 'PIN ಯಶಸ್ವಿಯಾಗಿ ಬದಲಾಯಿಸಲಾಗಿದೆ!',
        'changePinMismatch': 'ಹೊಸ PINಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ.',
        'changePinWrongOld': 'ಪ್ರಸ್ತುತ PIN ತಪ್ಪಾಗಿದೆ.',
        'changePinTooShort': 'PIN ಕನಿಷ್ಠ 6 ಅಕ್ಷರಗಳಾಗಿರಬೇಕು.',
        'profileEmailLabel': 'ಇಮೇಲ್ (ಐಚ್ಛಿಕ)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ಇಮೇಲ್ ಸೇರಿಸುವುದು ಸುಲಭ PIN ಮರುಪಡೆಯುವಿಕೆಗೆ ಸಹಾಯ ಮಾಡುತ್ತದೆ.',
        'signupEmailLabel': 'ಇಮೇಲ್ (ಐಚ್ಛಿಕ — PIN ಮರುಪಡೆಯುವಿಕೆಗೆ)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'ನಿಮ್ಮ ನೋಂದಾಯಿತ ಫೋನ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ. PIN ಮರುಹೊಂದಿಸಲು ನಿಮ್ಮ ಇಮೇಲ್‌ಗೆ OTP ಕಳುಹಿಸುತ್ತೇವೆ.',
        'forgotPinOtpSentEmail': 'ನಿಮ್ಮ ನೋಂದಾಯಿತ ಇಮೇಲ್‌ಗೆ OTP ಕಳುಹಿಸಲಾಗಿದೆ. ಕೆಳಗೆ ನಮೂದಿಸಿ.',
    },
    'ml-IN': {
        'changePinTitle': 'PIN മാറ്റുക',
        'changePinSubtitle': 'സുരക്ഷയ്ക്കായി നിങ്ങളുടെ ലോഗിൻ PIN അപ്‌ഡേറ്റ് ചെയ്യുക.',
        'changePinOldLabel': 'നിലവിലെ PIN',
        'changePinOldPlaceholder': 'നിലവിലെ PIN നൽകുക',
        'changePinNewLabel': 'പുതിയ PIN',
        'changePinNewPlaceholder': 'പുതിയ 6 അക്ക PIN നൽകുക',
        'changePinConfirmLabel': 'പുതിയ PIN സ്ഥിരീകരിക്കുക',
        'changePinConfirmPlaceholder': 'പുതിയ PIN വീണ്ടും നൽകുക',
        'changePinBtn': 'PIN അപ്‌ഡേറ്റ് ചെയ്യുക',
        'changePinSuccess': 'PIN വിജയകരമായി മാറ്റി!',
        'changePinMismatch': 'പുതിയ PINകൾ പൊരുത്തപ്പെടുന്നില്ല.',
        'changePinWrongOld': 'നിലവിലെ PIN തെറ്റാണ്.',
        'changePinTooShort': 'PIN കുറഞ്ഞത് 6 അക്ഷരങ്ങൾ ആയിരിക്കണം.',
        'profileEmailLabel': 'ഇമെയിൽ (ഐച്ഛികം)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ഇമെയിൽ ചേർക്കുന്നത് എളുപ്പത്തിൽ PIN വീണ്ടെടുക്കാൻ സഹായിക്കുന്നു.',
        'signupEmailLabel': 'ഇമെയിൽ (ഐച്ഛികം — PIN വീണ്ടെടുക്കലിന്)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'നിങ്ങളുടെ രജിസ്റ്റർ ചെയ്ത ഫോൺ നമ്പർ നൽകുക. PIN റീസെറ്റ് ചെയ്യാൻ നിങ്ങളുടെ ഇമെയിലിലേക്ക് OTP അയയ്ക്കും.',
        'forgotPinOtpSentEmail': 'നിങ്ങളുടെ രജിസ്റ്റർ ചെയ്ത ഇമെയിലിലേക്ക് OTP അയച്ചു. ചുവടെ നൽകുക.',
    },
    'bn-IN': {
        'changePinTitle': 'PIN পরিবর্তন',
        'changePinSubtitle': 'নিরাপত্তার জন্য আপনার লগইন PIN আপডেট করুন।',
        'changePinOldLabel': 'বর্তমান PIN',
        'changePinOldPlaceholder': 'বর্তমান PIN দিন',
        'changePinNewLabel': 'নতুন PIN',
        'changePinNewPlaceholder': 'নতুন 6 সংখ্যার PIN দিন',
        'changePinConfirmLabel': 'নতুন PIN নিশ্চিত করুন',
        'changePinConfirmPlaceholder': 'নতুন PIN আবার দিন',
        'changePinBtn': 'PIN আপডেট করুন',
        'changePinSuccess': 'PIN সফলভাবে পরিবর্তন হয়েছে!',
        'changePinMismatch': 'নতুন PINগুলি মেলেনি।',
        'changePinWrongOld': 'বর্তমান PIN ভুল।',
        'changePinTooShort': 'PIN কমপক্ষে 6 অক্ষর হতে হবে।',
        'profileEmailLabel': 'ইমেইল (ঐচ্ছিক)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ইমেইল যোগ করলে সহজে PIN পুনরুদ্ধার করা যায়।',
        'signupEmailLabel': 'ইমেইল (ঐচ্ছিক — PIN পুনরুদ্ধারের জন্য)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'আপনার নিবন্ধিত ফোন নম্বর দিন। PIN রিসেট করতে আপনার ইমেইলে OTP পাঠাব।',
        'forgotPinOtpSentEmail': 'আপনার নিবন্ধিত ইমেইলে OTP পাঠানো হয়েছে। নিচে দিন।',
    },
    'mr-IN': {
        'changePinTitle': 'PIN बदला',
        'changePinSubtitle': 'सुरक्षिततेसाठी तुमचा लॉगिन PIN अपडेट करा.',
        'changePinOldLabel': 'सध्याचा PIN',
        'changePinOldPlaceholder': 'सध्याचा PIN टाका',
        'changePinNewLabel': 'नवीन PIN',
        'changePinNewPlaceholder': 'नवीन 6 अंकी PIN टाका',
        'changePinConfirmLabel': 'नवीन PIN पुष्टी करा',
        'changePinConfirmPlaceholder': 'नवीन PIN पुन्हा टाका',
        'changePinBtn': 'PIN अपडेट करा',
        'changePinSuccess': 'PIN यशस्वीरित्या बदलला!',
        'changePinMismatch': 'नवीन PIN जुळत नाहीत.',
        'changePinWrongOld': 'सध्याचा PIN चुकीचा आहे.',
        'changePinTooShort': 'PIN किमान 6 अक्षरे असणे आवश्यक आहे.',
        'profileEmailLabel': 'ईमेल (पर्यायी)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ईमेल जोडल्यास सहज PIN पुनर्प्राप्ती शक्य होते.',
        'signupEmailLabel': 'ईमेल (पर्यायी — PIN पुनर्प्राप्तीसाठी)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'तुमचा नोंदणीकृत फोन नंबर टाका. PIN रीसेट करण्यासाठी तुमच्या ईमेलवर OTP पाठवू.',
        'forgotPinOtpSentEmail': 'तुमच्या नोंदणीकृत ईमेलवर OTP पाठवला. खाली टाका.',
    },
    'gu-IN': {
        'changePinTitle': 'PIN બદલો',
        'changePinSubtitle': 'સુરક્ષા માટે તમારો લોગિન PIN અપડેટ કરો.',
        'changePinOldLabel': 'વર્તમાન PIN',
        'changePinOldPlaceholder': 'વર્તમાન PIN દાખલ કરો',
        'changePinNewLabel': 'નવો PIN',
        'changePinNewPlaceholder': 'નવો 6 અંકનો PIN દાખલ કરો',
        'changePinConfirmLabel': 'નવો PIN ખાતરી કરો',
        'changePinConfirmPlaceholder': 'નવો PIN ફરીથી દાખલ કરો',
        'changePinBtn': 'PIN અપડેટ કરો',
        'changePinSuccess': 'PIN સફળતાપૂર્વક બદલાયો!',
        'changePinMismatch': 'નવા PIN મેળ ખાતા નથી.',
        'changePinWrongOld': 'વર્તમાન PIN ખોટો છે.',
        'changePinTooShort': 'PIN ઓછામાં ઓછા 6 અક્ષરો હોવા જોઈએ.',
        'profileEmailLabel': 'ઈમેલ (વૈકલ્પિક)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ઈમેલ ઉમેરવાથી સરળ PIN પુનઃપ્રાપ્તિ શક્ય બને છે.',
        'signupEmailLabel': 'ઈમેલ (વૈકલ્પિક — PIN પુનઃપ્રાપ્તિ માટે)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'તમારો નોંધાયેલ ફોન નંબર દાખલ કરો. PIN રીસેટ કરવા ઈમેલ પર OTP મોકલીશું.',
        'forgotPinOtpSentEmail': 'તમારા નોંધાયેલ ઈમેલ પર OTP મોકલ્યો. નીચે દાખલ કરો.',
    },
    'pa-IN': {
        'changePinTitle': 'PIN ਬਦਲੋ',
        'changePinSubtitle': 'ਸੁਰੱਖਿਆ ਲਈ ਆਪਣਾ ਲੌਗਿਨ PIN ਅੱਪਡੇਟ ਕਰੋ।',
        'changePinOldLabel': 'ਮੌਜੂਦਾ PIN',
        'changePinOldPlaceholder': 'ਮੌਜੂਦਾ PIN ਦਾਖਲ ਕਰੋ',
        'changePinNewLabel': 'ਨਵਾਂ PIN',
        'changePinNewPlaceholder': 'ਨਵਾਂ 6 ਅੰਕਾਂ ਦਾ PIN ਦਾਖਲ ਕਰੋ',
        'changePinConfirmLabel': 'ਨਵਾਂ PIN ਪੁਸ਼ਟੀ ਕਰੋ',
        'changePinConfirmPlaceholder': 'ਨਵਾਂ PIN ਦੁਬਾਰਾ ਦਾਖਲ ਕਰੋ',
        'changePinBtn': 'PIN ਅੱਪਡੇਟ ਕਰੋ',
        'changePinSuccess': 'PIN ਸਫਲਤਾਪੂਰਵਕ ਬਦਲਿਆ ਗਿਆ!',
        'changePinMismatch': 'ਨਵੇਂ PIN ਮੇਲ ਨਹੀਂ ਖਾਂਦੇ।',
        'changePinWrongOld': 'ਮੌਜੂਦਾ PIN ਗਲਤ ਹੈ।',
        'changePinTooShort': 'PIN ਘੱਟੋ-ਘੱਟ 6 ਅੱਖਰ ਹੋਣੇ ਚਾਹੀਦੇ।',
        'profileEmailLabel': 'ਈਮੇਲ (ਵਿਕਲਪਿਕ)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ਈਮੇਲ ਜੋੜਨ ਨਾਲ ਆਸਾਨ PIN ਰਿਕਵਰੀ ਹੋ ਸਕਦੀ ਹੈ।',
        'signupEmailLabel': 'ਈਮੇਲ (ਵਿਕਲਪਿਕ — PIN ਰਿਕਵਰੀ ਲਈ)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'ਆਪਣਾ ਰਜਿਸਟਰਡ ਫੋਨ ਨੰਬਰ ਦਾਖਲ ਕਰੋ। PIN ਰੀਸੈੱਟ ਕਰਨ ਲਈ ਈਮੇਲ ਤੇ OTP ਭੇਜਾਂਗੇ।',
        'forgotPinOtpSentEmail': 'ਤੁਹਾਡੇ ਰਜਿਸਟਰਡ ਈਮੇਲ ਤੇ OTP ਭੇਜਿਆ। ਹੇਠਾਂ ਦਾਖਲ ਕਰੋ।',
    },
    'or-IN': {
        'changePinTitle': 'PIN ବଦଳାନ୍ତୁ',
        'changePinSubtitle': 'ସୁରକ୍ଷା ପାଇଁ ଆପଣଙ୍କ ଲଗଇନ PIN ଅପଡେଟ କରନ୍ତୁ।',
        'changePinOldLabel': 'ବର୍ତ୍ତମାନର PIN',
        'changePinOldPlaceholder': 'ବର୍ତ୍ତମାନର PIN ଦିଅନ୍ତୁ',
        'changePinNewLabel': 'ନୂଆ PIN',
        'changePinNewPlaceholder': 'ନୂଆ 6 ସଂଖ୍ୟାର PIN ଦିଅନ୍ତୁ',
        'changePinConfirmLabel': 'ନୂଆ PIN ନିଶ୍ଚିତ କରନ୍ତୁ',
        'changePinConfirmPlaceholder': 'ନୂଆ PIN ପୁଣି ଦିଅନ୍ତୁ',
        'changePinBtn': 'PIN ଅପଡେଟ କରନ୍ତୁ',
        'changePinSuccess': 'PIN ସଫଳତାର ସହ ବଦଳାଗଲା!',
        'changePinMismatch': 'ନୂଆ PINଗୁଡିକ ମେଳ ଖାଉନାହିଁ।',
        'changePinWrongOld': 'ବର୍ତ୍ତମାନର PIN ଭୁଲ।',
        'changePinTooShort': 'PIN ଅତିକମରେ 6 ଅକ୍ଷର ହେବା ଆବଶ୍ୟକ।',
        'profileEmailLabel': 'ଇମେଲ (ଐଚ୍ଛିକ)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ଇମେଲ ଯୋଡିଲେ ସହଜରେ PIN ପୁନରୁଦ୍ଧାର ସମ୍ଭବ।',
        'signupEmailLabel': 'ଇମେଲ (ଐଚ୍ଛିକ — PIN ପୁନରୁଦ୍ଧାର ପାଇଁ)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'ଆପଣଙ୍କ ପଞ୍ଜୀକୃତ ଫୋନ ନମ୍ବର ଦିଅନ୍ତୁ। PIN ରିସେଟ ପାଇଁ ଇମେଲରେ OTP ପଠାଇବୁ।',
        'forgotPinOtpSentEmail': 'ଆପଣଙ୍କ ପଞ୍ଜୀକୃତ ଇମେଲରେ OTP ପଠାଗଲା। ତଳେ ଦିଅନ୍ତୁ।',
    },
    'as-IN': {
        'changePinTitle': 'PIN সলনি কৰক',
        'changePinSubtitle': 'সুৰক্ষাৰ বাবে আপোনাৰ লগইন PIN আপডেট কৰক।',
        'changePinOldLabel': 'বৰ্তমান PIN',
        'changePinOldPlaceholder': 'বৰ্তমান PIN দিয়ক',
        'changePinNewLabel': 'নতুন PIN',
        'changePinNewPlaceholder': 'নতুন 6 সংখ্যাৰ PIN দিয়ক',
        'changePinConfirmLabel': 'নতুন PIN নিশ্চিত কৰক',
        'changePinConfirmPlaceholder': 'নতুন PIN পুনৰ দিয়ক',
        'changePinBtn': 'PIN আপডেট কৰক',
        'changePinSuccess': 'PIN সফলভাৱে সলনি হ\'ল!',
        'changePinMismatch': 'নতুন PINবোৰ মিলা নাই।',
        'changePinWrongOld': 'বৰ্তমান PIN ভুল।',
        'changePinTooShort': 'PIN কমেও 6 আখৰ হ\'ব লাগিব।',
        'profileEmailLabel': 'ইমেইল (ঐচ্ছিক)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ইমেইল যোগ কৰিলে সহজে PIN পুনৰুদ্ধাৰ কৰিব পাৰি।',
        'signupEmailLabel': 'ইমেইল (ঐচ্ছিক — PIN পুনৰুদ্ধাৰৰ বাবে)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'আপোনাৰ পঞ্জীকৃত ফোন নম্বৰ দিয়ক। PIN ৰিছেট কৰিবলৈ ইমেইলত OTP পঠিয়াম।',
        'forgotPinOtpSentEmail': 'আপোনাৰ পঞ্জীকৃত ইমেইলত OTP পঠিওৱা হৈছে। তলত দিয়ক।',
    },
    'ur-IN': {
        'changePinTitle': 'PIN تبدیل کریں',
        'changePinSubtitle': 'سیکیورٹی کے لیے اپنا لاگ ان PIN اپڈیٹ کریں۔',
        'changePinOldLabel': 'موجودہ PIN',
        'changePinOldPlaceholder': 'موجودہ PIN درج کریں',
        'changePinNewLabel': 'نیا PIN',
        'changePinNewPlaceholder': 'نیا 6 ہندسوں کا PIN درج کریں',
        'changePinConfirmLabel': 'نیا PIN تصدیق کریں',
        'changePinConfirmPlaceholder': 'نیا PIN دوبارہ درج کریں',
        'changePinBtn': 'PIN اپڈیٹ کریں',
        'changePinSuccess': 'PIN کامیابی سے تبدیل ہو گیا!',
        'changePinMismatch': 'نئے PIN مماثل نہیں ہیں۔',
        'changePinWrongOld': 'موجودہ PIN غلط ہے۔',
        'changePinTooShort': 'PIN کم از کم 6 حروف ہونا چاہیے۔',
        'profileEmailLabel': 'ای میل (اختیاری)',
        'profileEmailPlaceholder': 'your@email.com',
        'profileEmailHint': 'ای میل شامل کرنے سے آسان PIN بازیابی ممکن ہوتی ہے۔',
        'signupEmailLabel': 'ای میل (اختیاری — PIN بازیابی کے لیے)',
        'signupEmailPlaceholder': 'your@email.com',
        'forgotPinHintEmail': 'اپنا رجسٹرڈ فون نمبر درج کریں۔ PIN ری سیٹ کرنے کے لیے ای میل پر OTP بھیجیں گے۔',
        'forgotPinOtpSentEmail': 'آپ کے رجسٹرڈ ای میل پر OTP بھیجا گیا۔ نیچے درج کریں۔',
    },
}

# Read the file
with open(TRANS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# For each language, find the forgotPinLimitExceeded line and insert new keys after it
for lang_code, keys in NEW_KEYS.items():
    # Build the insertion text
    lines = []
    for key, val in keys.items():
        # Escape single quotes in value
        escaped_val = val.replace("'", "\\'")
        lines.append(f"        {key}: '{escaped_val}',")
    insert_text = "\n".join(lines)

    # Find the forgotPinLimitExceeded line for this language block
    # We'll search for the pattern within that language's section
    # Strategy: find the lang key, then find forgotPinLimitExceeded after it
    lang_pos = content.find(f"'{lang_code}':")
    if lang_pos == -1:
        print(f"WARNING: Could not find language block for {lang_code}")
        continue

    # Find forgotPinLimitExceeded after lang_pos
    marker = "forgotPinLimitExceeded:"
    marker_pos = content.find(marker, lang_pos)
    if marker_pos == -1:
        print(f"WARNING: Could not find forgotPinLimitExceeded for {lang_code}")
        continue

    # Find the end of that line
    line_end = content.find("\n", marker_pos)
    if line_end == -1:
        print(f"WARNING: Could not find line end for {lang_code}")
        continue

    # Insert after the line
    content = content[:line_end+1] + insert_text + "\n" + content[line_end+1:]
    print(f"Patched {lang_code}: {len(keys)} keys added")

# Also update the forgotPinHint and forgotPinOtpSent in English to mention email
# (replace the SMS-only text with email-first text)
content = content.replace(
    "forgotPinHint: 'Enter your registered phone number. We will send an OTP via SMS to reset your PIN.'",
    "forgotPinHint: 'Enter your registered phone number. We will send a verification code to your registered email to reset your PIN.'",
    1  # only first occurrence (English)
)
content = content.replace(
    "forgotPinOtpSent: 'We sent an OTP to {phone}. Enter it below with your new PIN.'",
    "forgotPinOtpSent: 'We sent a verification code to your email. Enter it below with your new PIN.'",
    1  # only first occurrence (English)
)

with open(TRANS_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! All translations patched.")
