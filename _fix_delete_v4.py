"""
v4 — Apply the stashed delete-zone-card + delete-modal design from git stash.
Overwrites the current delete section in ProfilePage.jsx and CSS in App.css.
"""
import re, pathlib, textwrap

ROOT = pathlib.Path(__file__).resolve().parent / "frontend" / "src"
JSX  = ROOT / "pages" / "ProfilePage.jsx"
CSS  = ROOT / "App.css"

# ──────────────────────────────────────────────────────────────────────
#  1.  ProfilePage.jsx — Add handleDeleteAccount + replace delete JSX
# ──────────────────────────────────────────────────────────────────────
jsx_src = JSX.read_text(encoding="utf-8")
lines = jsx_src.split("\n")

# --- 1a. Add handleDeleteAccount function if not present ---
if "handleDeleteAccount" not in jsx_src:
    # Find the line with "return (" and insert before it
    insert_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("return ("):
            insert_idx = i
            break
    if insert_idx:
        handler_code = [
            "",
            "    const handleDeleteAccount = async () => {",
            "        setDeleting(true);",
            "        try {",
            "            await deleteAccount();",
            "        } catch (err) {",
            "            setMessage({ type: 'error', text: 'Failed to delete account. Please try again.' });",
            "            setDeleting(false);",
            "            setShowDeleteConfirm(false);",
            "        }",
            "    };",
            "",
        ]
        lines = lines[:insert_idx] + handler_code + lines[insert_idx:]
        print("  ✅ Added handleDeleteAccount function")

# --- 1b. Replace the delete section JSX ---
jsx_src = "\n".join(lines)

# Find the old delete section — from the comment to the closing )}
# Pattern: from "{/* Delete Account" or "{/* ── Delete Account" to the popup closing `)}`
# that comes before `</div>{/* end profile-page-scroll */}`

# Find start
delete_start_markers = [
    "{/* ── Delete Account ──",
    "{/* — Delete Account",
    "{/* Delete Account",
    "delete-section",
    "delete-account-row",
]
start_idx = -1
for marker in delete_start_markers:
    idx = jsx_src.find(marker)
    if idx != -1:
        # Go back to beginning of line
        line_start = jsx_src.rfind("\n", 0, idx)
        start_idx = line_start + 1 if line_start != -1 else idx
        break

# Find end — look for `</div>{/* end profile-page-scroll */}`
end_marker = "</div>{/* end profile-page-scroll */}"
end_idx = jsx_src.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_delete_jsx = textwrap.dedent("""\
            {/* ── Delete Account ── */}
            <div className="delete-zone-card">
                <div className="delete-zone-inner">
                    <div className="delete-zone-badge">⚠️</div>
                    <div className="delete-zone-text">
                        <h4 className="delete-zone-title">{t('deleteAccountTitle')}</h4>
                        <p className="delete-zone-desc">{t('deleteAccountWarning')}</p>
                    </div>
                    <button
                        className="delete-zone-btn"
                        onClick={() => setShowDeleteConfirm(true)}
                        disabled={deleting}
                    >
                        {t('deleteAccountBtn')}
                    </button>
                </div>
            </div>

            """) + end_marker + """

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="delete-modal-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)}>
                    <div className="delete-modal" onClick={e => e.stopPropagation()}>
                        <div className="delete-modal-top">
                            <div className="delete-modal-icon-ring">
                                <span style={{ fontSize: '24px' }}>⚠️</span>
                            </div>
                            <h3>{t('deleteAccountConfirmTitle')}</h3>
                            <p>{t('deleteAccountConfirmMsg')}</p>
                        </div>
                        <div className="delete-modal-actions">
                            <button
                                className="delete-modal-cancel"
                                onClick={() => setShowDeleteConfirm(false)}
                                disabled={deleting}
                            >
                                {t('deleteAccountCancel')}
                            </button>
                            <button
                                className="delete-modal-confirm"
                                onClick={handleDeleteAccount}
                                disabled={deleting}
                            >
                                {deleting
                                    ? <span className="delete-spinner" />
                                    : t('deleteAccountConfirmBtn')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
"""

    jsx_src = jsx_src[:start_idx] + new_delete_jsx + jsx_src[end_idx + len(end_marker):]
    JSX.write_text(jsx_src, encoding="utf-8")
    print(f"✅ ProfilePage.jsx updated ({len(jsx_src.splitlines())} lines)")
