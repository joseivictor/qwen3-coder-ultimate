"""
QWEN3-CODER ULTIMATE — Production Hardening v1.0
Battle-testing infrastructure: retry, circuit breaker, health checks, error budget.
Brings production-grade reliability to all API and tool calls.
"""

import functools
import logging
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


# ── RETRY POLICY ─────────────────────────────────────────────────────────────

@dataclass
class RetryPolicy:
    max_attempts:   int   = 3
    base_delay_s:   float = 1.0
    max_delay_s:    float = 30.0
    backoff_factor: float = 2.0
    jitter:         bool  = True
    retryable_exceptions: tuple = (Exception,)
    retryable_status_codes: set = field(default_factory=lambda: {429, 500, 502, 503, 504})

    def delay_for(self, attempt: int) -> float:
        import random
        delay = min(self.base_delay_s * (self.backoff_factor ** attempt), self.max_delay_s)
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)
        return delay


API_RETRY    = RetryPolicy(max_attempts=3, base_delay_s=2.0, max_delay_s=30.0)
TOOL_RETRY   = RetryPolicy(max_attempts=2, base_delay_s=0.5, max_delay_s=5.0)
STRICT_RETRY = RetryPolicy(max_attempts=1)  # no retry for destructive ops


def retry(policy: RetryPolicy = None):
    """Decorator: retry with exponential backoff."""
    if policy is None:
        policy = API_RETRY

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(policy.max_attempts):
                try:
                    return fn(*args, **kwargs)
                except policy.retryable_exceptions as e:
                    last_exc = e
                    if attempt == policy.max_attempts - 1:
                        break
                    delay = policy.delay_for(attempt)
                    logger.warning(f"retry {attempt+1}/{policy.max_attempts} for {fn.__name__}: {e} — sleeping {delay:.1f}s")
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


