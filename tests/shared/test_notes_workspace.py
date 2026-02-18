"""Tests for NotesWorkspace — project-local notes with recycle bin.

Covers: create, read, update, delete (soft), restore, purge, clear,
persistence across instances, and Design by Contract violations.
"""

import pytest

from games.shared.contracts import ContractViolation
from games.shared.notes_workspace import Note, NotesWorkspace

# --- Fixtures ---


@pytest.fixture()
def ws(tmp_path):
    """Fresh workspace in a temporary directory."""
    return NotesWorkspace(tmp_path / ".games_workspace")


# --- Note dataclass ---


class TestNote:
    def test_to_dict_roundtrip(self):
        note = Note(
            id="abc123",
            title="Hello",
            content="World",
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
        data = note.to_dict()
        restored = Note.from_dict(data)
        assert restored.id == note.id
        assert restored.title == note.title
        assert restored.content == note.content
        assert restored.tags == []
        assert restored.deleted_at is None

    def test_from_dict_ignores_extra_keys(self):
        data = {
            "id": "x",
            "title": "t",
            "content": "c",
            "created_at": "now",
            "updated_at": "now",
            "extra_field": "ignored",
        }
        note = Note.from_dict(data)
        assert note.id == "x"

    def test_tags_default_empty(self):
        note = Note(id="a", title="b", content="c", created_at="", updated_at="")
        assert note.tags == []


# --- Create ---


class TestCreate:
    def test_create_returns_id(self, ws):
        nid = ws.create("Test Note", "Some content")
        assert isinstance(nid, str)
        assert len(nid) == 12

    def test_create_persists(self, ws):
        nid = ws.create("Persisted", "Data here")
        note = ws.get(nid)
        assert note is not None
        assert note.title == "Persisted"
        assert note.content == "Data here"

    def test_create_strips_title(self, ws):
        nid = ws.create("  padded  ", "")
        note = ws.get(nid)
        assert note.title == "padded"

    def test_create_blank_title_raises(self, ws):
        with pytest.raises(ContractViolation):
            ws.create("", "content")

    def test_create_whitespace_title_raises(self, ws):
        with pytest.raises(ContractViolation):
            ws.create("   ", "content")

    def test_create_sets_timestamps(self, ws):
        nid = ws.create("Timed")
        note = ws.get(nid)
        assert note.created_at == note.updated_at
        assert "T" in note.created_at  # ISO format


# --- Read ---


class TestRead:
    def test_get_nonexistent_returns_none(self, ws):
        assert ws.get("nonexistent") is None

    def test_list_notes_empty(self, ws):
        assert ws.list_notes() == []

    def test_list_notes_order(self, ws):
        import time

        ws.create("First")
        time.sleep(0.01)
        ws.create("Second")
        notes = ws.list_notes()
        assert len(notes) == 2
        assert notes[0].title == "Second"  # newest first

    def test_list_notes_excludes_deleted(self, ws):
        nid = ws.create("To Delete")
        ws.delete(nid)
        assert ws.list_notes() == []


# --- Update ---


class TestUpdate:
    def test_update_title(self, ws):
        nid = ws.create("Original")
        assert ws.update(nid, title="Updated")
        assert ws.get(nid).title == "Updated"

    def test_update_content(self, ws):
        nid = ws.create("Note", "old")
        ws.update(nid, content="new")
        assert ws.get(nid).content == "new"

    def test_update_advances_timestamp(self, ws):
        import time

        nid = ws.create("Note")
        old_ts = ws.get(nid).updated_at
        time.sleep(0.01)
        ws.update(nid, content="changed")
        assert ws.get(nid).updated_at > old_ts

    def test_update_nonexistent_returns_false(self, ws):
        assert ws.update("nope", title="x") is False

    def test_update_blank_title_raises(self, ws):
        nid = ws.create("Note")
        with pytest.raises(ContractViolation):
            ws.update(nid, title="")

    def test_update_empty_id_raises(self, ws):
        with pytest.raises(ContractViolation):
            ws.update("", title="x")


# --- Delete (soft) ---


class TestDelete:
    def test_delete_moves_to_trash(self, ws):
        nid = ws.create("Trashable")
        assert ws.delete(nid)
        assert ws.get(nid) is None
        trash = ws.list_trash()
        assert len(trash) == 1
        assert trash[0].id == nid

    def test_delete_sets_deleted_at(self, ws):
        nid = ws.create("Note")
        ws.delete(nid)
        trashed = ws.list_trash()[0]
        assert trashed.deleted_at is not None

    def test_delete_nonexistent_returns_false(self, ws):
        assert ws.delete("nope") is False

    def test_delete_idempotent(self, ws):
        nid = ws.create("Note")
        assert ws.delete(nid)
        assert ws.delete(nid) is False


# --- Restore ---


class TestRestore:
    def test_restore_moves_back(self, ws):
        nid = ws.create("Restorable")
        ws.delete(nid)
        assert ws.restore(nid)
        assert ws.get(nid) is not None
        assert ws.list_trash() == []

    def test_restore_clears_deleted_at(self, ws):
        nid = ws.create("Note")
        ws.delete(nid)
        ws.restore(nid)
        note = ws.get(nid)
        assert note.deleted_at is None

    def test_restore_nonexistent_returns_false(self, ws):
        assert ws.restore("nope") is False


# --- Purge ---


class TestPurge:
    def test_purge_permanently_deletes(self, ws):
        nid = ws.create("Gone")
        ws.delete(nid)
        assert ws.purge(nid)
        assert ws.list_trash() == []
        assert ws.get(nid) is None

    def test_purge_nonexistent_returns_false(self, ws):
        assert ws.purge("nope") is False


# --- Empty Trash ---


class TestEmptyTrash:
    def test_empty_trash(self, ws):
        ws.create("A")
        ws.create("B")
        ws.clear()
        count = ws.empty_trash()
        assert count == 2
        assert ws.list_trash() == []

    def test_empty_trash_when_empty(self, ws):
        assert ws.empty_trash() == 0


# --- Clear ---


class TestClear:
    def test_clear_moves_all_to_trash(self, ws):
        ws.create("A")
        ws.create("B")
        ws.create("C")
        count = ws.clear()
        assert count == 3
        assert ws.list_notes() == []
        assert len(ws.list_trash()) == 3

    def test_clear_empty_workspace(self, ws):
        assert ws.clear() == 0


# --- Persistence ---


class TestPersistence:
    def test_survives_reinstantiation(self, tmp_path):
        ws_dir = tmp_path / ".games_workspace"
        ws1 = NotesWorkspace(ws_dir)
        nid = ws1.create("Persistent", "content")

        ws2 = NotesWorkspace(ws_dir)
        note = ws2.get(nid)
        assert note is not None
        assert note.title == "Persistent"

    def test_trash_survives_reinstantiation(self, tmp_path):
        ws_dir = tmp_path / ".games_workspace"
        ws1 = NotesWorkspace(ws_dir)
        nid = ws1.create("Trashed")
        ws1.delete(nid)

        ws2 = NotesWorkspace(ws_dir)
        trash = ws2.list_trash()
        assert len(trash) == 1
        assert trash[0].id == nid

    def test_corrupt_file_skipped(self, tmp_path):
        ws_dir = tmp_path / ".games_workspace"
        ws = NotesWorkspace(ws_dir)
        ws.create("Good")
        # Write a corrupt file
        (ws_dir / "notes" / "corrupt.json").write_text("not json", encoding="utf-8")
        notes = ws.list_notes()
        assert len(notes) == 1
        assert notes[0].title == "Good"
