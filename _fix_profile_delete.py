"""Fix ProfilePage.jsx on disk: replace old type-DELETE section with compact Yes/No popup."""
import re

path = r'frontend\src\pages\ProfilePage.jsx'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original: {len(content)} chars, {content.count(chr(10))} lines")

# 1. Remove DELETE_CONFIRM_PHRASE constant
content = content.replace("const DELETE_CONFIRM_PHRASE = 'DELETE';\n", '')

# 2. Remove old deleteInput and deleteMessage state
content = content.replace("    const [deleteInput, setDeleteInput] = useState('');\n", '')
content = content.replace("    const [deleteMessage, setDeleteMessage] = useState(null);\n", '')

# 3. Remove handleDeleteAccount function
content = re.sub(
    r'    // [^\n]* Delete account handler[^\n]*\n    const handleDeleteAccount = async.*?;\n\n',
    '',
    content,
    flags=re.DOTALL
)

# 4. Replace the entire delete JSX block
# Find from "{/* Delete Account" to the closing </div> before "</div>{/* end profile-page-scroll"
old_pattern = re.compile(
    r'(\s*\{/\* Delete Account[^\n]*\*/\}.*?)\n\s*</div>\{/\* end profile-page-scroll',
    re.DOTALL
)

new_jsx = """
            {/* Delete Account */}
            <div className="delete-strip">
                <span className="delete-strip-text">{t('deleteAccountWarning')}</span>
                <button onClick={() => setShowDeleteConfirm(true)} className="delete-strip-btn">
                    {t('deleteAccountBtn')}
                </button>
            </div>

            {showDeleteConfirm && (
                <div className="delete-popup-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)}>
                    <div className="delete-popup" onClick={(e) => e.stopPropagation()}>
                        <div className="delete-popup-body">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="12" y1="8" x2="12" y2="12"/>
                                <line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                            <p>{t('deleteAccountConfirmMsg')}</p>
                        </div>
                        <div className="delete-popup-actions">
                            <button onClick={() => setShowDeleteConfirm(false)} disabled={deleting} className="delete-popup-no">
                                {t('deleteAccountCancel')}
                            </button>
                            <button
                                onClick={async () => { setDeleting(true); await deleteAccount(); }}
                                disabled={deleting}
                                className="delete-popup-yes"
                            >
                                {deleting ? <span className="delete-spinner" /> : t('deleteAccountConfirmBtn')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            </div>{/* end profile-page-scroll"""

m = old_pattern.search(content)
if m:
    content = content[:m.start()] + new_jsx + content[m.end():]
    print("Replaced delete JSX section")
else:
    print("ERROR: Could not find old delete section!")
    # Debug: show what patterns exist
    if '{/* Delete Account' in content:
        print("Found '{/* Delete Account' in content")
    if '</div>{/* end profile-page-scroll' in content:
        print("Found '</div>{/* end profile-page-scroll' in content")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
print(f"Result: {len(c)} chars, {c.count(chr(10))} lines")
print(f"  delete-strip: {'delete-strip' in c}")
print(f"  deleteProfile: {'deleteProfile' in c}")
print(f"  DELETE_CONFIRM: {'DELETE_CONFIRM' in c}")
print(f"  handleDeleteAccount: {'handleDeleteAccount' in c}")
print(f"  delete-popup: {'delete-popup' in c}")