def retry_call(fn: Callable, args=(), kwargs=None, policy: RetryPolicy = None) -> Any:
    """Call fn with retry. No decorator needed."""
    policy  = policy or API_RETRY
    kwargs  = kwargs or {}
    last_exc = None
    for attempt in range(policy.max_attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt == policy.max_attempts - 1:
                break
            delay = policy.delay_for(attempt)
            logger.warning(f"retry_call {fn.__name__} attempt {attempt+1}: {e}")
            time.sleep(delay)
    raise last_exc


# ── CIRCUIT BREAKER ───────────────────────────────────────────────────────────

class CircuitState(str, Enum):
    CLOSED   = "closed"    # normal: requests pass through
    OPEN     = "open"      # tripped: reject all requests fast
    HALF_OPEN= "half_open" # testing: allow one request to see if healed


class CircuitBreaker:
    """
    Classic circuit breaker pattern.
    CLOSED → OPEN after failure_threshold failures.
    OPEN → HALF_OPEN after recovery_timeout.
    HALF_OPEN → CLOSED on success, OPEN on failure.
    """

    def __init__(
        self,
        name:              str   = "default",
        failure_threshold: int   = 5,
        recovery_timeout:  float = 60.0,
        success_threshold: int   = 2,
    ):
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold
        self._state            = CircuitState.CLOSED
        self._failures         = 0
        self._successes        = 0
        self._last_failure_ts  = 0.0
        self._lock             = threading.Lock()
        self._stats = {"total": 0, "failures": 0, "rejected": 0, "recoveries": 0}

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_ts >= self.recovery_timeout:
                    self._state   = CircuitState.HALF_OPEN
                    self._successes = 0
            return self._state

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        state = self.state
        self._stats["total"] += 1

        if state == CircuitState.OPEN:
            self._stats["rejected"] += 1
            raise RuntimeError(f"Circuit breaker '{self.name}' is OPEN — failing fast")

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._successes += 1
                if self._successes >= self.success_threshold:
                    self._state    = CircuitState.CLOSED
                    self._failures = 0
                    self._stats["recoveries"] += 1
                    logger.info(f"Circuit '{self.name}' CLOSED (recovered)")
            else:
                self._failures = max(0, self._failures - 1)

    def _on_failure(self):
        with self._lock:
            self._failures       += 1
            self._stats["failures"] += 1
            self._last_failure_ts = time.time()
            if self._failures >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    logger.error(f"Circuit '{self.name}' OPENED after {self._failures} failures")
                self._state = CircuitState.OPEN

    def reset(self):
        with self._lock:
            self._state    = CircuitState.CLOSED
            self._failures = 0
            self._successes = 0

    def stats(self) -> str:
        return (
            f"Circuit[{self.name}] {self.state.value}: "
            f"fails={self._stats['failures']} rejected={self._stats['rejected']} "
            f"recovered={self._stats['recoveries']}"
        )


# ── SAFE EXECUTE ─────────────────────────────────────────────────────────────

def safe_execute(fn: Callable, *args, fallback=None, log_exc: bool = True, **kwargs) -> Any:
    """Call fn safely. Return fallback on any exception."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        if log_exc:
            logger.warning(f"safe_execute: {fn.__name__} failed: {e}")
        return fallback


# ── ERROR BUDGET ─────────────────────────────────────────────────────────────

class ErrorBudget:
    """
    SRE-style error budget. Tracks errors over a sliding window.
    Burns down from 100% as errors occur. Alerts when low.
    """

    def __init__(self, window_s: float = 300.0, budget_pct: float = 5.0):
        self._window_s   = window_s       # 5 min default
        self._budget_pct = budget_pct     # 5% error rate allowed
        self._calls: list[tuple[float, bool]] = []   # (ts, is_error)
        self._lock = threading.Lock()

    def record(self, success: bool):
        with self._lock:
            now = time.time()
            self._calls.append((now, not success))
            cutoff = now - self._window_s
            self._calls = [(ts, e) for ts, e in self._calls if ts > cutoff]

    def error_rate(self) -> float:
        with self._lock:
            if not self._calls:
                return 0.0
            errors = sum(1 for _, e in self._calls if e)
            return errors / len(self._calls) * 100

    def budget_remaining(self) -> float:
        return max(0.0, self._budget_pct - self.error_rate())

    def is_exhausted(self) -> bool:
        return self.budget_remaining() <= 0

    def stats(self) -> str:
        rate = self.error_rate()
        remaining = self.budget_remaining()
        total = len(self._calls)
        return (
            f"ErrorBudget: {rate:.1f}% error rate | "
            f"{remaining:.1f}% remaining | "
            f"{total} calls in window"
        )


# ── HEALTH CHECK ─────────────────────────────────────────────────────────────

@dataclass
class HealthStatus:
    name:      str
    healthy:   bool
    latency_ms:float
    message:   str = ""
    ts:        float = field(default_factory=time.time)


class HealthChecker:
    """Periodically checks API endpoints and tracks health."""

    def __init__(self, check_interval_s: float = 60.0):
        self._checks: dict[str, Callable] = {}
        self._results: dict[str, HealthStatus] = {}
        self._interval = check_interval_s
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def register(self, name: str, check_fn: Callable):
        self._checks[name] = check_fn

    def check_all(self) -> dict[str, HealthStatus]:
        for name, fn in self._checks.items():
            start = time.time()
            try:
                fn()
                latency = (time.time() - start) * 1000
                self._results[name] = HealthStatus(name=name, healthy=True, latency_ms=latency)
            except Exception as e:
                latency = (time.time() - start) * 1000
                self._results[name] = HealthStatus(name=name, healthy=False, latency_ms=latency, message=str(e))
        return self._results

    def start_background(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            self.check_all()
            time.sleep(self._interval)

    def stop(self):
        self._running = False

    def status(self) -> str:
        if not self._results:
            return "HealthChecker: no checks run yet"
        lines = ["Health:"]
        for name, s in self._results.items():
            icon = "OK" if s.healthy else "FAIL"
            lines.append(f"  [{icon}] {name} {s.latency_ms:.0f}ms {s.message}")
        return "\n".join(lines)

    def all_healthy(self) -> bool:
        return all(s.healthy for s in self._results.values())


# ── RATE LIMITER ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Token bucket rate limiter — prevents API rate limit errors proactively."""

    def __init__(self, calls_per_minute: int = 60):
        self._rate     = calls_per_minute / 60.0  # calls per second
        self._tokens   = float(calls_per_minute)
        self._max      = float(calls_per_minute)
        self._last_refill = time.time()
        self._lock     = threading.Lock()
        self._waits    = 0

    def acquire(self, cost: float = 1.0) -> float:
        """Block until token available. Returns wait time in seconds."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_refill
            self._tokens = min(self._max, self._tokens + elapsed * self._rate)
            self._last_refill = now

            if self._tokens >= cost:
                self._tokens -= cost
                return 0.0

            wait = (cost - self._tokens) / self._rate
            self._tokens = 0
            self._waits += 1

        time.sleep(wait)
        return wait

    def stats(self) -> str:
        return f"RateLimiter: {self._tokens:.1f} tokens | {self._waits} waits"


# ── HARDENED WRAPPER ─────────────────────────────────────────────────────────

class HardenedAPIClient:
    """
    Wraps any OpenAI-compatible client with:
    - Retry with exponential backoff
    - Circuit breaker
    - Rate limiter
    - Error budget tracking
    - Health monitoring
    """

    def __init__(
        self,
        client,
        name:              str = "api",
        calls_per_minute:  int = 60,
        failure_threshold: int = 5,
        retry_policy: RetryPolicy = None,
    ):
        self._client   = client
        self._name     = name
        self._circuit  = CircuitBreaker(name=name, failure_threshold=failure_threshold)
        self._limiter  = RateLimiter(calls_per_minute=calls_per_minute)
        self._budget   = ErrorBudget()
        self._policy   = retry_policy or API_RETRY

    def create(self, **kwargs) -> Any:
        """Hardened chat.completions.create call."""
        self._limiter.acquire()

        def _call():
            return self._client.chat.completions.create(**kwargs)

        try:
            result = self._circuit.call(retry_call, _call, policy=self._policy)
            self._budget.record(success=True)
            return result
        except Exception as e:
            self._budget.record(success=False)
            raise

    def stats(self) -> str:
        return (
            f"HardenedAPI[{self._name}]: "
            f"{self._circuit.stats()} | "
            f"{self._budget.stats()} | "
            f"{self._limiter.stats()}"
        )

    def health(self) -> bool:
        return (
            self._circuit.state != CircuitState.OPEN and
            not self._budget.is_exhausted()
        )
