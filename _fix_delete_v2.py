"""Rewrite delete section in ProfilePage.jsx and App.css for proper alignment and clean look."""
import re

# ═══════════════════════════════════════════
# 1. Fix ProfilePage.jsx — better JSX structure
# ═══════════════════════════════════════════
jsx_path = r'frontend\src\pages\ProfilePage.jsx'
with open(jsx_path, 'r', encoding='utf-8') as f:
    jsx = f.read()

# Replace from "{/* Delete Account */}" to just before "</div>{/* end profile-page-scroll"
old_pattern = re.compile(
    r'\s*\{/\* Delete Account \*/\}.*?(?=\s*</div>\{/\* end profile-page-scroll)',
    re.DOTALL
)

new_jsx = """
            {/* Delete Account — minimal link at bottom */}
            <div className="delete-account-row">
                <button onClick={() => setShowDeleteConfirm(true)} className="delete-account-link">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                    {t('deleteAccountBtn')}
                </button>
            </div>

            {showDeleteConfirm && (
                <div className="delete-popup-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)}>
                    <div className="delete-popup" onClick={(e) => e.stopPropagation()}>
                        <div className="delete-popup-header">
                            <div className="delete-popup-icon">
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                    <line x1="10" y1="11" x2="10" y2="17"/>
                                    <line x1="14" y1="11" x2="14" y2="17"/>
                                </svg>
                            </div>
                            <h3 className="delete-popup-title">{t('deleteAccountConfirmTitle')}</h3>
                            <p className="delete-popup-msg">{t('deleteAccountConfirmMsg')}</p>
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
"""

m = old_pattern.search(jsx)
if m:
    jsx = jsx[:m.start()] + new_jsx + jsx[m.end():]
    print("JSX: Replaced delete section")
else:
    print("JSX ERROR: Could not find delete section")

with open(jsx_path, 'w', encoding='utf-8') as f:
    f.write(jsx)

# ═══════════════════════════════════════════
# 2. Fix App.css — replace old CSS block with clean new one
# ═══════════════════════════════════════════
css_path = r'frontend\src\App.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Remove old delete CSS (everything from the comment block to end)
old_css = re.compile(
    r'/\* [═]+ *\n\s*Delete Account.*$',
    re.DOTALL
)

new_css = """/* ═══════════════════════════════════════════════════════════════════════
   Delete Account — Link & Centered Popup
   ═══════════════════════════════════════════════════════════════════════ */

/* Delete trigger — small red text link at bottom */
.delete-account-row {
    display: flex;
    justify-content: center;
    margin: 28px 0 16px;
    padding-top: 20px;
    border-top: 1px solid var(--border-light, #eee);
}
.delete-account-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: none;
    border: none;
    color: #b91c1c;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.15s ease;
    opacity: 0.75;
}
.delete-account-link:hover {
    opacity: 1;
    background: rgba(220, 38, 38, 0.06);
}
.delete-account-link svg {
    opacity: 0.7;
}

/* Popup overlay */
.delete-popup-overlay {
    position: fixed;
    inset: 0;
    z-index: 10000;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    animation: fadeIn 0.15s ease;
}

/* Popup card */
.delete-popup {
    background: white;
    border-radius: 16px;
    width: 340px;
    max-width: calc(100vw - 48px);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
    overflow: hidden;
    animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Popup header — centered with icon */
.delete-popup-header {
    text-align: center;
    padding: 28px 24px 20px;
}
.delete-popup-icon {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: #fef2f2;
    border: 2px solid #fecaca;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
}
.delete-popup-title {
    font-size: 17px;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 8px;
}
.delete-popup-msg {
    font-size: 13px;
    color: #6b7280;
    line-height: 1.5;
    margin: 0;
}

/* Popup action buttons */
.delete-popup-actions {
    display: flex;
    gap: 10px;
    padding: 4px 24px 24px;
}
.delete-popup-no,
.delete-popup-yes {
    flex: 1;
    padding: 11px 16px;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    text-align: center;
}
.delete-popup-no {
    background: #f3f4f6;
    color: #374151;
}
.delete-popup-no:hover {
    background: #e5e7eb;
}
.delete-popup-yes {
    background: #dc2626;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 42px;
}
.delete-popup-yes:hover:not(:disabled) {
    background: #b91c1c;
}
.delete-popup-yes:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* Spinner */
.delete-spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
}

/* Mobile */
@media (max-width: 480px) {
    .delete-popup {
        width: calc(100vw - 32px);
    }
    .delete-popup-header {
        padding: 24px 20px 16px;
    }
    .delete-popup-actions {
        padding: 4px 20px 20px;
    }
}
"""

m = old_css.search(css)
if m:
    css = css[:m.start()] + new_css
    print("CSS: Replaced delete styles")
else:
    print("CSS ERROR: Could not find old delete CSS")

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)

# ═══════════════════════════════════════════
# 3. Verify
# ═══════════════════════════════════════════
with open(jsx_path, 'r', encoding='utf-8') as f:
    j = f.read()
with open(css_path, 'r', encoding='utf-8') as f:
    c = f.read()

print(f"\nJSX: {j.count(chr(10))} lines")
print(f"  delete-account-link: {'delete-account-link' in j}")
print(f"  delete-popup-header: {'delete-popup-header' in j}")
print(f"  old delete-strip: {'delete-strip' in j}")

print(f"\nCSS: {c.count(chr(10))} lines")
print(f"  delete-account-row: {'delete-account-row' in c}")
print(f"  delete-popup-header: {'delete-popup-header' in c}")
print(f"  old delete-strip: {'delete-strip' in c}")
