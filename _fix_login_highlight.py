"""Fix double-highlight glitch on login page phone input and OTP digits.

Problem: When user taps the phone number box, TWO green outlines appear:
  1) .login-phone-input:focus-within → border + box-shadow on wrapper
  2) input:focus-visible → outline: 2px solid green on inner input
This creates a "double green line" glitch.

Same issue on OTP digit inputs and any .form-input that has both
custom :focus styles AND the global :focus-visible outline.
"""
import pathlib

CSS = pathlib.Path("frontend/src/App.css")
text = CSS.read_text(encoding="utf-8")
count = 0

# ── 1. Suppress focus-visible outline on login phone inner input ──
old1 = """.login-phone-input input {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text);
    padding: 14px;
    font-size: 16px;
    letter-spacing: 1px;
    outline: none;
    min-width: 0;
    pointer-events: auto;
    cursor: text;
}"""

new1 = """.login-phone-input input {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text);
    padding: 14px;
    font-size: 16px;
    letter-spacing: 1px;
    outline: none;
    min-width: 0;
    pointer-events: auto;
    cursor: text;
}
.login-phone-input input:focus,
.login-phone-input input:focus-visible {
    outline: none !important;
    box-shadow: none !important;
    border: none;
}"""

if old1 in text:
    text = text.replace(old1, new1)
    count += 1
    print("  1: Suppressed double outline on login phone input")
else:
    print("X 1: login-phone-input input not matched")

# ── 2. Suppress focus-visible outline on OTP digits ──
old2 = """.otp-digit:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.3);
    background: #f0fdf4;
}"""

new2 = """.otp-digit:focus,
.otp-digit:focus-visible {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,163,74,0.3);
    background: #f0fdf4;
    outline: none !important;
}"""

if old2 in text:
    text = text.replace(old2, new2)
    count += 1
    print("  2: Suppressed double outline on OTP digits")
else:
    print("X 2: otp-digit:focus not matched")

# ── 3. Remove .form-input:not(:placeholder-shown) permanent highlight ──
old3 = """/* Selected (non-default) select styling"""
idx3 = text.find(old3)
if idx3 >= 0:
    end3 = text.find("}", idx3)
    block = text[idx3:end3+1]
    # Remove .form-input:not(:placeholder-shown) from the selector list
    new_block = block.replace(".form-input:not(:placeholder-shown),\n", "")
    text = text.replace(block, new_block)
    count += 1
    print("  3: Removed .form-input:not(:placeholder-shown) permanent highlight")
else:
    print("X 3: selected styling block not found")

# ── 4. Remove duplicate .form-input:focus at line ~3858 ──
old4 = """/* Textarea & multi-line inputs: expand focus glow */
.form-input:focus,
.ai-form-group textarea:focus {"""

new4 = """/* Textarea & multi-line inputs: expand focus glow */
.ai-form-group textarea:focus {"""

if old4 in text:
    text = text.replace(old4, new4)
    count += 1
    print("  4: Removed duplicate .form-input:focus rule")
else:
    print("X 4: duplicate form-input:focus not matched")

# ── 5. Add focus-visible suppression for ALL custom-styled inputs ──
old5 = """button:focus-visible,
a:focus-visible,
select:focus-visible,
input:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 3px;
}"""

new5 = """button:focus-visible,
a:focus-visible,
select:focus-visible,
input:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 3px;
}
/* Suppress double outline on elements that already have custom :focus box-shadow */
.form-input:focus-visible,
.search-bar input:focus-visible,
.input-bar input:focus-visible,
.price-search:focus-visible,
.price-filter:focus-visible,
.ai-form-group select:focus-visible,
.ai-form-group input:focus-visible,
.login-phone-input input:focus-visible,
.otp-digit:focus-visible,
.top-bar__lang-select:focus-visible,
.navbar-lang-select:focus-visible {
    outline: none !important;
}"""

if old5 in text:
    text = text.replace(old5, new5)
    count += 1
    print("  5: Added focus-visible suppression for custom-styled inputs")
else:
    print("X 5: focus-visible block not matched")

# ── 6. Revert login-phone-input overflow to hidden ──
if "overflow: visible;" in text:
    text = text.replace(
        "overflow: visible;\n    transition: all 0.2s;\n    position: relative;\n    z-index: 1;\n}\n.login-phone-input:focus-within",
        "overflow: hidden;\n    transition: all 0.2s;\n    position: relative;\n    z-index: 1;\n}\n.login-phone-input:focus-within"
    )
    count += 1
    print("  6: Reverted login-phone-input overflow to hidden")
else:
    print("  6: overflow already hidden (skip)")

CSS.write_text(text, encoding="utf-8")

# ── Verify ──
final = CSS.read_text(encoding="utf-8")
print(f"\n=== Verification ({count} changes applied) ===")

checks = [
    (".login-phone-input input:focus-visible", "phone input outline suppressed"),
    (".otp-digit:focus-visible", "OTP outline suppressed"),
    (".form-input:focus-visible,", "form-input outline suppressed"),
    ("overflow: hidden", "login-phone overflow hidden"),
]
for pat, label in checks:
    status = "OK" if pat in final else "MISSING"
    print(f"  [{status}] {label}")

if ".form-input:not(:placeholder-shown)" not in final:
    print("  [OK] No permanent placeholder-shown highlight")
else:
    print("  [MISSING] placeholder-shown still present")

print(f"\nTotal lines: {len(final.splitlines())}")
print("Done!")
