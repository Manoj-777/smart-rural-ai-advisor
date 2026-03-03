"""
Fix mic button positioning on mobile:
1. Adjust chat page height to account for bottom nav
2. Compact mic button on mobile  
3. Fix input bar layout for small screens
4. Hide voice status text on mobile (save space)
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CSS  = ROOT / 'frontend' / 'src' / 'App.css'

lines = CSS.read_text(encoding='utf-8').splitlines(keepends=True)

def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1

def find_closing_brace(start):
    brace = 0
    for i in range(start, len(lines)):
        brace += lines[i].count('{') - lines[i].count('}')
        if brace == 0:
            return i
    return -1

changes = 0

# ── 1. Fix 480px chat-page height to account for bottom nav ──
# Find the 480px breakpoint's .chat-page rule
idx_480 = find_line('@media (max-width: 480px)')
if idx_480 >= 0:
    idx_chat_480 = find_line('.chat-page {', idx_480)
    if idx_chat_480 >= 0 and idx_chat_480 < idx_480 + 500:
        end_chat_480 = find_closing_brace(idx_chat_480)
        new_chat_480 = """    .chat-page {
        height: calc(100vh - 44px - 82px);
        gap: 0;
    }
"""
        lines[idx_chat_480:end_chat_480+1] = [new_chat_480]
        print(f'[OK] Fixed 480px chat-page height (accounts for bottom nav)')
        changes += 1

# ── 2. Add mobile-specific mic button and input bar fixes ──
# Find the bottom nav's 600px media query and add input bar fixes there
idx_bottom_600 = find_line('@media (max-width: 600px)', find_line('Bottom Navigation'))
if idx_bottom_600 >= 0:
    # Find the closing brace of this media query
    end_600 = find_closing_brace(idx_bottom_600)
    
    # Insert new rules before the closing brace
    mobile_input_fixes = """
    /* ── Chat input bar: compact for mobile with bottom nav ── */
    .input-bar {
        padding: 8px 10px;
        gap: 6px;
        margin: 0 4px 4px;
        border-radius: 12px;
        position: relative;
        z-index: 10;
    }
    .input-bar input {
        padding: 8px 12px;
        font-size: 14px;
        border-radius: 20px;
        min-width: 0;
    }
    
    /* Compact mic button on phone */
    .mic-btn {
        width: 38px;
        height: 38px;
        font-size: 17px;
        flex-shrink: 0;
    }
    
    /* Hide voice status label on phone to save space */
    .voice-status {
        display: none;
    }
    
    /* Compact send button */
    .input-bar .send-btn {
        padding: 8px 12px;
        font-size: 13px;
        border-radius: 20px;
        white-space: nowrap;
    }
    
    /* Voice input group: no gap needed when status is hidden */
    .voice-input-group {
        flex-shrink: 0;
    }

"""
    lines.insert(end_600, mobile_input_fixes)
    print(f'[OK] Added mobile input bar + mic button fixes in 600px breakpoint')
    changes += 1

# ── 3. Also fix the 480px section's send-btn and add mic fixes ──
# Find the 480px send-btn rule (around line 3399)
idx_480_send = find_line('.send-btn {', idx_480)
if idx_480_send >= 0 and idx_480_send < idx_480 + 500:
    end_480_send = find_closing_brace(idx_480_send)
    new_480_send = """    .send-btn {
        padding: 7px 10px;
        font-size: 12px;
    }
    .mic-btn {
        width: 34px;
        height: 34px;
        font-size: 16px;
    }
    .input-bar {
        padding: 6px 8px;
        gap: 5px;
        margin: 0 2px 2px;
    }
    .input-bar input {
        padding: 7px 10px;
        font-size: 13px;
    }
"""
    lines[idx_480_send:end_480_send+1] = [new_480_send]
    print(f'[OK] Updated 480px send-btn + mic + input bar')
    changes += 1

# ── 4. Fix 600px breakpoint chat-page height too ──
idx_600_main = find_line('@media (max-width: 600px)')
if idx_600_main >= 0 and idx_600_main < 1000:
    # There may be a chat-page inside this block
    pass  # The bottom nav 600px block already handles this

# ── 5. Also update the base large-screen 600px chat height ──
# The existing bottom-nav block already has 
# .chat-page { height: calc(100vh - 48px - 90px) !important; }
# Let's verify it's correct - should match the nav + bottom bar
idx_bn_chat = find_line('.chat-page', find_line('Ensure content'))
if idx_bn_chat >= 0:
    end_bn_chat = find_closing_brace(idx_bn_chat)
    cur_chat = ''.join(lines[idx_bn_chat:end_bn_chat+1])
    print(f'[INFO] Bottom-nav chat-page rule: {cur_chat.strip()}')

CSS.write_text(''.join(lines), encoding='utf-8')
print(f'\n\u2705 Done! {changes} mic/input fixes applied.')
print('Next: cd frontend && npx vite build')
