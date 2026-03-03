"""
v3 — Rewrite the delete-account section in ProfilePage to match the
chat-history delete style (compact strip + info + Yes/No popup).
Also rewrites only the profile-delete CSS block in App.css.
"""
import re, pathlib, textwrap

ROOT = pathlib.Path(__file__).resolve().parent / "frontend" / "src"
JSX  = ROOT / "pages" / "ProfilePage.jsx"
CSS  = ROOT / "App.css"

# ──────────────────────────────────────────────────────────────────────
#  1.  ProfilePage.jsx — replace the delete section
# ──────────────────────────────────────────────────────────────────────
jsx_src = JSX.read_text(encoding="utf-8")

# Locate the old delete block: from the comment `{/* Delete Account` to the
# closing of the popup `)}` just before `</div>{/* end profile-page-scroll */}`
old_delete_re = re.compile(
    r'\{/\*\s*Delete Account.*?\n.*?'   # comment line
    r'(.*?\n)*?'                         # everything in between
    r'\s*\{showDeleteConfirm.*?\n'       # popup start
    r'(.*?\n)*?'                         # popup body
    r'\s*\)\}',                          # closing `)}` of the popup conditional
    re.DOTALL
)

# Build the new JSX snippet
new_delete_jsx = textwrap.dedent("""\
            {/* ── Delete Account ── */}
            <div className="delete-section">
                <div className="delete-section-info">
                    <div className="delete-section-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="12"/>
                            <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                    </div>
                    <div className="delete-section-text">
                        <span className="delete-section-title">{t('deleteAccountTitle')}</span>
                        <span className="delete-section-desc">{t('deleteAccountWarning')}</span>
                    </div>
                </div>
                <button
                    className="delete-section-btn"
                    onClick={() => setShowDeleteConfirm(true)}
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                    {t('deleteAccountBtn')}
                </button>
            </div>

            {/* Delete confirmation popup */}
            {showDeleteConfirm && (
                <div className="delete-popup-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)}>
                    <div className="delete-popup" onClick={(e) => e.stopPropagation()}>
                        <div className="delete-popup-body">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                                <line x1="12" y1="9" x2="12" y2="13"/>
                                <line x1="12" y1="17" x2="12.01" y2="17"/>
                            </svg>
                            <div>
                                <p style={{fontWeight: 600, marginBottom: '6px', color: '#991b1b'}}>{t('deleteAccountConfirmTitle')}</p>
                                <p>{t('deleteAccountConfirmMsg')}</p>
                            </div>
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
            )}\
""")

# Do the replacement
match = old_delete_re.search(jsx_src)
if match:
    jsx_src = jsx_src[:match.start()] + new_delete_jsx + jsx_src[match.end():]
    JSX.write_text(jsx_src, encoding="utf-8")
    print(f"✅ ProfilePage.jsx updated ({len(jsx_src.splitlines())} lines)")
else:
    print("⚠️  Could not locate old delete block in JSX — trying alternate approach")
    # Alternate: find from the tip-box line onward
    tip_idx = jsx_src.find("{/* Delete Account")
    if tip_idx == -1:
        tip_idx = jsx_src.find("delete-account-row")
    if tip_idx != -1:
        # Find the end marker
        end_marker = "</div>{/* end profile-page-scroll */}"
        end_idx = jsx_src.find(end_marker)
        if end_idx != -1:
            jsx_src = jsx_src[:tip_idx] + new_delete_jsx + "\n\n\n            " + jsx_src[end_idx:]
            JSX.write_text(jsx_src, encoding="utf-8")
            print(f"✅ ProfilePage.jsx updated (alternate) ({len(jsx_src.splitlines())} lines)")
        else:
            print("❌ Could not find end marker in JSX")
    else:
        print("❌ Could not find any delete section in JSX")

# ──────────────────────────────────────────────────────────────────────
#  2.  App.css — replace ALL profile-delete CSS (keep chat-history-delete)
# ──────────────────────────────────────────────────────────────────────
css_src = CSS.read_text(encoding="utf-8")

# Remove old blocks: everything from "/* Delete Account" or ".delete-strip"
# to the @media block for delete, then append our new CSS.

