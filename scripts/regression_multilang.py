import argparse
import json
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import boto3
from botocore.config import Config

DEFAULT_REGION = "ap-south-1"
DEFAULT_FUNCTION = "smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM"
DEFAULT_PROMPT_BANK = Path("tests/phase3_prompt_bank.json")
DEFAULT_OUT_DIR = Path("artifacts")

DEFAULT_LANGUAGES = [
    "en", "ta", "hi", "te"
]

SCRIPT_RANGES = {
    "ta": [(0x0B80, 0x0BFF)],
    "hi": [(0x0900, 0x097F)],
    "mr": [(0x0900, 0x097F)],
    "te": [(0x0C00, 0x0C7F)],
    "kn": [(0x0C80, 0x0CFF)],
    "ml": [(0x0D00, 0x0D7F)],
    "bn": [(0x0980, 0x09FF)],
    "as": [(0x0980, 0x09FF)],
    "gu": [(0x0A80, 0x0AFF)],
    "pa": [(0x0A00, 0x0A7F)],
    "or": [(0x0B00, 0x0B7F)],
    "ur": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)],
}

BLOCK_HINTS = [
    "i can help only with agriculture",
    "only with farming",
    "not related to farming",
    "outside my scope",
    "cannot help with",
    "can\'t help with",
    "safety",
    "guardrail",
]

RATE_LIMIT_HINTS = [
    "rate limit exceeded",
    "too many requests",
]


@dataclass
class HarnessConfig:
    region: str
    function_name: str
    prompt_bank_path: Path
    out_dir: Path
    languages: list[str]
    max_workers: int
    delay_sec: float
    retry_count: int
    min_reply_chars: int
    min_pass_rate: float
    min_lang_pass_rate: float
    core_limit: int
    edge_limit: int


def _is_letter(ch: str) -> bool:
    return unicodedata.category(ch).startswith("L")


def _count_disallowed_control_chars(text: str) -> int:
    allowed_controls = {"\n", "\r", "\t"}
    return sum(
        1
        for c in text
        if unicodedata.category(c) == "Cc" and c not in allowed_controls
    )


def _in_ranges(ch: str, ranges: list[tuple[int, int]]) -> bool:
    cp = ord(ch)
    for start, end in ranges:
        if start <= cp <= end:
            return True
    return False


def _script_quality(text: str, lang: str) -> dict:
    letters = [c for c in text if _is_letter(c)]
    if not letters:
        return {
            "letter_count": 0,
            "latin_ratio": 0.0,
            "expected_script_ratio": 0.0,
            "replacement_char_count": text.count("\uFFFD"),
            "control_char_count": _count_disallowed_control_chars(text),
        }

    latin = sum(1 for c in letters if "LATIN" in unicodedata.name(c, ""))
    expected = sum(1 for c in letters if _in_ranges(c, SCRIPT_RANGES.get(lang, [])))

    return {
        "letter_count": len(letters),
        "latin_ratio": round(latin / len(letters), 4),
        "expected_script_ratio": round(expected / len(letters), 4),
        "replacement_char_count": text.count("\uFFFD"),
        "control_char_count": _count_disallowed_control_chars(text),
    }


def _load_prompt_bank(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_prompt(raw_prompt: dict) -> str:
    text = raw_prompt.get("text", "")
    repeat = raw_prompt.get("repeat", 1)
    if isinstance(repeat, int) and repeat > 1:
        text = text * repeat
    return text


def _translate_prompt(translate_client, prompt_en: str, target_lang: str, cache: dict[tuple[str, str], str]) -> str:
    if not (prompt_en or "").strip():
        return prompt_en

    if target_lang == "en":
        return prompt_en

    cache_key = (target_lang, prompt_en)
    if cache_key in cache:
        return cache[cache_key]

    response = translate_client.translate_text(
        Text=prompt_en,
        SourceLanguageCode="en",
        TargetLanguageCode=target_lang,
    )
    text = response.get("TranslatedText", "")
    cache[cache_key] = text
    return text


def _invoke_chat(lambda_client, function_name: str, message: str, language: str, session_id: str, farmer_id: str) -> dict:
    event = {
        "httpMethod": "POST",
        "path": "/chat",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": message,
                "language": language,
                "session_id": session_id,
                "farmer_id": farmer_id,
            },
            ensure_ascii=False,
        ),
    }

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event, ensure_ascii=False).encode("utf-8"),
    )

    outer = json.loads(response["Payload"].read().decode("utf-8"))
    status_code = outer.get("statusCode", 0)

    body_raw = outer.get("body", "{}")
    if isinstance(body_raw, str):
        try:
            body = json.loads(body_raw)
        except Exception:
            body = {}
    elif isinstance(body_raw, dict):
        body = body_raw
    else:
        body = {}

    data = body.get("data", {}) if isinstance(body, dict) else {}
    if not isinstance(data, dict):
        data = {}
    reply = (data.get("reply") or "").strip()
    reply_en = (data.get("reply_en") or "").strip()

    return {
        "status_code": status_code,
        "body": body,
        "data": data,
        "reply": reply,
        "reply_en": reply_en,
    }


