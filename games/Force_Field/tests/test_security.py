"""Tests for security functionality."""

import tempfile
import unittest
from pathlib import Path

from games.Force_Field.src.security import SecurityManager


class TestSecurity(unittest.TestCase):
    """Test security manager functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.security_manager = SecurityManager()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Clean up temp directory
        for file in self.temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        self.temp_dir.rmdir()

    def test_validate_safe_save_path(self) -> None:
        """Test validation of safe save file paths."""
        # Test case 1: File outside game directory should fail
        external_file = self.temp_dir / "test_save.txt"
        external_file.write_text("test content")
        result = self.security_manager.validate_save_path(external_file)
        self.assertFalse(result)

        # Test case 2: File within game directory should pass
        # Create a mock file within the game directory structure
        from pathlib import Path

        game_dir = Path(__file__).parent.parent.resolve()
        internal_file = game_dir / "test_internal_save.txt"
        try:
            internal_file.write_text("test content")
            result = self.security_manager.validate_save_path(internal_file)
            self.assertTrue(result)
        finally:
            # Clean up test file
            if internal_file.exists():
                internal_file.unlink()

    def test_sanitize_filename(self) -> None:
        """Test filename sanitization."""
        # Test dangerous characters
        dangerous_name = 'test<>:"/\\|?*file.txt'
        sanitized = self.security_manager.sanitize_filename(dangerous_name)
        self.assertEqual(sanitized, "testfile.txt")

        # Test empty filename
        empty_sanitized = self.security_manager.sanitize_filename("")
        self.assertEqual(empty_sanitized, "savegame")

        # Test long filename
        long_name = "a" * 150 + ".txt"
        long_sanitized = self.security_manager.sanitize_filename(long_name)
        self.assertLessEqual(len(long_sanitized), 100)

    def test_file_hash_calculation(self) -> None:
        """Test file hash calculation."""
        test_file = self.temp_dir / "hash_test.txt"
        test_content = "test content for hashing"
        test_file.write_text(test_content)

        hash_result = self.security_manager.calculate_file_hash(test_file)
        self.assertIsNotNone(hash_result)
        if hash_result is not None:
            self.assertEqual(len(hash_result), 64)  # SHA-256 hex digest length

    def test_validate_save_file_content(self) -> None:
        """Test save file content validation."""
        # Safe content
        safe_file = self.temp_dir / "safe.txt"
        safe_file.write_text("level=5\nscore=1000")
        self.assertTrue(self.security_manager.validate_save_file_content(safe_file))

        # Suspicious content
        suspicious_file = self.temp_dir / "suspicious.txt"
        suspicious_file.write_text("import os\nos.system('rm -rf /')")
        self.assertFalse(
            self.security_manager.validate_save_file_content(suspicious_file)
        )

    def test_create_secure_temp_file(self) -> None:
        """Test secure temporary file creation."""
        temp_file = self.security_manager.create_secure_temp_file(".test")
        self.assertIsNotNone(temp_file)
        if temp_file:
            self.assertTrue(temp_file.exists())
            self.assertTrue(str(temp_file).endswith(".test"))
            # Clean up
            temp_file.unlink()


if __name__ == "__main__":
    unittest.main()