else:
    print(f"❌ Could not find delete section (start={start_idx}, end={end_idx})")

# ──────────────────────────────────────────────────────────────────────
#  2.  App.css — Replace all profile-delete CSS with stashed design
# ──────────────────────────────────────────────────────────────────────
css_src = CSS.read_text(encoding="utf-8")

# Find start of old delete CSS
patterns_to_find = [
    "/* Delete Account",
    "/* ═══════════════════════════════════════════════════════════════════════\n   Delete Account",
    ".delete-strip {",
    ".delete-section {",
    ".delete-account-row {",
]

start_pos = len(css_src)
for p in patterns_to_find:
    idx = css_src.find(p)
    if idx != -1 and idx < start_pos:
        start_pos = idx

# Also look for the section comment
comment_start = css_src.rfind("/* ═══", 0, start_pos + 5)
if comment_start != -1 and comment_start > start_pos - 300:
    start_pos = comment_start

new_delete_css = textwrap.dedent("""\
/* ═══════════════════════════════════════════════════════════════════════
   Delete Account Zone — Card + Modal (from stash)
   ═══════════════════════════════════════════════════════════════════════ */
.delete-zone-card {
    background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%);
    border: 1px solid #fecaca;
    border-radius: var(--radius, 12px);
    padding: 20px 24px;
    margin-top: 32px;
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.delete-zone-card:hover {
    box-shadow: 0 4px 16px rgba(220, 38, 38, 0.08);
    border-color: #fca5a5;
}
.delete-zone-inner {
    display: flex;
    align-items: center;
    gap: 16px;
    min-width: 0;
}
.delete-zone-badge {
    width: 42px;
    height: 42px;
    border-radius: var(--radius-sm, 8px);
    background: rgba(220, 38, 38, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
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
    margin: 0 0 4px;
}
.delete-zone-desc {
    font-size: 13px;
    color: #b91c1c;
    line-height: 1.5;
    margin: 0;
    opacity: 0.85;
}
.delete-zone-btn {
    padding: 10px 22px;
    background: var(--error, #dc2626);
    color: white;
    border: none;
    border-radius: var(--radius-sm, 8px);
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
    background: rgba(0, 0, 0, 0.45);
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
    max-width: 420px;
    width: 100%;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0,0,0,0.04);
    overflow: hidden;
    animation: slideUp 0.3s cubic-bezier(.2,.8,.3,1);
}
.delete-modal-top {
    text-align: center;
    padding: 32px 28px 20px;
}
.delete-modal-icon-ring {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #fef2f2, #fee2e2);
    border: 2px solid #fecaca;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
}
.delete-modal-top h3 {
    font-size: 20px;
    font-weight: 700;
    color: #991b1b;
    margin: 0 0 8px;
}
.delete-modal-top p {
    font-size: 14px;
    color: #7f1d1d;
    line-height: 1.6;
    margin: 0;
    opacity: 0.85;
}
.delete-modal-actions {
    display: flex;
    gap: 12px;
    padding: 4px 28px 28px;
}
.delete-modal-cancel {
    flex: 1;
    padding: 12px;
    background: #f1f5f9;
    color: var(--text-secondary, #475569);
    border: 1px solid var(--border, #e2e8f0);
    border-radius: var(--radius-sm, 8px);
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}
.delete-modal-cancel:hover {
    background: #e2e8f0;
}
.delete-modal-confirm {
    flex: 1;
    padding: 12px;
    background: var(--error, #dc2626);
    color: white;
    border: none;
    border-radius: var(--radius-sm, 8px);
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 46px;
    gap: 8px;
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
    }
    .delete-zone-btn {
        width: 100%;
        text-align: center;
    }
    .delete-modal {
        border-radius: 16px;
    }
    .delete-modal-top {
        padding: 24px 20px 16px;
    }
    .delete-modal-actions {
        padding: 0 20px 20px;
        flex-direction: column-reverse;
    }
}
""")

css_src = css_src[:start_pos].rstrip() + "\n\n" + new_delete_css
CSS.write_text(css_src, encoding="utf-8")
print(f"✅ App.css updated ({len(css_src.splitlines())} lines)")
print(f"   Delete CSS replaced from position {start_pos}")
print("\nDone! Run:  cd frontend && npx vite build  then  python _redeploy_frontend.py")
