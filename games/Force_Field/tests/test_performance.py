"""Tests for performance monitoring functionality."""

import time
import unittest

from games.Force_Field.src.performance_monitor import PerformanceMonitor


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(history_size=10)

    def test_frame_timing(self) -> None:
        """Test frame timing measurement."""
        self.monitor.start_frame()
        time.sleep(0.01)  # Simulate 10ms frame
        self.monitor.end_frame()

        self.assertEqual(len(self.monitor.frame_times), 1)
        self.assertGreater(self.monitor.frame_times[0], 0.009)  # At least 9ms
        self.assertLess(self.monitor.frame_times[0], 0.02)  # Less than 20ms

    def test_fps_calculation(self) -> None:
        """Test FPS calculation."""
        # Simulate several frames
        for _ in range(5):
            self.monitor.start_frame()
            time.sleep(0.01)  # 10ms per frame = 100 FPS theoretical
            self.monitor.end_frame()

        fps = self.monitor.get_fps()
        self.assertGreater(fps, 50)  # Should be at least 50 FPS
        self.assertLess(fps, 150)  # Should be less than 150 FPS

    def test_render_timing(self) -> None:
        """Test render timing measurement."""
        self.monitor.start_render()
        time.sleep(0.005)  # Simulate 5ms render
        self.monitor.end_render()

        self.assertEqual(len(self.monitor.render_times), 1)
        render_time_ms = self.monitor.get_render_time_ms()
        self.assertGreater(render_time_ms, 4)  # At least 4ms
        self.assertLess(render_time_ms, 10)  # Less than 10ms

    def test_update_timing(self) -> None:
        """Test update timing measurement."""
        self.monitor.start_update()
        time.sleep(0.002)  # Simulate 2ms update
        self.monitor.end_update()

        self.assertEqual(len(self.monitor.update_times), 1)
        update_time_ms = self.monitor.get_update_time_ms()
        self.assertGreater(update_time_ms, 1)  # At least 1ms
        self.assertLess(update_time_ms, 5)  # Less than 5ms

    def test_performance_stats(self) -> None:
        """Test comprehensive performance statistics."""
        # Simulate a few frames with different timings
        for _ in range(3):
            self.monitor.start_frame()
            self.monitor.start_render()
            time.sleep(0.003)  # 3ms render
            self.monitor.end_render()

            self.monitor.start_update()
            time.sleep(0.002)  # 2ms update
            self.monitor.end_update()

            time.sleep(0.005)  # Additional frame time
            self.monitor.end_frame()

        stats = self.monitor.get_performance_stats()

        # Verify all expected keys are present
        expected_keys = [
            "fps",
            "frame_time_ms",
            "render_time_ms",
            "update_time_ms",
            "total_frames",
            "dropped_frames",
            "drop_rate",
        ]
        for key in expected_keys:
            self.assertIn(key, stats)

        # Verify reasonable values
        self.assertGreater(stats["fps"], 50)
        self.assertGreater(stats["frame_time_ms"], 5)
        self.assertEqual(stats["total_frames"], 3)

    def test_performance_evaluation(self) -> None:
        """Test performance evaluation methods."""
        # Simulate good performance
        for _ in range(5):
            self.monitor.start_frame()
            time.sleep(0.01)  # 10ms = 100 FPS
            self.monitor.end_frame()

        # Performance should be considered good
        self.assertTrue(self.monitor.is_performance_good())

        # Optimization suggestions should be minimal for good performance
        suggestions = self.monitor.get_optimization_suggestions()
        self.assertIsInstance(suggestions, list)

    def test_dropped_frame_detection(self) -> None:
        """Test dropped frame detection."""
        # Simulate normal frame
        self.monitor.start_frame()
        time.sleep(0.01)  # 10ms - normal
        self.monitor.end_frame()

        # Simulate dropped frame
        self.monitor.start_frame()
        time.sleep(0.03)  # 30ms - should be considered dropped
        self.monitor.end_frame()

        stats = self.monitor.get_performance_stats()
        self.assertEqual(stats["total_frames"], 2)
        self.assertEqual(stats["dropped_frames"], 1)
        self.assertEqual(stats["drop_rate"], 50.0)


if __name__ == "__main__":
    unittest.main()
