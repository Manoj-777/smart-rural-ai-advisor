"""
Fix: Mic button overlapping Crop Doctor in bottom nav on mobile.

Root cause: 100vh on mobile browsers includes the URL bar height, so
calc(100vh - 48px - 90px) makes the chat page TALLER than the visible
area. The input bar (with mic) extends into the bottom nav zone.

Fix:
1. Use 100dvh (dynamic viewport height) with 100vh fallback
2. Increase bottom clearance from 90px → 110px
3. Give input-bar more bottom margin (4px → 10px)
"""
import re, pathlib

CSS = pathlib.Path("frontend/src/App.css")
text = CSS.read_text(encoding="utf-8")

# ── 1. In the 600px media query: chat-page height ──
# Change: calc(100vh - 48px - 90px) → calc(100dvh - 48px - 110px) with fallback
text = text.replace(
    """.chat-page {
        height: calc(100vh - 48px - 90px) !important;
    }""",
    """.chat-page {
        height: calc(100vh - 48px - 110px) !important;
        height: calc(100dvh - 48px - 110px) !important;
    }"""
)

# ── 2. Weather page same treatment ──
text = text.replace(
    """.weather-page {
        height: calc(100vh - 48px - 90px) !important;
    }""",
    """.weather-page {
        height: calc(100vh - 48px - 110px) !important;
        height: calc(100dvh - 48px - 110px) !important;
    }"""
)

# ── 3. main-content padding-bottom 90px → 110px ──
text = text.replace(
    "padding-bottom: 90px !important;",
    "padding-bottom: 110px !important;"
)

# ── 4. In 600px media query input-bar: margin 0 4px 4px → 0 4px 12px ──
text = text.replace(
    """    .input-bar {
        padding: 8px 10px;
        gap: 6px;
        margin: 0 4px 4px;""",
    """    .input-bar {
        padding: 8px 10px;
        gap: 6px;
        margin: 0 4px 12px;"""
)

# ── 5. Also fix the 480px chat-page (non-important, but good to align) ──
# calc(100vh - 44px - 82px) → calc(100vh - 44px - 110px)
text = text.replace(
    """    .chat-page {
        height: calc(100vh - 44px - 82px);""",
    """    .chat-page {
        height: calc(100vh - 44px - 110px);
        height: calc(100dvh - 44px - 110px);"""
)

CSS.write_text(text, encoding="utf-8")

# Verify
final = CSS.read_text(encoding="utf-8")
checks = [
    ("100dvh - 48px - 110px", "600px chat-page dvh"),
    ("padding-bottom: 110px", "main-content padding"),
    ("margin: 0 4px 12px", "input-bar margin"),
    ("100dvh - 44px - 110px", "480px chat-page dvh"),
]
print("=== Verification ===")
for pattern, label in checks:
    found = pattern in final
    print(f"{'✅' if found else '❌'} {label}: {'FOUND' if found else 'MISSING'}")

print(f"\nTotal lines: {len(final.splitlines())}")
print("Done!")
