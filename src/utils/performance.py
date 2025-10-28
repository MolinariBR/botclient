import logging
import time
import psutil
import threading
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring utility for tracking execution times and system resources"""

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.errors: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    @contextmanager
    def measure(self, operation: str):
        """Context manager to measure execution time of a block of code"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory

            with self._lock:
                self.execution_times[operation].append(execution_time)
                self.call_counts[operation] += 1

            logger.info(
                f"Performance: {operation} took {execution_time:.3f}s, "
                f"memory delta: {memory_delta:.2f}MB"
            )

    def measure_function(self, operation: Optional[str] = None):
        """Decorator to measure execution time of a function"""
        def decorator(func: Callable) -> Callable:
            op_name = operation or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                with self.measure(op_name):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        with self._lock:
                            self.errors[op_name] += 1
                        raise

            return wrapper
        return decorator

    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get performance statistics for an operation"""
        with self._lock:
            times = list(self.execution_times[operation])
            if not times:
                return {
                    "calls": 0,
                    "errors": self.errors[operation],
                    "avg_time": 0,
                    "min_time": 0,
                    "max_time": 0,
                    "median_time": 0,
                    "p95_time": 0,
                    "p99_time": 0
                }

            return {
                "calls": self.call_counts[operation],
                "errors": self.errors[operation],
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "p95_time": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                "p99_time": statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times)
            }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for all operations"""
        operations = set(self.execution_times.keys()) | set(self.call_counts.keys()) | set(self.errors.keys())
        return {op: self.get_stats(op) for op in operations}

    def log_summary(self):
        """Log a summary of all performance statistics"""
        stats = self.get_all_stats()

        logger.info("=== Performance Summary ===")
        for operation, op_stats in sorted(stats.items()):
            if op_stats["calls"] > 0:
                error_rate = (op_stats["errors"] / op_stats["calls"]) * 100 if op_stats["calls"] > 0 else 0
                logger.info(
                    f"{operation}: {op_stats['calls']} calls, "
                    f"avg {op_stats['avg_time']:.3f}s, "
                    f"p95 {op_stats['p95_time']:.3f}s, "
                    f"errors {op_stats['errors']} ({error_rate:.1f}%)"
                )

    def reset(self):
        """Reset all performance data"""
        with self._lock:
            self.execution_times.clear()
            self.call_counts.clear()
            self.errors.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def measure_performance(operation: Optional[str] = None):
    """Decorator to measure function performance"""
    return performance_monitor.measure_function(operation)


@contextmanager
def measure_block(operation: str):
    """Context manager to measure a block of code"""
    with performance_monitor.measure(operation):
        yield