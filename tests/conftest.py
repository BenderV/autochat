import pytest
import json
import re
from difflib import unified_diff


DIFFS = []


def replace_file_paths_with_XXX(content: str) -> str:
    print("replace_file_paths_with_XXX")
    """Replace file paths with XXX for consistent diffs across environments"""
    if "Traceback" in content:
        # Replace any file path in quotes with XXX/filename.py
        content = re.sub(r"File \\\".*?([^/]+\.py)\\\"", r"File \"XXX/\1\"", content)
        # Replace line number with xxx
        content = re.sub(r"line \d+", r"line xxx", content)
    return content


def request_body_diff_matcher(r1, r2):
    """Matcher that compares requests with the same sequence index"""
    # Decode and pretty-format the bodies
    body1 = json.loads(r1.body.decode("utf-8"))
    body1_dump = json.dumps(body1, indent=2)
    body2 = json.loads(r2.body.decode("utf-8"))
    body2_dump = json.dumps(body2, indent=2)

    # body1.messages length != body2.messages length; we should not compare them
    if len(body1.get("messages", [])) != len(body2.get("messages", [])):
        return False

    body1_dump = replace_file_paths_with_XXX(body1_dump)
    body2_dump = replace_file_paths_with_XXX(body2_dump)

    # If bodies are different, show the diff
    if body1_dump != body2_dump:
        diff = unified_diff(
            body1_dump.splitlines(keepends=True),
            body2_dump.splitlines(keepends=True),
            n=3,
        )
        # We store the diff in the DIFFS list to show it in the terminal summary
        DIFFS.append(
            "\nRequest bodies differ! (- cassette, + current):\n" + "".join(diff)
        )
        # Even though the bodies are different, we still want to continue the test
        return True

    return True


def before_record_response(response):
    # Remove headers we don't want to record
    headers_to_filter = {
        "date",
        "server",
        "x-request-id",
        "x-ratelimit-limit-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-requests",
        "x-ratelimit-reset-tokens",
        "anthropic-ratelimit-input-tokens-limit",
        "anthropic-ratelimit-input-tokens-remaining",
        "anthropic-ratelimit-input-tokens-reset",
        "anthropic-ratelimit-output-tokens-limit",
        "anthropic-ratelimit-output-tokens-remaining",
        "anthropic-ratelimit-output-tokens-reset",
        "anthropic-ratelimit-requests-limit",
        "anthropic-ratelimit-requests-remaining",
        "anthropic-ratelimit-requests-reset",
        "anthropic-ratelimit-tokens-limit",
        "anthropic-ratelimit-tokens-remaining",
        "anthropic-ratelimit-tokens-reset",
        "openai-organization",
        "openai-processing-ms",
        "openai-version",
        "set-cookie",
        "cf-cache-status",
        "cf-ray",
    }

    response["headers"] = {
        k: v
        for k, v in response["headers"].items()
        if k.lower() not in headers_to_filter
    }
    return response


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [
            ("Authorization", None),
            ("api-key", None),
            ("x-api-key", None),
            ("accept", None),
            ("accept-encoding", None),
            ("connection", None),
            ("content-length", None),
            ("user-agent", None),
            ("x-stainless-arch", None),
            ("x-stainless-async", None),
            ("x-stainless-lang", None),
            ("x-stainless-os", None),
            ("x-stainless-package-version", None),
            ("x-stainless-retry-count", None),
            ("x-stainless-runtime", None),
            ("x-stainless-runtime-version", None),
            ("cookie", None),
        ],
        "before_record_response": before_record_response,
        "record_mode": "once",
        "match_on": [
            "method",
            "scheme",
            "host",
            "port",
            "path",
            "query",
            "custom_body_diff",
        ],
    }


def pytest_recording_configure(config, vcr):
    vcr.register_matcher("custom_body_diff", request_body_diff_matcher)


@pytest.fixture(scope="session", autouse=True)
def check_diffs_at_end(request):
    yield
    if DIFFS:
        print("\nDifferences found in the following tests:")
        for diff in DIFFS:
            print(diff)
        pytest.fail("Request body differences found in tests", pytrace=False)
