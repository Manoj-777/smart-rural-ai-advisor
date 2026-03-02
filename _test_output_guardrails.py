#!/usr/bin/env python3
"""Test output guardrails — PII leakage, prompt leakage, truncation."""
import sys
sys.path.insert(0, 'backend')
from utils.guardrails import run_output_guardrails

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASSED: {name}")
    else:
        failed += 1
        print(f"  FAILED: {name} — {detail}")

print("=" * 60)
print("OUTPUT GUARDRAILS UNIT TESTS")
print("=" * 60)
print()

# Test 1: Clean output passes through unchanged
print("Test 1: Clean agricultural response")
r = run_output_guardrails("Rice is best grown in kharif season. Apply urea at 2 bags/acre.")
test("Not modified", not r['modified'])
test("Text unchanged", r['text'] == "Rice is best grown in kharif season. Apply urea at 2 bags/acre.")
print()

# Test 2: PII in output gets masked (Aadhaar)
print("Test 2: Aadhaar leakage in output")
r = run_output_guardrails("Based on your Aadhaar 2345 6789 0123, you are eligible for PM-KISAN scheme.")
test("Modified", r['modified'])
test("PII detected", len(r['pii_masked']) > 0)
test("Aadhaar masked", "2345 6789 0123" not in r['text'])
print(f"  -> Cleaned: {r['text'][:100]}")
print(f"  -> PII types: {r['pii_masked']}")
print()

# Test 3: Phone number leakage
print("Test 3: Phone number leakage in output")
r = run_output_guardrails("We sent a confirmation to your phone 9876543210. Your PM-KISAN registration is active.")
test("Modified", r['modified'])
test("Phone masked", "9876543210" not in r['text'])
print(f"  -> PII types: {r['pii_masked']}")
print()

# Test 4: Email leakage
print("Test 4: Email leakage in output")
r = run_output_guardrails("Your registration email farmer.rajesh@gmail.com has been confirmed for the scheme.")
test("Modified", r['modified'])
test("Email masked", "farmer.rajesh@gmail.com" not in r['text'])
print(f"  -> PII types: {r['pii_masked']}")
print()

# Test 5: System prompt leakage — Understanding Agent
print("Test 5: System prompt leakage (Understanding Agent)")
r = run_output_guardrails(
    "You are the Understanding Agent in a multi-agent agricultural advisory system. "
    "Your job is to analyze the farmer's query."
)
test("Modified", r['modified'])
test("Prompt leaked flag", r['prompt_leaked'])
test("Response replaced", "Understanding Agent" not in r['text'])
print(f"  -> Replaced with: {r['text'][:80]}")
print()

# Test 6: System prompt leakage — internal keywords
print("Test 6: Internal keyword leakage (system_prompt)")
r = run_output_guardrails("The system_prompt instructs me to help with farming. Here is advice about rice cultivation.")
test("Prompt leaked flag", r['prompt_leaked'])
test("Response replaced", "system_prompt" not in r['text'])
print()

# Test 7: System prompt leakage — inferenceConfig
print("Test 7: Internal keyword leakage (inferenceConfig)")
r = run_output_guardrails("My inferenceConfig has maxTokens set to 1024. Anyway, for rice farming...")
test("Prompt leaked flag", r['prompt_leaked'])
print()

# Test 8: System prompt leakage — Bedrock AgentCore
print("Test 8: Internal keyword leakage (Bedrock AgentCore)")
r = run_output_guardrails("I'm running on Bedrock AgentCore with a cognitive pipeline. Your crops need water.")
test("Prompt leaked flag", r['prompt_leaked'])
print()

# Test 9: Output truncation
print("Test 9: Long output truncation")
long_text = "This is farming advice about rice cultivation in India. " * 200
r = run_output_guardrails(long_text)
test("Modified", r['modified'])
test("Truncated flag", r['truncated'])
test("Under cap", len(r['text']) < 8200, f"got {len(r['text'])}")
test("Has trim notice", "trimmed" in r['text'].lower())
print(f"  -> Original: {r['original_length']} chars -> Output: {len(r['text'])} chars")
print()

# Test 10: Multiple PII types
print("Test 10: Multiple PII types in single output")
r = run_output_guardrails(
    "Your phone 9876543210, email farmer@example.com, and PAN ABCDE1234F "
    "are all linked to your PM-KISAN account."
)
test("Multiple PII types", len(r['pii_masked']) >= 2, f"got {r['pii_masked']}")
test("Phone masked", "9876543210" not in r['text'])
test("Email masked", "farmer@example.com" not in r['text'])
print(f"  -> PII types: {r['pii_masked']}")
print()

# Test 11: Empty/None input
print("Test 11: Edge cases (empty, None)")
r = run_output_guardrails("")
test("Empty string OK", not r['modified'])
r = run_output_guardrails(None)
test("None OK", not r['modified'])
print()

# Test 12: Normal farming text with numbers (no false positives)
print("Test 12: No false positives on farming numbers")
r = run_output_guardrails(
    "Apply 150 kg urea per hectare. Temperature today is 32 degrees. "
    "Rainfall expected: 45mm over 3 days. Yield potential: 4.5 tonnes/acre."
)
test("Not modified", not r['modified'], "Farming numbers shouldn't trigger PII")
print()

print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED!")
    sys.exit(1)
print("=" * 60)
