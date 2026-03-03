"""Error handling and recovery mechanisms."""
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import traceback
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories."""
    AUDIO = "audio"
    FILE = "file"
    PLAYLIST = "playlist"
    CONFIG = "config"
    NETWORK = "network"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Error information."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "exception": str(self.exception) if self.exception else None,
            "traceback": self.traceback,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
        }


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_requests: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = "closed"  # closed, open, half-open
        self._half_open_successes = 0
    
    @property
    def state(self) -> str:
        """Get current state."""
        # Check if we should transition from open to half-open
        if self._state == "open" and self._last_failure_time:
            elapsed = (datetime.now() - self._last_failure_time).total_seconds()
            if elapsed >= self.recovery_timeout:
                self._state = "half-open"
                self._half_open_successes = 0
        
        return self._state
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        state = self.state
        return state in ("closed", "half-open")
    
    def record_success(self):
        """Record successful execution."""
        if self._state == "half-open":
            self._half_open_successes += 1
            if self._half_open_successes >= self.half_open_requests:
                self._state = "closed"
                self._failure_count = 0
                logger.info(f"Circuit breaker '{self.name}' closed after recovery")
        elif self._state == "closed":
            self._failure_count = 0
    
    def record_failure(self):
        """Record failed execution."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._state == "half-open":
            self._state = "open"
            logger.warning(f"Circuit breaker '{self.name}' reopened after failure in half-open")
        elif self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self._failure_count} failures"
            )
    
    def reset(self):
        """Reset the circuit breaker."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"
        self._half_open_successes = 0


class RetryPolicy:
    """Retry policy with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for given attempt."""
        import random
        
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return delay


class ErrorHandler:
    """Centralized error handling and recovery."""
    
    def __init__(self):
        self._errors: list[ErrorInfo] = []
        self._max_errors = 100
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._recovery_handlers: dict[ErrorCategory, Callable] = {}
        self._error_callbacks: list[Callable[[ErrorInfo], None]] = []
    
    def register_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Register a circuit breaker."""
        cb = CircuitBreaker(name, **kwargs)
        self._circuit_breakers[name] = cb
        return cb
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self._circuit_breakers.get(name)
    
    def register_recovery_handler(
        self,
        category: ErrorCategory,
        handler: Callable[[ErrorInfo], bool]
    ):
        """Register a recovery handler for an error category."""
        self._recovery_handlers[category] = handler
    
    def register_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """Register a callback for error events."""
        self._error_callbacks.append(callback)
    
    def handle_error(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: dict = None,
        attempt_recovery: bool = True,
    ) -> ErrorInfo:
        """Handle an error with optional recovery."""
        error = ErrorInfo(
            category=category,
            severity=severity,
            message=str(exception),
            exception=exception,
            traceback=traceback.format_exc(),
            context=context or {},
        )
        
        # Log the error
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(severity, logging.ERROR)
        
        logger.log(log_level, f"[{category.value}] {exception}")
        
        # Attempt recovery
        if attempt_recovery and category in self._recovery_handlers:
            try:
                error.recovery_attempted = True
                error.recovery_successful = self._recovery_handlers[category](error)
                if error.recovery_successful:
                    logger.info(f"Recovery successful for {category.value} error")
            except Exception as e:
                logger.error(f"Recovery failed: {e}")
        
        # Store error
        self._errors.append(error)
        if len(self._errors) > self._max_errors:
            self._errors.pop(0)
        
        # Notify callbacks
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
        
        return error
    
    def get_errors(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 10,
    ) -> list[ErrorInfo]:
        """Get error history."""
        errors = self._errors
        
        if category:
            errors = [e for e in errors if e.category == category]
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        return errors[-limit:]
    
    def clear_errors(self):
        """Clear error history."""
        self._errors.clear()


# Global error handler instance
error_handler = ErrorHandler()


# Decorators for error handling
def with_retry(
    policy: RetryPolicy = None,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    on_failure: Optional[Callable] = None,
):
    """Decorator to retry a function on failure."""
    policy = policy or RetryPolicy()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(policy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{policy.max_retries} for {func.__name__} "
                            f"after {delay:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay)
            
            # All retries failed
            error_handler.handle_error(
                last_exception,
                category=category,
                attempt_recovery=False,
            )
            if on_failure:
                return on_failure(last_exception)
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{policy.max_retries} for {func.__name__} "
                            f"after {delay:.1f}s: {e}"
                        )
                        import time
                        time.sleep(delay)
            
            # All retries failed
            error_handler.handle_error(
                last_exception,
                category=category,
                attempt_recovery=False,
            )
            if on_failure:
                return on_failure(last_exception)
            raise last_exception
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_circuit_breaker(name: str, fallback: Optional[Callable] = None):
    """Decorator to protect a function with a circuit breaker."""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cb = error_handler.get_circuit_breaker(name)
            if not cb:
                cb = error_handler.register_circuit_breaker(name)
            
            if not cb.can_execute():
                logger.warning(f"Circuit breaker '{name}' is open, using fallback")
                if fallback:
                    return await fallback(*args, **kwargs)
                raise Exception(f"Circuit breaker '{name}' is open")
            
            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cb = error_handler.get_circuit_breaker(name)
            if not cb:
                cb = error_handler.register_circuit_breaker(name)
            
            if not cb.can_execute():
                logger.warning(f"Circuit breaker '{name}' is open, using fallback")
                if fallback:
                    return fallback(*args, **kwargs)
                raise Exception(f"Circuit breaker '{name}' is open")
            
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
