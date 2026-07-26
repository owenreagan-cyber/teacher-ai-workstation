from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable

NO_RETRY_STATUS_CODES = {401, 403}
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class RateLimitError(RuntimeError):
    pass


@dataclass
class RetryPolicy:
    max_attempts: int = 5
    base_delay: float = 0.5
    max_delay: float = 30.0
    jitter_seed: int | None = None

    def delay_for_attempt(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None:
            return min(max(retry_after, 0.0), self.max_delay)
        base = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        rng = random.Random(self.jitter_seed) if self.jitter_seed is not None else random
        jitter = rng.uniform(0, base * 0.1)
        return min(base + jitter, self.max_delay)


def classify_response(status_code: int) -> str:
    """401/403 are never retried. 429/5xx are retryable (bounded). Anything
    else is treated as terminal (no-retry) -- including 2xx success."""
    if status_code in NO_RETRY_STATUS_CODES:
        return "no-retry"
    if status_code in RETRYABLE_STATUS_CODES:
        return "retryable"
    return "no-retry"


def parse_retry_after(headers: dict[str, str]) -> float | None:
    for key, value in headers.items():
        if key.lower() == "retry-after":
            try:
                return float(value)
            except ValueError:
                return None
    return None


def execute_with_retry(
    call: Callable[[], tuple[int, dict[str, str]]],
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] | None = None,
) -> tuple[int, dict[str, str], int]:
    """call() -> (status_code, headers). Never retries 401/403. Retries
    429/5xx up to policy.max_attempts with capped, bounded backoff, honoring
    Retry-After when present. Returns (final_status, final_headers,
    attempts_made) so callers/tests can verify the retry count directly."""
    policy = policy or RetryPolicy()
    sleep = sleep or (lambda _seconds: None)
    attempt = 0
    while True:
        attempt += 1
        status_code, headers = call()
        if classify_response(status_code) != "retryable" or attempt >= policy.max_attempts:
            return status_code, headers, attempt
        retry_after = parse_retry_after(headers)
        sleep(policy.delay_for_attempt(attempt, retry_after))
