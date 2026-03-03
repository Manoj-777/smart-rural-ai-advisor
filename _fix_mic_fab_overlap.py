"""
Fix: Floating MicFab button overlapping Crop Doctor in bottom nav on mobile.

Root cause: .mic-fab-wrapper is position:fixed bottom:32px right:32px z-index:1000.
The bottom nav is ~90px tall at the bottom of screen. So the 60px FAB at bottom:32px
sits directly on top of Crop Doctor (5th nav item, top-right of the 2-row grid).

Fix: Inside the 600px media query, move the FAB above the bottom nav and shrink it.
"""
import pathlib

CSS = pathlib.Path("frontend/src/App.css")
text = CSS.read_text(encoding="utf-8")

# Find the closing brace of the 600px bottom-nav media query block
# We'll add mic-fab overrides inside that block, before the closing }
#
# Current end of the 600px block (around line 4224):
#     .send-btn {
#         ...
#         flex-shrink: 0;
#     }
#
# }
#
# We need to insert BEFORE that closing }

old_block = """\
    .send-btn {
        padding: 8px 14px;
        font-size: 14px;
        border-radius: 18px;
        flex-shrink: 0;
    }

}"""

new_block = """\
    .send-btn {
        padding: 8px 14px;
        font-size: 14px;
        border-radius: 18px;
        flex-shrink: 0;
    }

    /* ── Move floating mic FAB above bottom nav on mobile ── */
    .mic-fab-wrapper {
        bottom: 105px !important;
        right: 16px !important;
    }
    .dash-mic-fab {
        width: 48px;
        height: 48px;
    }
    .dash-mic-fab svg {
        width: 22px;
        height: 22px;
    }
    .mic-fab-tooltip {
        display: none;
    }

}"""

if old_block in text:
    text = text.replace(old_block, new_block)
    print("✅ Inserted mic-fab mobile overrides in 600px media query")
else:
    print("❌ Could not find insertion point! Trying fallback...")
    # Fallback: just append a new 600px block
    text += """

/* ── Move floating mic FAB above bottom nav on mobile ── */
@media (max-width: 600px) {
    .mic-fab-wrapper {
        bottom: 105px !important;
        right: 16px !important;
    }
    .dash-mic-fab {
        width: 48px;
        height: 48px;
    }
    .dash-mic-fab svg {
        width: 22px;
        height: 22px;
    }
    .mic-fab-tooltip {
        display: none;
    }
}
"""
    print("✅ Added separate 600px media query for mic-fab")

CSS.write_text(text, encoding="utf-8")

# Verify
final = CSS.read_text(encoding="utf-8")
checks = [
    ("bottom: 105px !important", "FAB bottom position"),
    ("right: 16px !important", "FAB right position"),
    ("width: 48px", "FAB smaller size"),
]
print("\n=== Verification ===")
for pat, label in checks:
    found = pat in final
    print(f"{'✅' if found else '❌'} {label}: {'FOUND' if found else 'MISSING'}")

print(f"\nTotal lines: {len(final.splitlines())}")
print("Done!")
