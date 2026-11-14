"""Smoke-test the running Persian Site Assistant API.

Checks service health/readiness, sends a known-answer question, a product
recommendation question and an unsupported question, then saves full UTF-8
responses for manual quality review. This expects a running API and configured LLM.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("data/test_output/chat_smoke_test.json")

TEST_CASES = [
    {
        "name": "supported_company_services",
        "question": "شرکت چه خدماتی ارائه می‌دهد؟",
        "expect_sources": True,
        "manual_review": False,
    },
    {
        "name": "product_recommendation_store_150",
        "question": (
            "ما یک فروشگاه اینترنتی با حدود ۱۵۰ محصول داریم. "
            "سفارش‌ها را دستی ثبت می‌کنیم و موجودی همیشه دقیق نیست. "
            "بودجه نمایشی ما ۵۰ تا ۶۵ میلیون تومان است. "
            "کدام محصول یا ترکیب محصولات مناسب‌تر است و چرا؟"
        ),
        "expect_sources": True,
        "manual_review": True,
        "manual_review_note": (
            "Check that بازارینو is the main fit, انباربان is only an optional "
            "inventory complement, and any quoted price is labelled illustrative."
        ),
    },
    {
        "name": "unsupported_bank_account",
        "question": "شماره حساب بانکی مدیرعامل چیست؟",
        "expect_sources": False,
        "manual_review": True,
        "manual_review_note": "Check that the assistant does not invent sensitive or missing information.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the running FastAPI application.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="HTTP timeout in seconds (default: 180; local models can be slow).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"UTF-8 JSON report path (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()


def validate_chat_response(
    status_code: int,
    payload: Any,
    *,
    expect_sources: bool,
) -> list[str]:
    """Return response-contract errors; an empty list means the shape is valid."""
    errors: list[str] = []

    if status_code != 200:
        return [f"Expected HTTP 200, received HTTP {status_code}."]

    if not isinstance(payload, dict):
        return ["Response body is not a JSON object."]

    answer = payload.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        errors.append("Response has no non-empty string 'answer'.")

    sources = payload.get("sources")
    if not isinstance(sources, list):
        errors.append("Response field 'sources' must be a list.")
    else:
        if expect_sources and not sources:
            errors.append("Supported question returned no sources.")

        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"Source at position {index} is not an object.")
                continue
            if not isinstance(source.get("source_id"), str):
                errors.append(f"Source at position {index} has no source_id.")
            if not isinstance(source.get("title"), str):
                errors.append(f"Source at position {index} has no title.")

    return errors


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    report: dict[str, Any] = {
        "created_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "checks": [],
        "chat_tests": [],
    }

    failures = 0

    try:
        with httpx.Client(timeout=args.timeout) as client:
            # Verify that the process is alive and the RAG service is ready.
            for endpoint in ("/health", "/ready"):
                check: dict[str, Any] = {"endpoint": endpoint}
                started = time.perf_counter()

                try:
                    response = client.get(f"{base_url}{endpoint}")
                    check["status_code"] = response.status_code
                    try:
                        check["body"] = response.json()
                    except ValueError:
                        check["body_text"] = response.text

                    check["passed"] = response.status_code == 200
                    check["elapsed_ms"] = round(
                        (time.perf_counter() - started) * 1000, 2
                    )
                except httpx.HTTPError as exc:
                    check["passed"] = False
                    check["error"] = str(exc)

                report["checks"].append(check)
                if not check["passed"]:
                    failures += 1

            if all(check["passed"] for check in report["checks"]):
                # Exercise one known-answer case and one abstention case.
                for case in TEST_CASES:
                    result: dict[str, Any] = {
                        "name": case["name"],
                        "question": case["question"],
                        "manual_review": case["manual_review"],
                        "manual_review_note": case.get("manual_review_note"),
                    }
                    started = time.perf_counter()

                    try:
                        response = client.post(
                            f"{base_url}/api/v1/chat",
                            json={"message": case["question"]},
                        )
                        result["status_code"] = response.status_code
                        result["elapsed_ms"] = round(
                            (time.perf_counter() - started) * 1000, 2
                        )

                        try:
                            payload = response.json()
                            result["response"] = payload
                            errors = validate_chat_response(
                                response.status_code,
                                payload,
                                expect_sources=case["expect_sources"],
                            )
                        except ValueError:
                            result["response_text"] = response.text
                            errors = ["Response body is not valid JSON."]

                        result["errors"] = errors
                        result["passed"] = not errors

                    except httpx.HTTPError as exc:
                        result["passed"] = False
                        result["errors"] = [str(exc)]

                    report["chat_tests"].append(result)
                    if not result["passed"]:
                        failures += 1
            else:
                print("Skipping chat requests because health/readiness failed.")

    except httpx.HTTPError as exc:
        report["fatal_error"] = str(exc)
        failures += 1

    output_path = args.output
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"API base URL: {base_url}")
    for check in report["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"{status}: {check['endpoint']}")

    for result in report["chat_tests"]:
        status = "PASS" if result["passed"] else "FAIL"
        source_count = len(result.get("response", {}).get("sources", []))
        elapsed = result.get("elapsed_ms", "n/a")
        print(
            f"{status}: {result['name']} "
            f"(HTTP {result.get('status_code', 'n/a')}, "
            f"{source_count} sources, {elapsed} ms)"
        )
        if result["manual_review"]:
            print("  Manual review required: check that the answer does not invent data.")

        for error in result.get("errors", []):
            print(f"  - {error}")

    print(f"\nFull UTF-8 response report: {output_path}")
    if failures:
        print(f"Smoke test finished with {failures} failure(s).")
        return 1

    print("HTTP and response-contract checks passed.")
    print("Review the saved Persian answers manually, especially the abstention case.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
