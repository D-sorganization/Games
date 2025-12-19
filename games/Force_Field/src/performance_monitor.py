"""Performance monitoring and metrics collection for Force Field game."""

import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors game performance metrics and provides optimization insights."""

    def __init__(self, history_size: int = 60) -> None:
        """Initialize performance monitor.

        Args:
            history_size: Number of frames to keep in history for averaging
        """
        self.history_size = history_size
        self.frame_times: deque[float] = deque(maxlen=history_size)
        self.render_times: deque[float] = deque(maxlen=history_size)
        self.update_times: deque[float] = deque(maxlen=history_size)

        self.frame_start_time: float | None = None
        self.render_start_time: float | None = None
        self.update_start_time: float | None = None

        self.total_frames = 0
        self.dropped_frames = 0

        # Performance thresholds
        self.target_fps = 60.0
        self.target_frame_time = 1.0 / self.target_fps

    def start_frame(self) -> None:
        """Mark the start of a new frame."""
        self.frame_start_time = time.perf_counter()

    def end_frame(self) -> None:
        """Mark the end of the current frame and record metrics."""
        if self.frame_start_time is None:
            return

        frame_time = time.perf_counter() - self.frame_start_time
        self.frame_times.append(frame_time)
        self.total_frames += 1

        # Check for dropped frames
        if frame_time > self.target_frame_time * 1.5:
            self.dropped_frames += 1

        self.frame_start_time = None

    def start_render(self) -> None:
        """Mark the start of rendering phase."""
        self.render_start_time = time.perf_counter()

    def end_render(self) -> None:
        """Mark the end of rendering phase."""
        if self.render_start_time is None:
            return

        render_time = time.perf_counter() - self.render_start_time
        self.render_times.append(render_time)
        self.render_start_time = None

    def start_update(self) -> None:
        """Mark the start of game logic update phase."""
        self.update_start_time = time.perf_counter()

    def end_update(self) -> None:
        """Mark the end of game logic update phase."""
        if self.update_start_time is None:
            return

        update_time = time.perf_counter() - self.update_start_time
        self.update_times.append(update_time)
        self.update_start_time = None

    def get_fps(self) -> float:
        """Get current average FPS."""
        if not self.frame_times:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_frame_time_ms(self) -> float:
        """Get average frame time in milliseconds."""
        if not self.frame_times:
            return 0.0

        return (sum(self.frame_times) / len(self.frame_times)) * 1000.0

    def get_render_time_ms(self) -> float:
        """Get average render time in milliseconds."""
        if not self.render_times:
            return 0.0

        return (sum(self.render_times) / len(self.render_times)) * 1000.0

    def get_update_time_ms(self) -> float:
        """Get average update time in milliseconds."""
        if not self.update_times:
            return 0.0

        return (sum(self.update_times) / len(self.update_times)) * 1000.0

    def get_performance_stats(self) -> dict[str, float]:
        """Get comprehensive performance statistics."""
        return {
            "fps": self.get_fps(),
            "frame_time_ms": self.get_frame_time_ms(),
            "render_time_ms": self.get_render_time_ms(),
            "update_time_ms": self.get_update_time_ms(),
            "total_frames": self.total_frames,
            "dropped_frames": self.dropped_frames,
            "drop_rate": (self.dropped_frames / max(1, self.total_frames)) * 100.0,
        }

    def log_performance_summary(self) -> None:
        """Log a summary of current performance metrics."""
        stats = self.get_performance_stats()

        logger.info(
            "Performance: %.1f FPS | Frame: %.2fms | Render: %.2fms | "
            "Update: %.2fms | Drops: %.1f%%",
            stats["fps"],
            stats["frame_time_ms"],
            stats["render_time_ms"],
            stats["update_time_ms"],
            stats["drop_rate"],
        )

    def is_performance_good(self) -> bool:
        """Check if current performance meets targets."""
        return (
            self.get_fps() >= self.target_fps * 0.9  # Within 10% of target
            and self.get_frame_time_ms() <= self.target_frame_time * 1000 * 1.1
        )

    def get_optimization_suggestions(self) -> list[str]:
        """Get performance optimization suggestions based on current metrics."""
        suggestions = []
        stats = self.get_performance_stats()

        if stats["fps"] < self.target_fps * 0.8:
            suggestions.append("Consider reducing render scale or map size")

        if stats["render_time_ms"] > 10.0:
            suggestions.append("Rendering is slow - check raycasting optimization")

        if stats["update_time_ms"] > 5.0:
            suggestions.append(
                "Game logic is slow - optimize bot AI or collision detection"
            )

        if stats["drop_rate"] > 5.0:
            suggestions.append(
                "High frame drop rate - consider performance optimizations"
            )

        return suggestions
