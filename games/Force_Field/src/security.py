"""Security utilities for Force Field game."""

import hashlib
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manages security aspects of the game including save file validation."""

    def __init__(self) -> None:
        """Initialize security manager."""
        self.allowed_save_extensions = {".txt", ".json", ".dat"}
        self.max_save_file_size = 1024 * 1024  # 1MB max save file

    def validate_save_path(self, filepath: Path) -> bool:
        """Validate that a save file path is safe to use.

        Args:
            filepath: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve path to prevent directory traversal
            resolved_path = filepath.resolve()

            # Check if path is within allowed directory (game directory)
            game_dir = Path(__file__).parent.parent.resolve()
            try:
                # Use is_relative_to for secure path validation (Python 3.9+)
                if not resolved_path.is_relative_to(game_dir):
                    logger.warning(
                        "Save path outside game directory: %s", resolved_path
                    )
                    return False
            except AttributeError:
                # Fallback for Python < 3.9: check if game_dir is in parents
                if game_dir not in resolved_path.parents and resolved_path != game_dir:
                    logger.warning(
                        "Save path outside game directory: %s", resolved_path
                    )
                    return False

            # Check file extension
            if resolved_path.suffix.lower() not in self.allowed_save_extensions:
                logger.warning("Invalid save file extension: %s", resolved_path.suffix)
                return False

            # Check if file exists and validate size
            if resolved_path.exists():
                file_size = resolved_path.stat().st_size
                if file_size > self.max_save_file_size:
                    logger.warning("Save file too large: %d bytes", file_size)
                    return False

            return True

        except (OSError, ValueError) as e:
            logger.error("Error validating save path: %s", e)
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to prevent security issues.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        sanitized = "".join(c for c in filename if c not in dangerous_chars)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Ensure filename is not empty
        if not sanitized:
            sanitized = "savegame"

        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized

    def create_secure_temp_file(self, suffix: str = ".tmp") -> Path | None:
        """Create a secure temporary file.

        Args:
            suffix: File suffix

        Returns:
            Path to temporary file or None if creation failed
        """
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="force_field_")
            os.close(fd)  # Close file descriptor, we just need the path
            return Path(temp_path)
        except OSError as e:
            logger.error("Failed to create temporary file: %s", e)
            return None

    def calculate_file_hash(self, filepath: Path) -> str | None:
        """Calculate SHA-256 hash of a file for integrity checking.

        Args:
            filepath: Path to file

        Returns:
            Hex digest of file hash or None if calculation failed
        """
        try:
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            logger.error("Failed to calculate file hash: %s", e)
            return None

    def validate_save_file_content(self, filepath: Path) -> bool:
        """Validate save file content for basic security.

        Args:
            filepath: Path to save file

        Returns:
            True if content appears safe, False otherwise
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read(self.max_save_file_size)

            # Check for suspicious content
            suspicious_patterns = [
                "import ",
                "exec(",
                "eval(",
                "__import__",
                "subprocess",
                "os.system",
            ]

            content_lower = content.lower()
            for pattern in suspicious_patterns:
                if pattern in content_lower:
                    logger.warning("Suspicious pattern found in save file: %s", pattern)
                    return False

            return True

        except (OSError, UnicodeDecodeError) as e:
            logger.error("Error validating save file content: %s", e)
            return False

    def secure_delete_file(self, filepath: Path) -> bool:
        """Securely delete a file by overwriting it first.

        Note: This implementation performs a single overwrite pass with random data.
        On modern SSDs with wear leveling, this may not guarantee complete data
        erasure due to the underlying storage technology. For highly sensitive data,
        consider using specialized secure deletion tools or full disk encryption.

        Args:
            filepath: Path to file to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if not filepath.exists():
                return True

            # Get file size
            file_size = filepath.stat().st_size

            # Overwrite with random data
            with open(filepath, "r+b") as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())

            # Delete the file
            filepath.unlink()
            logger.debug("Securely deleted file: %s", filepath)
            return True

        except OSError as e:
            logger.error("Failed to securely delete file: %s", e)
            return False
