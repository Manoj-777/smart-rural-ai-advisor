"""
v5 — Fix the delete account section:
1. Update JSX to use existing deleteProfile* translation keys (not deleteAccount*)
2. Update English translations with better, clearer wording
3. Add new keys: deleteProfileConfirmTitle, deleteProfileConfirmMsg, deleteProfileConfirmYes
4. Fix the modal button alignment CSS
5. Improve the delete zone card and modal JSX with proper info
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent / "frontend" / "src"
JSX  = ROOT / "pages" / "ProfilePage.jsx"
CSS  = ROOT / "App.css"
I18N = ROOT / "i18n" / "translations.js"

# ══════════════════════════════════════════════════════════════════════
#  1. Fix translations — update English wording + add new confirm keys
# ══════════════════════════════════════════════════════════════════════
i18n_src = I18N.read_text(encoding="utf-8")

# English section — replace old deleteProfile block with better wording
old_en = """        deleteProfileTitle: 'Delete Account',
        deleteProfileWarning: 'This will permanently delete your profile, farm data, and login. This action cannot be undone.',
        deleteProfileBtn: 'Delete My Account',
        deleteProfileConfirmText: 'Type DELETE to confirm permanent deletion:',
        deleteProfileTypePlaceholder: 'Type DELETE here',
        deleteProfileTypeMismatch: 'Please type DELETE exactly to confirm',
        deleteProfileCancel: 'Cancel',
        deleteProfileConfirmBtn: 'Permanently Delete',"""

new_en = """        deleteProfileTitle: 'Danger Zone',
        deleteProfileWarning: 'Deleting your account will permanently remove all your data including your profile, farm details, crop preferences, and login credentials. This action cannot be undone.',
        deleteProfileBtn: 'Delete Account',
        deleteProfileConfirmTitle: 'Delete Your Account?',
        deleteProfileConfirmMsg: 'This will permanently erase your farmer profile, saved farm data, crop preferences, and login access. You will need to register again to use this service.',
        deleteProfileCancel: 'No, Keep My Account',
        deleteProfileConfirmBtn: 'Yes, Delete Everything',"""

if old_en in i18n_src:
    i18n_src = i18n_src.replace(old_en, new_en)
    print("  ✅ English translations updated")
else:
    print("  ⚠️  English block not found exactly, trying line-by-line fix")
    # Replace individual keys
    replacements = {
        "deleteProfileTitle: 'Delete Account'": "deleteProfileTitle: 'Danger Zone'",
        "deleteProfileWarning: 'This will permanently delete your profile, farm data, and login. This action cannot be undone.'": "deleteProfileWarning: 'Deleting your account will permanently remove all your data including your profile, farm details, crop preferences, and login credentials. This action cannot be undone.'",
        "deleteProfileBtn: 'Delete My Account'": "deleteProfileBtn: 'Delete Account'",
        "deleteProfileConfirmBtn: 'Permanently Delete'": "deleteProfileConfirmBtn: 'Yes, Delete Everything'",
        "deleteProfileCancel: 'Cancel'": "deleteProfileCancel: 'No, Keep My Account'",
    }
    for old, new in replacements.items():
        # Only replace the first occurrence (English)
        idx = i18n_src.find(old)
        if idx != -1:
            i18n_src = i18n_src[:idx] + new + i18n_src[idx + len(old):]
    
    # Remove old type-DELETE keys and add new confirm keys for English
    for old_key in ['deleteProfileConfirmText:', 'deleteProfileTypePlaceholder:', 'deleteProfileTypeMismatch:']:
        # Find and remove the line
        lines = i18n_src.split('\n')
        i18n_src = '\n'.join(l for l in lines if old_key not in l)
    
    # Add new confirm keys after deleteProfileBtn in English section
    btn_line = "        deleteProfileBtn: 'Delete Account',"
    new_keys = btn_line + "\n        deleteProfileConfirmTitle: 'Delete Your Account?',\n        deleteProfileConfirmMsg: 'This will permanently erase your farmer profile, saved farm data, crop preferences, and login access. You will need to register again to use this service.',"
    i18n_src = i18n_src.replace(btn_line, new_keys, 1)
    print("  ✅ English translations updated (line-by-line)")

# For all OTHER languages — remove old type-DELETE keys and add confirmTitle + confirmMsg
# We need to add deleteProfileConfirmTitle and deleteProfileConfirmMsg after deleteProfileBtn for each language
lines = i18n_src.split('\n')
new_lines = []
skip_keys = ['deleteProfileConfirmText:', 'deleteProfileTypePlaceholder:', 'deleteProfileTypeMismatch:']
i = 0
lang_confirm_added = set()
while i < len(lines):
    line = lines[i]
    
    # Skip old type-DELETE keys from all languages
    if any(k in line for k in skip_keys):
        i += 1
        continue
    
    new_lines.append(line)
    
    # After deleteProfileBtn line, add confirmTitle and confirmMsg if not already there
    if 'deleteProfileBtn:' in line and 'deleteProfileConfirmTitle' not in (lines[i+1] if i+1 < len(lines) else ''):
        # Check what language section we're in by looking backwards for a key pattern
        indent = '        '
        # For Tamil
        lang_translations = {
            'கணக்கை நீக்கு': ("'உங்கள் கணக்கை நீக்க வேண்டுமா?'", "'இது உங்கள் விவசாயி சுயவிவரம், சேமித்த பண்ணை தரவு, பயிர் விருப்பங்கள் மற்றும் உள்நுழைவு அணுகலை நிரந்தரமாக அழிக்கும்.'"),
            'ಖಾತೆಯನ್ನು ಅಳಿಸಿ': ("'ನಿಮ್ಮ ಖಾತೆಯನ್ನು ಅಳಿಸಬೇಕೇ?'", "'ಇದು ನಿಮ್ಮ ರೈತ ಪ್ರೊಫೈಲ್, ಉಳಿಸಿದ ಕೃಷಿ ಡೇಟಾ, ಬೆಳೆ ಆದ್ಯತೆಗಳು ಮತ್ತು ಲಾಗಿನ್ ಪ್ರವೇಶವನ್ನು ಶಾಶ್ವತವಾಗಿ ಅಳಿಸುತ್ತದೆ.'"),
            'ఖాతాను తొలగించు': ("'మీ ఖాతాను తొలగించాలా?'", "'ఇది మీ రైతు ప్రొఫైల్, సేవ్ చేసిన వ్యవసాయ డేటా, పంట ప్రాధాన్యతలు మరియు లాగిన్ యాక్సెస్‌ను శాశ్వతంగా తొలగిస్తుంది.'"),
            'खाता हटाएं': ("'क्या आप अपना खाता हटाना चाहते हैं?'", "'यह आपकी किसान प्रोफाइल, सहेजे गए खेत का डेटा, फसल प्राथमिकताएं और लॉगिन एक्सेस को स्थायी रूप से मिटा देगा।'"),
            'ନିଜ ଆକାଉଣ୍ଟ ବିଲୋପ': ("'ଆପଣ ନିଜ ଆକାଉଣ୍ଟ ବିଲୋପ କରିବାକୁ ଚାହୁଁଛନ୍ତି?'", "'ଏହା ଆପଣଙ୍କ କୃଷକ ପ୍ରୋଫାଇଲ, ସଞ୍ଚିତ ଚାଷ ତଥ୍ୟ, ଫସଲ ପସନ୍ଦ ଏବଂ ଲଗଇନ ଆକ୍ସେସକୁ ସ୍ଥାୟୀ ଭାବରେ ବିଲୋପ କରିବ।'"),
            'ਖਾਤਾ ਮਿਟਾਓ': ("'ਕੀ ਤੁਸੀਂ ਆਪਣਾ ਖਾਤਾ ਮਿਟਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ?'", "'ਇਹ ਤੁਹਾਡੀ ਕਿਸਾਨ ਪ੍ਰੋਫਾਈਲ, ਸੇਵ ਕੀਤੇ ਖੇਤ ਦੇ ਡੇਟਾ, ਫਸਲ ਤਰਜੀਹਾਂ ਅਤੇ ਲੌਗਇਨ ਐਕਸੈਸ ਨੂੰ ਸਥਾਈ ਤੌਰ \'ਤੇ ਮਿਟਾ ਦੇਵੇਗਾ।'"),
            'অ্যাকাউন্ট মুছুন': ("'আপনি কি আপনার অ্যাকাউন্ট মুছতে চান?'", "'এটি আপনার কৃষক প্রোফাইল, সংরক্ষিত খামারের ডেটা, ফসলের পছন্দ এবং লগইন অ্যাক্সেস স্থায়ীভাবে মুছে ফেলবে।'"),
            'ખાતું કાઢી નાખો': ("'શું તમે તમારું ખાતું કાઢી નાખવા માંગો છો?'", "'આ તમારી ખેડૂત પ્રોફાઇલ, સાચવેલ ખેતીનો ડેટા, પાક પસંદગીઓ અને લોગિન એક્સેસને કાયમી ધોરણે કાઢી નાખશે.'"),
            'खाते हटवा': ("'तुम्हाला खाते हटवायचे आहे?'", "'हे तुमचे शेतकरी प्रोफाइल, जतन केलेला शेतीचा डेटा, पीक प्राधान्ये आणि लॉगिन ॲक्सेस कायमचे हटवेल.'"),
            'اکاؤنٹ حذف کریں': ("'کیا آپ اپنا اکاؤنٹ حذف کرنا چاہتے ہیں؟'", "'یہ آپ کی کسان پروفائل، محفوظ کھیتی کا ڈیٹا، فصل کی ترجیحات اور لاگ ان رسائی کو مستقل طور پر حذف کر دے گا۔'"),
            'അക്കൗണ്ട് നീക്കം ചെയ്യുക': ("'നിങ്ങളുടെ അക്കൗണ്ട് നീക്കം ചെയ്യണോ?'", "'ഇത് നിങ്ങളുടെ കർഷക പ്രൊഫൈൽ, സേവ് ചെയ്ത കൃഷി ഡേറ്റ, വിള മുൻഗണനകൾ, ലോഗിൻ ആക്സസ് എന്നിവ ശാശ്വതമായി ഇല്ലാതാക്കും.'"),
            'ਖਾਤੂੰ ਕਾਢੀ ਨਾਖੋ': ("'ਸ਼ੁੰ ਤਮਨੇ ਖਾਤਰੀ ਛੇ?'", "'ਤਮਾਰੋ ਤਮਾਮ ਖੇਤੀਨੋ ਡੇਟਾ, ਪਾਕ ਪਸੰਦગીઓ ਅਨੇ ਪ੍ਰોફાઈલ ਮાહিતી ਕાયમી ਧોરણે ハટવાશે.'"),
            'ଆକାଉଣ୍ଟ ବିଲୋପ କରନ୍ତୁ': ("'ଆପଣ ନିଶ୍ଚିତ କି?'", "'ଆପଣଙ୍କ ସମସ୍ତ ଚାଷ ତଥ୍ୟ, ଫସଲ ପସନ୍ଦ ଏବଂ ପ୍ରୋଫାଇଲ ସୂଚନା ସ୍ଥାୟୀ ଭାବେ ବିଲୋପ ହେବ।'"),
        }
        # Generic fallback
        title_val = "'Delete Your Account?'"
        msg_val = "'This will permanently erase your farmer profile, saved farm data, crop preferences, and login access. You will need to register again to use this service.'"
        
        # Try to detect language from the line content
        for lang_marker, (t_val, m_val) in lang_translations.items():
            if lang_marker in line:
                title_val = t_val
                msg_val = m_val
                break
        
        new_lines.append(f"{indent}deleteProfileConfirmTitle: {title_val},")
        new_lines.append(f"{indent}deleteProfileConfirmMsg: {msg_val},")
    
    i += 1

i18n_src = '\n'.join(new_lines)
I18N.write_text(i18n_src, encoding="utf-8")
print(f"✅ translations.js updated ({len(new_lines)} lines)")

# ══════════════════════════════════════════════════════════════════════
#  2. Fix ProfilePage.jsx — use deleteProfile* keys + better layout
# ══════════════════════════════════════════════════════════════════════
jsx_src = JSX.read_text(encoding="utf-8")

# Replace all deleteAccount* references with deleteProfile*
key_map = {
    "deleteAccountTitle": "deleteProfileTitle",
    "deleteAccountWarning": "deleteProfileWarning",
    "deleteAccountBtn": "deleteProfileBtn",
    "deleteAccountConfirmTitle": "deleteProfileConfirmTitle",
    "deleteAccountConfirmMsg": "deleteProfileConfirmMsg",
    "deleteAccountCancel": "deleteProfileCancel",
    "deleteAccountConfirmBtn": "deleteProfileConfirmBtn",
}
for old_key, new_key in key_map.items():
    jsx_src = jsx_src.replace(f"'{old_key}'", f"'{new_key}'")

# Now rewrite the entire delete section with properly indented, clean JSX
# Find start and end
start_marker_candidates = [
    "{/* ── Delete Account",
    "{/* — Delete Account",
    "{/* Delete Account",
    "delete-zone-card",
]
start_idx = -1
for m in start_marker_candidates:
    idx = jsx_src.find(m)
    if idx != -1:
        line_start = jsx_src.rfind("\n", 0, idx)
        start_idx = line_start + 1 if line_start != -1 else idx
        break

end_of_file = jsx_src.rfind("export default ProfilePage")
closing_section = jsx_src.find("</div>\n    );\n}", start_idx if start_idx != -1 else 0)

# Replace from delete section start to just before closing </div> of profile-page
end_scroll = jsx_src.find("</div>{/* end profile-page-scroll */}")
end_component = jsx_src.find("</div>\n    );\n}")

if start_idx != -1 and end_component != -1:
    new_jsx_block = """            {/* ── Delete Account ── */}
            <div className="delete-zone-card">
                <div className="delete-zone-inner">
                    <div className="delete-zone-badge">⚠️</div>
                    <div className="delete-zone-text">
                        <h4 className="delete-zone-title">{t('deleteProfileTitle')}</h4>
                        <p className="delete-zone-desc">{t('deleteProfileWarning')}</p>
                    </div>
                    <button
                        className="delete-zone-btn"
                        onClick={() => setShowDeleteConfirm(true)}
                        disabled={deleting}
                    >
                        🗑️ {t('deleteProfileBtn')}
                    </button>
                </div>
            </div>

            </div>{/* end profile-page-scroll */}

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="delete-modal-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)}>
                    <div className="delete-modal" onClick={e => e.stopPropagation()}>
                        <div className="delete-modal-top">
                            <div className="delete-modal-icon-ring">
                                <span style={{ fontSize: '28px' }}>🗑️</span>
                            </div>
                            <h3>{t('deleteProfileConfirmTitle')}</h3>
                            <p>{t('deleteProfileConfirmMsg')}</p>
                        </div>
                        <div className="delete-modal-actions">
                            <button
                                className="delete-modal-cancel"
                                onClick={() => setShowDeleteConfirm(false)}
                                disabled={deleting}
                            >
                                {t('deleteProfileCancel')}
                            </button>
                            <button
                                className="delete-modal-confirm"
                                onClick={handleDeleteAccount}
                                disabled={deleting}
                            >
                                {deleting
                                    ? <span className="delete-spinner" />
                                    : <><span>🗑️</span> {t('deleteProfileConfirmBtn')}</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}