def _is_rate_limited(reply: str, reply_en: str) -> bool:
    merged = f"{reply} {reply_en}".lower()
    return any(h in merged for h in RATE_LIMIT_HINTS)


def _evaluate_core(result: dict, lang: str, min_reply_chars: int) -> tuple[str, list[str], dict]:
    reasons = []
    status = "PASS"

    status_code = result["status_code"]
    reply = result["reply"]
    reply_en = result["reply_en"]

    if status_code != 200:
        status = "FAIL"
        reasons.append(f"http_{status_code}")

    merged = f"{reply} {reply_en}".strip()
    if len(merged) < min_reply_chars:
        status = "FAIL"
        reasons.append("short_reply")

    if "traceback" in merged.lower() or "nonetype" in merged.lower():
        status = "FAIL"
        reasons.append("crash_signature")

    quality = _script_quality(reply, lang)

    if lang != "en" and quality["letter_count"] >= 20:
        if quality["expected_script_ratio"] < 0.45:
            status = "FAIL"
            reasons.append("expected_script_low")
        if quality["latin_ratio"] > 0.45:
            status = "FAIL"
            reasons.append("latin_ratio_high")

    if quality["replacement_char_count"] > 0:
        status = "FAIL"
        reasons.append("replacement_char_found")

    if quality["control_char_count"] > 0:
        status = "FAIL"
        reasons.append("control_char_found")

    return status, reasons, quality


def _evaluate_edge(result: dict, expected_status_any: list[int]) -> tuple[str, list[str], dict]:
    reasons = []
    status = "PASS"

    status_code = result["status_code"]
    reply = result["reply"]
    reply_en = result["reply_en"]
    merged = f"{reply} {reply_en}".strip()

    if status_code not in expected_status_any:
        status = "FAIL"
        reasons.append(f"unexpected_http_{status_code}")

    if status_code >= 500:
        status = "FAIL"
        reasons.append("server_error")

    lower_text = merged.lower()
    if "traceback" in lower_text or "nonetype" in lower_text:
        status = "FAIL"
        reasons.append("crash_signature")

    if "offtopic" in lower_text or any(h in lower_text for h in BLOCK_HINTS):
        reasons.append("safe_block_or_redirect")

    quality = {
        "letter_count": 0,
        "latin_ratio": 0.0,
        "expected_script_ratio": 0.0,
        "replacement_char_count": merged.count("\uFFFD"),
        "control_char_count": _count_disallowed_control_chars(merged),
    }

    if quality["replacement_char_count"] > 0:
        status = "FAIL"
        reasons.append("replacement_char_found")

    if quality["control_char_count"] > 0:
        status = "FAIL"
        reasons.append("control_char_found")

    return status, reasons, quality


def _run_case(
    cfg: HarnessConfig,
    lambda_client,
    translate_client,
    translation_cache: dict,
    lang: str,
    scenario: dict,
    case_type: str,
    sequence_id: int,
) -> dict:
    prompt_en = _build_prompt(scenario)
    prompt_local = _translate_prompt(translate_client, prompt_en, lang, translation_cache)

    sid = f"phase3-{lang}-{sequence_id}-{int(time.time())}"
    fid = f"phase3-farmer-{lang}-{sequence_id}"

    t0 = time.time()
    latest = None
    retry_used = 0

    for attempt in range(1, cfg.retry_count + 1):
        latest = _invoke_chat(lambda_client, cfg.function_name, prompt_local, lang, sid, fid)
        if not _is_rate_limited(latest["reply"], latest["reply_en"]):
            break
        retry_used = attempt
        if attempt < cfg.retry_count:
            time.sleep(2.0)

    latency = round(time.time() - t0, 3)

    if case_type == "core":
        verdict, reasons, quality = _evaluate_core(latest, lang, cfg.min_reply_chars)
    else:
        expected_status_any = scenario.get("expected_status_any", [200, 400])
        verdict, reasons, quality = _evaluate_edge(latest, expected_status_any)

    return {
        "case_id": scenario.get("id"),
        "case_type": case_type,
        "language": lang,
        "tags": scenario.get("tags", []),
        "status": verdict,
        "reasons": reasons,
        "latency_sec": latency,
        "status_code": latest["status_code"],
        "retry_used": retry_used,
        "prompt_en": prompt_en,
        "prompt_local": prompt_local,
        "reply_full": latest.get("reply") or "",
        "reply_en_full": latest.get("reply_en") or "",
        "reply_preview": (latest.get("reply") or "")[:500],
        "reply_en_preview": (latest.get("reply_en") or "")[:500],
        "quality": quality,
        "localization_mode": latest.get("data", {}).get("localization_mode"),
        "pipeline_mode": latest.get("data", {}).get("pipeline_mode"),
        "tools": latest.get("data", {}).get("tools_used") or latest.get("data", {}).get("tools") or [],
    }


