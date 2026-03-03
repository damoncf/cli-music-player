"""Tests for error handling."""
import pytest
import asyncio
from datetime import datetime

from cmp.utils.error_handling import (
    ErrorHandler,
    ErrorInfo,
    ErrorCategory,
    ErrorSeverity,
    CircuitBreaker,
    RetryPolicy,
    with_retry,
    with_circuit_breaker,
)


@pytest.fixture
def error_handler():
    """Create an ErrorHandler instance for testing."""
    return ErrorHandler()


@pytest.fixture
def circuit_breaker():
    """Create a CircuitBreaker instance for testing."""
    return CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)


class TestErrorInfo:
    """Tests for ErrorInfo."""
    
    def test_create_error_info(self):
        """Test creating error info."""
        exc = ValueError("Test error")
        error = ErrorInfo(
            category=ErrorCategory.AUDIO,
            severity=ErrorSeverity.HIGH,
            message="Test error message",
            exception=exc,
        )
        
        assert error.category == ErrorCategory.AUDIO
        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Test error message"
        assert error.exception == exc
        assert isinstance(error.timestamp, datetime)
    
    def test_to_dict(self):
        """Test error info serialization."""
        error = ErrorInfo(
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.MEDIUM,
            message="File not found",
            context={"path": "/test/file.mp3"},
        )
        
        data = error.to_dict()
        
        assert data["category"] == "file"
        assert data["severity"] == "medium"
        assert data["message"] == "File not found"
        assert data["context"]["path"] == "/test/file.mp3"


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state."""
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.can_execute() is True
    
    def test_record_success(self, circuit_breaker):
        """Test recording success."""
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_success()
        
        assert circuit_breaker.state == "closed"
    
    def test_open_after_failures(self, circuit_breaker):
        """Test circuit opens after threshold failures."""
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        assert circuit_breaker.state == "closed"
        
        circuit_breaker.record_failure()
        assert circuit_breaker.state == "open"
        assert circuit_breaker.can_execute() is False
    
    def test_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions to half-open after timeout."""
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        
        assert circuit_breaker.state == "open"
        
        # Wait for recovery timeout
        import time
        time.sleep(1.1)
        
        assert circuit_breaker.state == "half-open"
        assert circuit_breaker.can_execute() is True
    
    def test_reset(self, circuit_breaker):
        """Test circuit breaker reset."""
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        
        assert circuit_breaker.state == "open"
        
        circuit_breaker.reset()
        
        assert circuit_breaker.state == "closed"
        assert circuit_breaker._failure_count == 0


class TestRetryPolicy:
    """Tests for RetryPolicy."""
    
    def test_get_delay(self):
        """Test delay calculation."""
        policy = RetryPolicy(
            max_retries=3,
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
    
    def test_max_delay(self):
        """Test max delay cap."""
        policy = RetryPolicy(
            max_delay=5.0,
            exponential_base=10.0,
            jitter=False,
        )
        
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 5.0  # capped
        assert policy.get_delay(2) == 5.0  # capped


class TestErrorHandler:
    """Tests for ErrorHandler."""
    
    def test_handle_error(self, error_handler):
        """Test error handling."""
        exc = ValueError("Test error")
        error = error_handler.handle_error(
            exc,
            category=ErrorCategory.AUDIO,
            severity=ErrorSeverity.HIGH,
        )
        
        assert error.category == ErrorCategory.AUDIO
        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Test error"
    
    def test_error_history(self, error_handler):
        """Test error history."""
        error_handler.handle_error(ValueError("Error 1"), category=ErrorCategory.AUDIO)
        error_handler.handle_error(ValueError("Error 2"), category=ErrorCategory.FILE)
        error_handler.handle_error(ValueError("Error 3"), category=ErrorCategory.AUDIO)
        
        errors = error_handler.get_errors()
        assert len(errors) == 3
        
        audio_errors = error_handler.get_errors(category=ErrorCategory.AUDIO)
        assert len(audio_errors) == 2
    
    def test_recovery_handler(self, error_handler):
        """Test recovery handler."""
        recovery_called = []
        
        def recovery_handler(error):
            recovery_called.append(error)
            return True
        
        error_handler.register_recovery_handler(ErrorCategory.AUDIO, recovery_handler)
        
        error = error_handler.handle_error(
            ValueError("Test"),
            category=ErrorCategory.AUDIO,
            attempt_recovery=True,
        )
        
        assert len(recovery_called) == 1
        assert error.recovery_attempted is True
        assert error.recovery_successful is True
    
    def test_error_callback(self, error_handler):
        """Test error callback."""
        callbacks = []
        
        def callback(error):
            callbacks.append(error)
        
        error_handler.register_error_callback(callback)
        
        error_handler.handle_error(ValueError("Test"))
        
        assert len(callbacks) == 1
    
    def test_circuit_breaker_registration(self, error_handler):
        """Test circuit breaker registration."""
        cb = error_handler.register_circuit_breaker("test_cb", failure_threshold=5)
        
        assert cb.name == "test_cb"
        assert cb.failure_threshold == 5
        
        retrieved = error_handler.get_circuit_breaker("test_cb")
        assert retrieved == cb


class TestDecorators:
    """Tests for error handling decorators."""
    
    @pytest.mark.asyncio
    async def test_with_retry_async(self):
        """Test retry decorator with async function."""
        attempts = []
        
        @with_retry(policy=RetryPolicy(max_retries=2, base_delay=0.1))
        async def failing_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = await failing_func()
        
        assert result == "success"
        assert len(attempts) == 3
    
    def test_with_retry_sync(self):
        """Test retry decorator with sync function."""
        attempts = []
        
        @with_retry(policy=RetryPolicy(max_retries=2, base_delay=0.1))
        def failing_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = failing_func()
        
        assert result == "success"
        assert len(attempts) == 3
    
    @pytest.mark.asyncio
    async def test_with_circuit_breaker_async(self):
        """Test circuit breaker decorator with async function."""
        from cmp.utils.error_handling import error_handler
        
        # Register a circuit breaker with low threshold
        cb = error_handler.register_circuit_breaker("test_cb_async", failure_threshold=2)
        
        call_count = [0]
        
        @with_circuit_breaker("test_cb_async")
        async def protected_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Failure")
            return "success"
        
        # First two calls fail and open the circuit
        with pytest.raises(ValueError):
            await protected_func()
        with pytest.raises(ValueError):
            await protected_func()
        
        # Circuit should be open now
        with pytest.raises(Exception, match="Circuit breaker"):
            await protected_func()
    
    def test_with_circuit_breaker_sync(self):
        """Test circuit breaker decorator with sync function."""
        from cmp.utils.error_handling import error_handler
        
        # Register a circuit breaker with low threshold
        cb = error_handler.register_circuit_breaker("test_cb_sync_new", failure_threshold=2)
        
        call_count = [0]
        
        @with_circuit_breaker("test_cb_sync_new")
        def protected_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Failure")
            return "success"
        
        # First two calls fail and open the circuit
        with pytest.raises(ValueError):
            protected_func()
        with pytest.raises(ValueError):
            protected_func()
        
        # Circuit should be open now
        with pytest.raises(Exception, match="Circuit breaker"):
            protected_func()