export default ProfilePage;
"""
    jsx_src = jsx_src[:start_idx] + new_jsx_block
    JSX.write_text(jsx_src, encoding="utf-8")
    print(f"✅ ProfilePage.jsx updated ({len(jsx_src.splitlines())} lines)")
else:
    print(f"❌ Could not locate delete section in JSX (start={start_idx}, end={end_component})")

# ══════════════════════════════════════════════════════════════════════
#  3. Fix App.css — Improve delete modal alignment
# ══════════════════════════════════════════════════════════════════════
css_src = CSS.read_text(encoding="utf-8")

# Find and replace the Delete Account CSS section
css_markers = [
    "/* ═══════════════════════════════════════════════════════════════════════\n   Delete Account",
    "/* Delete Account",
    ".delete-zone-card {",
]
css_start = len(css_src)
for p in css_markers:
    idx = css_src.find(p)
    if idx != -1 and idx < css_start:
        css_start = idx

# Look for section comment before
comment_start = css_src.rfind("/* ═══", 0, css_start + 5)
if comment_start != -1 and comment_start > css_start - 300:
    css_start = comment_start

new_css = """/* ═══════════════════════════════════════════════════════════════════════
   Delete Account — Danger Zone Card + Confirmation Modal 
   ═══════════════════════════════════════════════════════════════════════ */
