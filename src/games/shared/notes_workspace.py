"""Project-local notes workspace with recycle bin support.

Provides a file-based notes system with CRUD operations, soft-delete
via recycle bin semantics, and restore support. Designed for project-local
persistence with reversible operations.

Usage:
    workspace = NotesWorkspace("/path/to/project")
    note_id = workspace.create("My note title", "Note content here")
    workspace.delete(note_id)       # Moves to recycle bin
    workspace.restore(note_id)      # Restores from recycle bin
    workspace.purge(note_id)        # Permanently deletes from bin
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from games.shared.contracts import ContractViolation, precondition

logger = logging.getLogger(__name__)


@dataclass
class Note:
    """A single note with metadata."""

    id: str
    title: str
    content: str
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Note:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(tz=UTC).isoformat()


class NotesWorkspace:
    """File-based notes workspace with recycle bin.

    Storage layout:
        {workspace_dir}/
            notes/          # Active notes (one JSON file each)
            trash/          # Soft-deleted notes
    """

    def __init__(self, workspace_dir: str | Path) -> None:
        self._root = Path(workspace_dir)
        self._notes_dir = self._root / "notes"
        self._trash_dir = self._root / "trash"
        self._notes_dir.mkdir(parents=True, exist_ok=True)
        self._trash_dir.mkdir(parents=True, exist_ok=True)

    # --- CRUD ---

    @precondition(
        lambda self, title, content="": bool(title.strip()),
        "title must not be blank",
    )
    def create(self, title: str, content: str = "") -> str:
        """Create a new note and persist it. Returns the note ID."""
        now = _now_iso()
        note = Note(
            id=uuid.uuid4().hex[:12],
            title=title.strip(),
            content=content,
            created_at=now,
            updated_at=now,
        )
        self._save_note(note, self._notes_dir)
        logger.info("Created note %s: %s", note.id, note.title)
        return note.id

    def get(self, note_id: str) -> Note | None:
        """Retrieve an active note by ID, or None if not found."""
        return self._load_note(note_id, self._notes_dir)

    def list_notes(self) -> list[Note]:
        """List all active (non-deleted) notes, newest first."""
        notes = self._load_all(self._notes_dir)
        notes.sort(key=lambda n: n.updated_at, reverse=True)
        return notes

    @precondition(
        lambda self, note_id, **kw: bool(note_id),
        "note_id must not be empty",
    )
    def update(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
    ) -> bool:
        """Update title and/or content. Returns True if updated."""
        note = self._load_note(note_id, self._notes_dir)
        if note is None:
            return False
        if title is not None:
            if not title.strip():
                raise ContractViolation("title must not be blank")
            note.title = title.strip()
        if content is not None:
            note.content = content
        note.updated_at = _now_iso()
        self._save_note(note, self._notes_dir)
        logger.info("Updated note %s", note_id)
        return True

    # --- Recycle Bin ---

    def delete(self, note_id: str) -> bool:
        """Soft-delete: move note from notes/ to trash/. Returns True if moved."""
        note = self._load_note(note_id, self._notes_dir)
        if note is None:
            return False
        note.deleted_at = _now_iso()
        self._save_note(note, self._trash_dir)
        self._delete_file(note_id, self._notes_dir)
        logger.info("Deleted note %s to recycle bin", note_id)
        return True

    def restore(self, note_id: str) -> bool:
        """Restore a note from the recycle bin. Returns True if restored."""
        note = self._load_note(note_id, self._trash_dir)
        if note is None:
            return False
        note.deleted_at = None
        note.updated_at = _now_iso()
        self._save_note(note, self._notes_dir)
        self._delete_file(note_id, self._trash_dir)
        logger.info("Restored note %s from recycle bin", note_id)
        return True

    def list_trash(self) -> list[Note]:
        """List all notes in the recycle bin, most recently deleted first."""
        notes = self._load_all(self._trash_dir)
        notes.sort(key=lambda n: n.deleted_at or "", reverse=True)
        return notes

    def purge(self, note_id: str) -> bool:
        """Permanently delete a note from the recycle bin. Returns True if purged."""
        if not self._note_path(note_id, self._trash_dir).exists():
            return False
        self._delete_file(note_id, self._trash_dir)
        logger.info("Purged note %s permanently", note_id)
        return True

    def empty_trash(self) -> int:
        """Permanently delete all notes in the recycle bin. Returns count purged."""
        trashed = self._load_all(self._trash_dir)
        for note in trashed:
            self._delete_file(note.id, self._trash_dir)
        logger.info("Emptied recycle bin (%d notes purged)", len(trashed))
        return len(trashed)

    # --- Bulk ---

    def clear(self) -> int:
        """Move all active notes to the recycle bin. Returns count deleted."""
        active = self.list_notes()
        for note in active:
            self.delete(note.id)
        return len(active)

    # --- Persistence helpers ---

    def _note_path(self, note_id: str, directory: Path) -> Path:
        return directory / f"{note_id}.json"

    def _save_note(self, note: Note, directory: Path) -> None:
        path = self._note_path(note.id, directory)
        path.write_text(json.dumps(note.to_dict(), indent=2), encoding="utf-8")

    def _load_note(self, note_id: str, directory: Path) -> Note | None:
        path = self._note_path(note_id, directory)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Note.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            logger.warning("Corrupt note file: %s", path)
            return None

    def _load_all(self, directory: Path) -> list[Note]:
        notes = []
        for path in directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                notes.append(Note.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                logger.warning("Skipping corrupt note: %s", path)
        return notes

    def _delete_file(self, note_id: str, directory: Path) -> None:
        path = self._note_path(note_id, directory)
        if path.exists():
            path.unlink()