def _build_work_items(prompt_bank: dict, languages: list[str]) -> list[tuple[str, str, dict, int]]:
    items = []
    sequence = 0

    for lang in languages:
        for case in prompt_bank.get("core_prompts", []):
            sequence += 1
            items.append((lang, "core", case, sequence))
        for case in prompt_bank.get("edge_prompts", []):
            sequence += 1
            items.append((lang, "edge", case, sequence))

    return items


def _summarize(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    by_language = {}
    for row in results:
        lang = row["language"]
        if lang not in by_language:
            by_language[lang] = {
                "total": 0,
                "pass": 0,
                "fail": 0,
                "avg_latency_sec": 0.0,
            }
        bucket = by_language[lang]
        bucket["total"] += 1
        if row["status"] == "PASS":
            bucket["pass"] += 1
        else:
            bucket["fail"] += 1

    for lang, bucket in by_language.items():
        latencies = [r["latency_sec"] for r in results if r["language"] == lang]
        bucket["avg_latency_sec"] = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
        bucket["pass_rate"] = round(bucket["pass"] / bucket["total"], 4) if bucket["total"] else 0.0

    return {
        "total": total,
        "pass": passed,
        "fail": failed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "by_language": by_language,
    }


def _write_markdown_report(path: Path, summary: dict, config: HarnessConfig, failures: list[dict]) -> None:
    lines = []
    lines.append("# Phase 3 Multilingual Regression Report")
    lines.append("")
    lines.append(f"- Timestamp (UTC): {datetime.now(UTC).isoformat()}")
    lines.append(f"- Region: {config.region}")
    lines.append(f"- Lambda: {config.function_name}")
    lines.append(f"- Languages: {', '.join(config.languages)}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total cases: {summary['total']}")
    lines.append(f"- Pass: {summary['pass']}")
    lines.append(f"- Fail: {summary['fail']}")
    lines.append(f"- Pass rate: {round(summary['pass_rate'] * 100, 2)}%")
    lines.append("")
    lines.append("## Per Language")
    lines.append("")
    lines.append("| Language | Total | Pass | Fail | Pass Rate | Avg Latency (s) |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for lang, row in sorted(summary["by_language"].items()):
        lines.append(
            f"| {lang} | {row['total']} | {row['pass']} | {row['fail']} | {round(row['pass_rate'] * 100, 2)}% | {row['avg_latency_sec']} |"
        )

    lines.append("")
    lines.append("## Failures (Top 100)")
    lines.append("")
    if not failures:
        lines.append("- None")
    else:
        for row in failures[:100]:
            lines.append(
                f"- {row['case_id']} [{row['language']}/{row['case_type']}] status={row['status_code']} reasons={','.join(row['reasons'])}"
            )
            lines.append(f"  - prompt: {row['prompt_en'][:180]}")
            lines.append(f"  - reply: {row['reply_preview'][:220]}")

    path.write_text("\n".join(lines), encoding="utf-8")


def run_harness(cfg: HarnessConfig) -> int:
    prompt_bank = _load_prompt_bank(cfg.prompt_bank_path)

    if cfg.core_limit > 0:
        prompt_bank["core_prompts"] = prompt_bank.get("core_prompts", [])[:cfg.core_limit]
    if cfg.edge_limit > 0:
        prompt_bank["edge_prompts"] = prompt_bank.get("edge_prompts", [])[:cfg.edge_limit]

    aws_config = Config(
        connect_timeout=10,
        read_timeout=90,
        retries={"max_attempts": 2, "mode": "standard"},
    )
    lambda_client = boto3.client("lambda", region_name=cfg.region, config=aws_config)
    translate_client = boto3.client("translate", region_name=cfg.region, config=aws_config)
    translation_cache: dict[tuple[str, str], str] = {}

    work_items = _build_work_items(prompt_bank, cfg.languages)

    results: list[dict] = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=cfg.max_workers) as pool:
        futures = {}
        for i, (lang, case_type, case, seq) in enumerate(work_items):
            if i > 0 and cfg.delay_sec > 0:
                time.sleep(cfg.delay_sec)
            fut = pool.submit(
                _run_case,
                cfg,
                lambda_client,
                translate_client,
                translation_cache,
                lang,
                case,
                case_type,
                seq,
            )
            futures[fut] = (lang, case_type, case.get("id"))

        completed = 0
        total = len(futures)
        for fut in as_completed(futures):
            completed += 1
            row = fut.result()
            results.append(row)
            print(
                f"[{completed}/{total}] {row['status']:4s} {row['language']} {row['case_id']} "
                f"http={row['status_code']} latency={row['latency_sec']}s"
            )

    elapsed = round(time.time() - start, 2)

    summary = _summarize(results)
    summary["elapsed_sec"] = elapsed
    summary["thresholds"] = {
        "min_pass_rate": cfg.min_pass_rate,
        "min_lang_pass_rate": cfg.min_lang_pass_rate,
    }

    failures = [r for r in results if r["status"] != "PASS"]

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    cfg.out_dir.mkdir(parents=True, exist_ok=True)

    json_path = cfg.out_dir / f"phase3_regression_report_{timestamp}.json"
    md_path = cfg.out_dir / f"phase3_regression_report_{timestamp}.md"

    payload = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "config": {
            "region": cfg.region,
            "function": cfg.function_name,
            "prompt_bank": str(cfg.prompt_bank_path),
            "languages": cfg.languages,
            "max_workers": cfg.max_workers,
            "delay_sec": cfg.delay_sec,
            "retry_count": cfg.retry_count,
            "min_reply_chars": cfg.min_reply_chars,
            "min_pass_rate": cfg.min_pass_rate,
            "min_lang_pass_rate": cfg.min_lang_pass_rate,
        },
        "summary": summary,
        "results": sorted(results, key=lambda x: (x["language"], x["case_type"], x["case_id"])),
    }

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown_report(md_path, summary, cfg, failures)

    print("\n=== PHASE 3 SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    overall_ok = summary["pass_rate"] >= cfg.min_pass_rate
    per_lang_ok = all(
        row["pass_rate"] >= cfg.min_lang_pass_rate
        for row in summary["by_language"].values()
    )

    return 0 if (overall_ok and per_lang_ok) else 1


def parse_args() -> HarnessConfig:
    parser = argparse.ArgumentParser(description="Phase 3 multilingual regression harness")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--function", dest="function_name", default=DEFAULT_FUNCTION)
    parser.add_argument("--prompt-bank", default=str(DEFAULT_PROMPT_BANK))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--languages", default=",".join(DEFAULT_LANGUAGES), help="Comma-separated language codes")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--retry-count", type=int, default=3)
    parser.add_argument("--min-reply-chars", type=int, default=40)
    parser.add_argument("--min-pass-rate", type=float, default=0.85)
    parser.add_argument("--min-lang-pass-rate", type=float, default=0.75)
    parser.add_argument("--core-limit", type=int, default=0, help="Run only first N core prompts per language (0=all)")
    parser.add_argument("--edge-limit", type=int, default=0, help="Run only first N edge prompts per language (0=all)")

    args = parser.parse_args()

    langs = [x.strip() for x in args.languages.split(",") if x.strip()]

    return HarnessConfig(
        region=args.region,
        function_name=args.function_name,
        prompt_bank_path=Path(args.prompt_bank),
        out_dir=Path(args.out_dir),
        languages=langs,
        max_workers=args.max_workers,
        delay_sec=args.delay,
        retry_count=args.retry_count,
        min_reply_chars=args.min_reply_chars,
        min_pass_rate=args.min_pass_rate,
        min_lang_pass_rate=args.min_lang_pass_rate,
        core_limit=args.core_limit,
        edge_limit=args.edge_limit,
    )


if __name__ == "__main__":
    config = parse_args()
    raise SystemExit(run_harness(config))