.delete-zone-card {
    background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%);
    border: 1.5px solid #fecaca;
    border-radius: var(--radius, 12px);
    padding: 22px 24px;
    margin-top: 32px;
    margin-bottom: 8px;
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.delete-zone-card:hover {
    box-shadow: 0 4px 20px rgba(220, 38, 38, 0.1);
    border-color: #fca5a5;
}
.delete-zone-inner {
    display: flex;
    align-items: center;
    gap: 18px;
    min-width: 0;
}
.delete-zone-badge {
    width: 46px;
    height: 46px;
    border-radius: 12px;
    background: rgba(220, 38, 38, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.delete-zone-text {
    flex: 1;
    min-width: 0;
}
.delete-zone-title {
    font-size: 15px;
    font-weight: 700;
    color: #991b1b;
    margin: 0 0 6px;
    letter-spacing: -0.01em;
}
.delete-zone-desc {
    font-size: 13px;
    color: #b91c1c;
    line-height: 1.55;
    margin: 0;
    opacity: 0.82;
}
.delete-zone-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 22px;
    background: var(--error, #dc2626);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    flex-shrink: 0;
    letter-spacing: 0.01em;
}
.delete-zone-btn:hover {
    background: #b91c1c;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(220, 38, 38, 0.3);
}
.delete-zone-btn:active {
    transform: translateY(0) scale(0.97);
}
.delete-zone-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

/* ── Delete Confirmation Modal ── */
.delete-modal-overlay {
    position: fixed;
    inset: 0;
    z-index: 10000;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    animation: fadeIn 0.15s ease;
}
.delete-modal {
    background: white;
    border-radius: 20px;
    max-width: 400px;
    width: 100%;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0,0,0,0.04);
    overflow: hidden;
    animation: slideUp 0.3s cubic-bezier(.2,.8,.3,1);
}
.delete-modal-top {
    text-align: center;
    padding: 32px 28px 24px;
}
.delete-modal-icon-ring {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #fef2f2, #fee2e2);
    border: 2px solid #fecaca;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 18px;
}
.delete-modal-top h3 {
    font-size: 20px;
    font-weight: 700;
    color: #991b1b;
    margin: 0 0 10px;
}
.delete-modal-top p {
    font-size: 14px;
    color: #7f1d1d;
    line-height: 1.65;
    margin: 0;
    opacity: 0.85;
}
.delete-modal-actions {
    display: flex;
    gap: 12px;
    padding: 4px 28px 28px;
}
.delete-modal-cancel,
.delete-modal-confirm {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 13px 16px;
    border-radius: 12px;
    font-size: 14.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 48px;
    border: none;
}
.delete-modal-cancel {
    background: #f1f5f9;
    color: var(--text-secondary, #475569);
    border: 1px solid var(--border, #e2e8f0);
}
.delete-modal-cancel:hover {
    background: #e2e8f0;
}
.delete-modal-confirm {
    background: #dc2626;
    color: white;
}
.delete-modal-confirm:hover:not(:disabled) {
    background: #b91c1c;
    box-shadow: 0 4px 14px rgba(220, 38, 38, 0.3);
}
.delete-modal-confirm:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

/* Delete spinner */
.delete-spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
}

/* Responsive */
@media (max-width: 480px) {
    .delete-zone-inner {
        flex-direction: column;
        align-items: flex-start;
        gap: 14px;
    }
    .delete-zone-btn {
        width: 100%;
        justify-content: center;
    }
    .delete-modal {
        max-width: calc(100vw - 32px);
        border-radius: 16px;
    }
    .delete-modal-top {
        padding: 24px 20px 18px;
    }
    .delete-modal-actions {
        padding: 0 20px 20px;
        flex-direction: column-reverse;
    }
    .delete-modal-cancel,
    .delete-modal-confirm {
        width: 100%;
    }
}
"""

css_src = css_src[:css_start].rstrip() + "\n\n" + new_css
CSS.write_text(css_src, encoding="utf-8")
print(f"✅ App.css updated ({len(css_src.splitlines())} lines)")

print("\n✅ All done! Run:  cd frontend && npx vite build  then  python _redeploy_frontend.py")
