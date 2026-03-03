"""
Fix: Input/button focus & selection highlights not fully visible across all pages.

Issues:
1. Focus box-shadow opacity is 0.08-0.1 (nearly invisible on mobile screens)
2. Border changes are subtle (1-2px from light gray to green)
3. overflow:hidden on parent containers clips the focus glow
4. No visible "selected" state for interactive elements

Fix:
- Increase focus box-shadow opacity from 0.08/0.1 → 0.25
- Make focus border 2px solid everywhere
- Ensure overflow is not clipping focus rings on form containers
- Add stronger selected/active highlights for buttons
"""
import pathlib

CSS = pathlib.Path("frontend/src/App.css")
text = CSS.read_text(encoding="utf-8")
original = text

# ── 1. .form-input:focus (Profile, general forms) ──
# Line ~1248: box-shadow: 0 0 0 3px rgba(22,163,74,0.08)
text = text.replace(
    """.form-input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(22,163,74,0.08);
}""",
    """.form-input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.25);
    background: #f0fdf4;
}"""
)

# ── 2. .input-bar input:focus (Chat page) ──
# Line ~897: box-shadow: 0 0 0 4px rgba(22,163,74,0.1)
text = text.replace(
    """.input-bar input:focus {
    border-color: var(--primary);
    background: white;
    box-shadow: 0 0 0 4px rgba(22,163,74,0.1);
}""",
    """.input-bar input:focus {
    border-color: var(--primary);
    background: #f0fdf4;
    box-shadow: 0 0 0 4px rgba(22,163,74,0.25);
}"""
)

# ── 3. .search-bar input:focus (Schemes, Price pages) ──
# Line ~1210: box-shadow: 0 0 0 4px rgba(22,163,74,0.08)
text = text.replace(
    """.search-bar input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.08);
}""",
    """.search-bar input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.25);
    background: #f0fdf4;
}"""
)

# ── 4. .price-search:focus ──
# Line ~1821
text = text.replace(
    """.price-search:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(22,163,74,0.08);""",
    """.price-search:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.25);
    background: #f0fdf4;"""
)

# ── 5. .ai-form-group select:focus, .ai-form-group input:focus ──
# (Crop Recommend, Soil Analysis, Farm Calendar)
# Line ~3820: box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.1)
text = text.replace(
    """.ai-form-group select:focus,
.ai-form-group input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.1);
}""",
    """.ai-form-group select:focus,
.ai-form-group input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.25);
    background: #f0fdf4;
}"""
)

# ── 6. Also make the ai-form-group border thicker on focus ──
# The base border is only 1px, hard to see the color change
text = text.replace(
    """.ai-form-group select,
.ai-form-group input {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid var(--border);""",
    """.ai-form-group select,
.ai-form-group input {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 2px solid var(--border);"""
)

# ── 7. .login-phone-input:focus-within ──
# Line ~2716: box-shadow: 0 0 0 4px rgba(22,163,74,0.1)
text = text.replace(
    """.login-phone-input:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.1);
}""",
    """.login-phone-input:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.25);
    background: #f0fdf4;
}"""
)

# ── 8. .otp-digit:focus ──
# Line ~2862: box-shadow: 0 0 0 4px rgba(22,163,74,0.12)
text = text.replace(
    """.otp-digit:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.12);
}""",
    """.otp-digit:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.3);
    background: #f0fdf4;
}"""
)

# ── 9. Fix overflow:hidden on .login-phone-input (clips focus glow) ──
# Line ~2711
text = text.replace(
    """    border: 2px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.2s;
    position: relative;
    z-index: 1;
}
.login-phone-input:focus-within""",
    """    border: 2px solid var(--border);
    border-radius: 12px;
    overflow: visible;
    transition: all 0.2s;
    position: relative;
    z-index: 1;
}
.login-phone-input:focus-within"""
)

# ── 10. Global focus-visible: make more prominent ──
# Line ~4257
text = text.replace(
    """:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    border-radius: 4px;
}
button:focus-visible,
a:focus-visible,
select:focus-visible,
input:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;""",
    """:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 3px;
    border-radius: 4px;
}
button:focus-visible,
a:focus-visible,
select:focus-visible,
input:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 3px;"""
)

# ── 11. Add selected/active state for selects (dropdown) after selecting a value ──
# And ensure all form selects show their selection clearly
# Add after the ai-form-group focus rules
insert_after = """.ai-form-group select:focus,
.ai-form-group input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.25);
    background: #f0fdf4;
}"""

select_highlight = """

/* Selected (non-default) select styling — shows value was picked */
.ai-form-group select:not([value=""]),
.ai-form-group select:valid,
.form-input:not(:placeholder-shown),
select.form-input:valid {
    border-color: var(--primary);
    background: #f0fdf4;
}

/* Textarea & multi-line inputs: expand focus glow */
.form-input:focus,
.ai-form-group textarea:focus {
    box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.25);
    border-color: var(--primary);
    background: #f0fdf4;
}"""

text = text.replace(insert_after, insert_after + select_highlight, 1)

# ── 12. Make the base .form-input border consistent at 2px ──
text = text.replace(
    """.form-input {
    width: 100%;
    padding: 12px 14px;
    border: 2px solid var(--border);
    border-radius: var(--radius-sm);""",
    """.form-input {
    width: 100%;
    padding: 12px 14px;
    border: 2px solid var(--border);
    border-radius: var(--radius-sm);"""
)
# Already 2px, good.

# ── 13. Add transition to ai-form inputs for smooth focus ──
text = text.replace(
    """.ai-form-group select,
.ai-form-group input {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 2px solid var(--border);
    font-size: 14px;
    background: var(--bg);
    color: var(--text);
    transition: border-color 0.2s ease;
}""",
    """.ai-form-group select,
.ai-form-group input {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 2px solid var(--border);
    font-size: 14px;
    background: var(--bg);
    color: var(--text);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}"""
)

CSS.write_text(text, encoding="utf-8")

# Verify
final = CSS.read_text(encoding="utf-8")
checks = [
    ("0 0 0 4px rgba(22,163,74,0.25)", "form-input focus glow"),
    ("0 0 0 4px rgba(22, 163, 74, 0.25)", "ai-form focus glow"),
    ("background: #f0fdf4", "focus green tint bg"),
    ("border: 2px solid var(--border);\n    font-size: 14px", "ai-form 2px border"),
    ("overflow: visible;", "login-phone overflow fix"),
    ("outline-offset: 3px", "focus-visible offset"),
    (":not(:placeholder-shown)", "non-empty input highlight"),
    ("box-shadow 0.2s ease, background 0.2s", "ai-form smooth transitions"),
    ("0 0 0 4px rgba(22,163,74,0.3)", "otp focus glow"),
]
print("=== Verification ===")
for pat, label in checks:
    found = pat in final
    print(f"{'✅' if found else '❌'} {label}: {'FOUND' if found else 'MISSING'}")

print(f"\nTotal lines: {len(final.splitlines())}")
changes = sum(1 for a, b in zip(original.splitlines(), final.splitlines()) if a != b)
print(f"Lines changed: ~{changes}")
print("Done!")
