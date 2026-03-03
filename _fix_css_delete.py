"""Append delete-strip and delete-popup CSS to App.css"""

path = r'frontend\src\App.css'

css_to_append = """

/* ═══════════════════════════════════════════════════════════════════════
   Delete Account — Compact Strip & Yes/No Popup
   ═══════════════════════════════════════════════════════════════════════ */
.delete-strip {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 24px;
    margin-bottom: 20px;
    padding: 10px 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 10px;
}
.delete-strip-text {
    flex: 1;
    font-size: 12px;
    color: #991b1b;
    line-height: 1.4;
    opacity: 0.8;
}
.delete-strip-btn {
    padding: 6px 14px;
    background: transparent;
    color: #dc2626;
    border: 1.5px solid #dc2626;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.delete-strip-btn:hover {
    background: #dc2626;
    color: white;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.25);
}
.delete-strip-btn:active {
    transform: scale(0.96);
}

/* Delete Yes/No Popup */
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
    max-width: 320px;
    width: 100%;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.delete-popup-body {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 20px 20px 16px;
}
.delete-popup-body svg {
    flex-shrink: 0;
    margin-top: 1px;
}
.delete-popup-body p {
    font-size: 13.5px;
    color: #374151;
    line-height: 1.5;
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
    .delete-strip {
        flex-wrap: wrap;
        gap: 8px;
    }
    .delete-strip-btn {
        width: 100%;
        text-align: center;
    }
    .delete-popup {
        max-width: calc(100vw - 32px);
    }
    .delete-popup-actions {
        flex-direction: column-reverse;
    }
}
"""

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Before: {len(content)} chars")

content += css_to_append

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"After: {len(content)} chars")

# Verify
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
print(f"  delete-strip: {'delete-strip' in c}")
print(f"  delete-popup: {'delete-popup' in c}")