# Strategy: find the comment before delete-strip or delete-account-row and
# remove everything from there to end of file, then re-append the new CSS
# plus anything after if needed.

# Find start of old delete CSS
patterns_to_find = [
    "/* Delete Account",
    "/* ═══════════════════════════════════════════════════════════════════════\n   Delete Account",
    ".delete-strip {",
    ".delete-strip{",
    ".delete-account-row {",
    ".delete-account-row{",
]

start_pos = len(css_src)
for p in patterns_to_find:
    idx = css_src.find(p)
    if idx != -1 and idx < start_pos:
        start_pos = idx

# Also look for the comment block before
comment_start = css_src.rfind("/* ═══", 0, start_pos + 5)
if comment_start != -1 and comment_start > start_pos - 200:
    start_pos = comment_start

# Check there's no non-delete CSS after the delete block
# (there shouldn't be since delete was appended at the end)
remaining_after = css_src[start_pos:]
# We'll replace everything from start_pos to end of file

new_delete_css = textwrap.dedent("""\
/* ═══════════════════════════════════════════════════════════════════════
   Delete Account — Info Strip + Confirmation Popup
   ═══════════════════════════════════════════════════════════════════════ */

/* --- Delete section strip (like chat-history-delete pattern) --- */
.delete-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin: 28px 0 16px;
    padding: 14px 18px;
    background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%);
    border: 1px solid #fecaca;
    border-radius: 12px;
    transition: border-color 0.2s;
}
.delete-section:hover {
    border-color: #f87171;
}
.delete-section-info {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex: 1;
    min-width: 0;
}
.delete-section-icon {
    flex-shrink: 0;
    margin-top: 2px;
    opacity: 0.85;
}
.delete-section-text {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}
.delete-section-title {
    font-size: 13.5px;
    font-weight: 600;
    color: #991b1b;
    line-height: 1.3;
}
.delete-section-desc {
    font-size: 12px;
    color: #b91c1c;
    line-height: 1.45;
    opacity: 0.8;
}
.delete-section-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: transparent;
    color: #dc2626;
    border: 1.5px solid #dc2626;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.delete-section-btn:hover {
    background: #dc2626;
    color: white;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.25);
}
.delete-section-btn:active {
    transform: scale(0.96);
}
.delete-section-btn svg {
    transition: stroke 0.2s;
}
.delete-section-btn:hover svg {
    stroke: white;
}

/* --- Delete confirmation popup --- */
.delete-popup-overlay {
    position: fixed;
    inset: 0;
    z-index: 10000;
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    animation: fadeIn 0.15s ease;
}
.delete-popup {
    background: white;
    border-radius: 16px;
    max-width: 340px;
    width: 100%;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.delete-popup-body {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 22px 20px 16px;
}
.delete-popup-body svg {
    flex-shrink: 0;
    margin-top: 2px;
}
.delete-popup-body p {
    font-size: 13.5px;
    color: #374151;
    line-height: 1.55;
    margin: 0;
}
.delete-popup-actions {
    display: flex;
    gap: 10px;
    padding: 0 20px 20px;
}
.delete-popup-no {
    flex: 1;
    padding: 10px;
    background: #f3f4f6;
    color: #374151;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
}
.delete-popup-no:hover {
    background: #e5e7eb;
}
.delete-popup-yes {
    flex: 1;
    padding: 10px;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 40px;
}
.delete-popup-yes:hover:not(:disabled) {
    background: #b91c1c;
}
.delete-popup-yes:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}
.delete-spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
}

@media (max-width: 480px) {
    .delete-section {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
    }
    .delete-section-btn {
        width: 100%;
        justify-content: center;
    }
    .delete-popup {
        max-width: calc(100vw - 32px);
    }
    .delete-popup-actions {
        flex-direction: column-reverse;
    }
}
""")

css_src = css_src[:start_pos].rstrip() + "\n\n" + new_delete_css
CSS.write_text(css_src, encoding="utf-8")
print(f"✅ App.css updated ({len(css_src.splitlines())} lines)")
print("   Delete CSS replaced from position", start_pos)
print("\nDone! Now run:  npx vite build  then  python _redeploy_frontend.py")
