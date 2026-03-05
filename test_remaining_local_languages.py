import json
import datetime as dt
import unicodedata
from pathlib import Path

import boto3

REGION = "ap-south-1"
MODEL_ID = "apac.amazon.nova-pro-v1:0"

# Remaining local languages after Tamil test (excluding English)
LANGUAGES = {
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
}

# Expected Unicode blocks (inclusive)
SCRIPT_RANGES = {
    "hi": [(0x0900, 0x097F)],  # Devanagari
    "mr": [(0x0900, 0x097F)],  # Devanagari
    "te": [(0x0C00, 0x0C7F)],  # Telugu
    "kn": [(0x0C80, 0x0CFF)],  # Kannada
    "ml": [(0x0D00, 0x0D7F)],  # Malayalam
    "bn": [(0x0980, 0x09FF)],  # Bengali
    "as": [(0x0980, 0x09FF)],  # Assamese uses Bengali block
    "gu": [(0x0A80, 0x0AFF)],  # Gujarati
    "pa": [(0x0A00, 0x0A7F)],  # Gurmukhi
    "or": [(0x0B00, 0x0B7F)],  # Odia
    "ur": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)],  # Arabic + extensions
}

SEED_PROMPT_EN = (
    "My paddy leaves are turning yellow. Give short, practical farming advice "
    "with likely causes, immediate steps, and dosage guidance."
)

PROMPT_OVERRIDES = {
    "or": "ମୋ ଧାନ ପତ୍ର ପୀତ ହେଉଛି। ସମ୍ଭାବ୍ୟ କାରଣ, ତୁରନ୍ତ କଣ କରିବି, ଏବଂ ଛୋଟ ବ୍ୟବହାରିକ କୃଷି ପରାମର୍ଶ ଦିଅ।",
    "as": "মোৰ ধানৰ পাত পীত হৈ আছে। সম্ভাৱ্য কাৰণ, তৎক্ষণাত কি কৰিব, আৰু চুটি ব্যৱহাৰিক কৃষি পৰামৰ্শ দিয়ক।",
}

SAFE_RETRY_PROMPTS = {
    "te": "నా వరి ఆకులు పసుపు రంగులోకి మారుతున్నాయి. కారణం ఏమిటి? సులభమైన రైతు సలహా ఇవ్వండి.",
}


def _is_letter(ch: str) -> bool:
    return unicodedata.category(ch).startswith("L")


def _in_ranges(ch: str, ranges: list[tuple[int, int]]) -> bool:
    cp = ord(ch)
    return any(start <= cp <= end for start, end in ranges)


def _analyze_script(text: str, lang: str) -> dict:
    letters = [c for c in text if _is_letter(c)]
    if not letters:
        return {
            "letter_count": 0,
            "latin_ratio": 0.0,
            "expected_script_ratio": 0.0,
            "control_char_count": 0,
            "replacement_char_count": 0,
        }

    latin = sum(1 for c in letters if "LATIN" in unicodedata.name(c, ""))
    expected = sum(1 for c in letters if _in_ranges(c, SCRIPT_RANGES.get(lang, [])))

    control_count = sum(1 for c in text if unicodedata.category(c) == "Cc")
    replacement_count = text.count("\uFFFD")

    return {
        "letter_count": len(letters),
        "latin_ratio": round(latin / len(letters), 4),
        "expected_script_ratio": round(expected / len(letters), 4),
        "control_char_count": control_count,
        "replacement_char_count": replacement_count,
    }


def _translate_seed(translate_client, lang: str) -> str:
    if lang in PROMPT_OVERRIDES:
        return PROMPT_OVERRIDES[lang]
    out = translate_client.translate_text(
        Text=SEED_PROMPT_EN,
        SourceLanguageCode="en",
        TargetLanguageCode=lang,
    )
    return out["TranslatedText"]


def _invoke_model(runtime_client, prompt: str) -> dict:
    request_body = {
        "schemaVersion": "messages-v1",
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        # Intentionally no maxTokens to use model defaults
    }
    response = runtime_client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(request_body),
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(response["body"].read())
    text = ""
    try:
        text = payload["output"]["message"]["content"][0].get("text", "")
    except Exception:
        text = ""
    return {"payload": payload, "text": text}


def main() -> None:
    translate = boto3.client("translate", region_name=REGION)
    runtime = boto3.client("bedrock-runtime", region_name=REGION)

    results = []

    for code, name in LANGUAGES.items():
        try:
            prompt_local = _translate_seed(translate, code)
            model_resp = _invoke_model(runtime, prompt_local)
            payload = model_resp["payload"]
            text = model_resp["text"]

            if payload.get("stopReason") == "content_filtered" and code in SAFE_RETRY_PROMPTS:
                prompt_local = SAFE_RETRY_PROMPTS[code]
                model_resp = _invoke_model(runtime, prompt_local)
                payload = model_resp["payload"]
                text = model_resp["text"]

            quality = _analyze_script(text, code)

            flags = []
            if quality["latin_ratio"] > 0.25:
                flags.append("mixed_english_high")
            if quality["expected_script_ratio"] < 0.50:
                flags.append("expected_script_low")
            if quality["replacement_char_count"] > 0:
                flags.append("replacement_char_found")
            if quality["control_char_count"] > 0:
                flags.append("control_char_found")

            results.append(
                {
                    "language_code": code,
                    "language_name": name,
                    "prompt_local": prompt_local,
                    "stop_reason": payload.get("stopReason"),
                    "usage": payload.get("usage", {}),
                    "quality": quality,
                    "flags": flags,
                    "response_preview": text[:500],
                    "response_full": text,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "language_code": code,
                    "language_name": name,
                    "error": str(exc),
                }
            )

    total = len(results)
    ok = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    flagged = [r for r in ok if r.get("flags")]

    summary = {
        "total_languages": total,
        "successful": len(ok),
        "failed": len(errors),
        "flagged": len(flagged),
        "model": MODEL_ID,
        "region": REGION,
        "note": "Direct Bedrock invoke with no explicit maxTokens",
    }

    report = {
        "timestamp_utc": dt.datetime.now(dt.UTC).isoformat(),
        "seed_prompt_en": SEED_PROMPT_EN,
        "summary": summary,
        "results": results,
    }

    out = Path("artifacts") / "remaining_local_languages_test_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(str(out))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
