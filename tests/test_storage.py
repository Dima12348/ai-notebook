"""Tests for app.storage — SQLite storage layer."""
import os
import sys
import tempfile
from datetime import datetime, timedelta

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import storage


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Redirect DB_PATH to a temporary directory for every test."""
    db_file = tmp_path / "notebook.db"
    monkeypatch.setattr(storage, "DB_PATH", str(db_file))
    yield db_file


# ── init_db ──────────────────────────────────────────────────


class TestInitDb:
    def test_creates_tables_and_default_categories(self):
        storage.init_db()
        cats = storage.list_categories()
        assert len(cats) == 5
        names = [c["name"] for c in cats]
        assert "Справи" in names
        assert "Нотатки" in names

    def test_creates_default_settings(self):
        storage.init_db()
        settings = storage.get_all_settings()
        assert settings["robot_color"] == "#6366f1"
        assert settings["robot_size"] == "60"
        assert settings["robot_visible"] == "1"

    def test_idempotent(self):
        storage.init_db()
        storage.init_db()
        cats = storage.list_categories()
        assert len(cats) == 5  # no duplicates


# ── Settings ─────────────────────────────────────────────────


class TestSettings:
    def test_get_set_setting(self):
        storage.init_db()
        storage.set_setting("my_key", "my_value")
        assert storage.get_setting("my_key") == "my_value"

    def test_get_missing_returns_default(self):
        storage.init_db()
        assert storage.get_setting("nonexistent", "fallback") == "fallback"

    def test_overwrite_setting(self):
        storage.init_db()
        storage.set_setting("k", "v1")
        storage.set_setting("k", "v2")
        assert storage.get_setting("k") == "v2"

    def test_get_all_settings(self):
        storage.init_db()
        storage.set_setting("a", "1")
        storage.set_setting("b", "2")
        all_s = storage.get_all_settings()
        assert all_s["a"] == "1"
        assert all_s["b"] == "2"


# ── Categories ───────────────────────────────────────────────


class TestCategories:
    def test_create_category(self):
        storage.init_db()
        cat = storage.create_category("Робота", color="#ff0000", icon="💼")
        assert cat["name"] == "Робота"
        assert cat["color"] == "#ff0000"
        assert cat["icon"] == "💼"
        assert cat["id"] > 0

    def test_list_categories_with_count(self):
        storage.init_db()
        cats = storage.list_categories()
        cat_id = cats[0]["id"]
        storage.create_entry("Test", category_id=cat_id)
        cats = storage.list_categories()
        found = next(c for c in cats if c["id"] == cat_id)
        assert found["entry_count"] == 1

    def test_update_category(self):
        storage.init_db()
        cat = storage.create_category("Old")
        storage.update_category(cat["id"], name="New", color="#00ff00")
        cats = storage.list_categories()
        updated = next(c for c in cats if c["id"] == cat["id"])
        assert updated["name"] == "New"
        assert updated["color"] == "#00ff00"

    def test_delete_category_nulls_entries(self):
        storage.init_db()
        cat = storage.create_category("ToDelete")
        entry = storage.create_entry("Entry", category_id=cat["id"])
        storage.delete_category(cat["id"])
        refreshed = storage.get_entry(entry["id"])
        assert refreshed["category_id"] is None

    def test_category_unique_name(self):
        storage.init_db()
        storage.create_category("Unique")
        with pytest.raises(Exception):
            storage.create_category("Unique")


# ── Entries CRUD ─────────────────────────────────────────────


class TestEntriesCRUD:
    def test_create_and_get_entry(self):
        storage.init_db()
        entry = storage.create_entry(
            title="Test Note",
            content="Hello world",
            entry_type="note",
            priority="high",
        )
        assert entry["title"] == "Test Note"
        assert entry["content"] == "Hello world"
        assert entry["entry_type"] == "note"
        assert entry["priority"] == "high"
        assert entry["status"] == "active"

        fetched = storage.get_entry(entry["id"])
        assert fetched["title"] == "Test Note"

    def test_create_task_with_due_date(self):
        storage.init_db()
        entry = storage.create_entry(
            title="Task",
            entry_type="task",
            due_date="2026-05-10",
            remind_at="2026-05-09 10:00",
        )
        assert entry["entry_type"] == "task"
        assert entry["due_date"] == "2026-05-10"
        assert entry["remind_at"] == "2026-05-09 10:00"

    def test_update_entry(self):
        storage.init_db()
        entry = storage.create_entry("Old Title")
        storage.update_entry(entry["id"], title="New Title", priority="urgent")
        refreshed = storage.get_entry(entry["id"])
        assert refreshed["title"] == "New Title"
        assert refreshed["priority"] == "urgent"

    def test_update_entry_touches_updated_at(self):
        storage.init_db()
        entry = storage.create_entry("Title")
        old_updated = entry["updated_at"]
        storage.update_entry(entry["id"], content="changed")
        refreshed = storage.get_entry(entry["id"])
        assert refreshed["updated_at"] >= old_updated

    def test_delete_entry(self):
        storage.init_db()
        entry = storage.create_entry("ToDelete")
        storage.delete_entry(entry["id"])
        assert storage.get_entry(entry["id"]) is None

    def test_get_nonexistent_returns_none(self):
        storage.init_db()
        assert storage.get_entry(99999) is None

    def test_create_with_category(self):
        storage.init_db()
        cats = storage.list_categories()
        entry = storage.create_entry("Categorized", category_id=cats[0]["id"])
        assert entry["category_id"] == cats[0]["id"]
        assert entry["category_name"] == cats[0]["name"]

    def test_pinned_entry(self):
        storage.init_db()
        entry = storage.create_entry("Pinned", pinned=1)
        assert entry["pinned"] == 1


# ── Tags ─────────────────────────────────────────────────────


class TestTags:
    def test_create_entry_with_tags(self):
        storage.init_db()
        entry = storage.create_entry("Tagged", tags=["робота", "важливе"])
        assert set(entry["tags"]) == {"робота", "важливе"}

    def test_update_entry_tags(self):
        storage.init_db()
        entry = storage.create_entry("Tagged", tags=["old"])
        storage.update_entry(entry["id"], tags=["new1", "new2"])
        refreshed = storage.get_entry(entry["id"])
        assert set(refreshed["tags"]) == {"new1", "new2"}

    def test_tags_persist_across_entries(self):
        storage.init_db()
        storage.create_entry("A", tags=["shared"])
        storage.create_entry("B", tags=["shared"])
        from app.storage import _conn
        conn = _conn()
        count = conn.execute("SELECT COUNT(*) FROM tags WHERE name='shared'").fetchone()[0]
        conn.close()
        assert count == 1  # tag reused, not duplicated

    def test_empty_tags_ignored(self):
        storage.init_db()
        entry = storage.create_entry("Test", tags=["", "  ", "valid"])
        assert entry["tags"] == ["valid"]

    def test_delete_entry_cleans_tags(self):
        storage.init_db()
        entry = storage.create_entry("Tagged", tags=["temp"])
        storage.delete_entry(entry["id"])
        from app.storage import _conn
        conn = _conn()
        count = conn.execute(
            "SELECT COUNT(*) FROM entry_tags WHERE entry_id=?", (entry["id"],)
        ).fetchone()[0]
        conn.close()
        assert count == 0


# ── List / Filter ────────────────────────────────────────────


class TestListEntries:
    def test_list_all(self):
        storage.init_db()
        storage.create_entry("A")
        storage.create_entry("B")
        entries = storage.list_entries()
        assert len(entries) == 2

    def test_filter_by_status(self):
        storage.init_db()
        storage.create_entry("Active")
        done = storage.create_entry("Done")
        storage.update_entry(done["id"], status="done")
        active = storage.list_entries(status="active")
        assert len(active) == 1
        assert active[0]["title"] == "Active"

    def test_filter_by_category(self):
        storage.init_db()
        cats = storage.list_categories()
        storage.create_entry("Cat A", category_id=cats[0]["id"])
        storage.create_entry("Cat B", category_id=cats[1]["id"])
        filtered = storage.list_entries(category_id=cats[0]["id"])
        assert len(filtered) == 1

    def test_filter_by_entry_type(self):
        storage.init_db()
        storage.create_entry("Note", entry_type="note")
        storage.create_entry("Task", entry_type="task")
        notes = storage.list_entries(entry_type="note")
        assert len(notes) == 1

    def test_filter_by_priority(self):
        storage.init_db()
        storage.create_entry("Normal")
        storage.create_entry("Urgent", priority="urgent")
        urgent = storage.list_entries(priority="urgent")
        assert len(urgent) == 1

    def test_search(self):
        storage.init_db()
        storage.create_entry("Buy groceries", content="milk, eggs")
        storage.create_entry("Write code", content="python")
        results = storage.list_entries(search="milk")
        assert len(results) == 1
        assert results[0]["title"] == "Buy groceries"

    def test_search_by_title(self):
        storage.init_db()
        storage.create_entry("UniqueTitle123")
        results = storage.list_entries(search="UniqueTitle123")
        assert len(results) == 1

    def test_limit(self):
        storage.init_db()
        for i in range(10):
            storage.create_entry(f"Entry {i}")
        entries = storage.list_entries(limit=3)
        assert len(entries) == 3

    def test_pinned_first(self):
        storage.init_db()
        storage.create_entry("Normal")
        storage.create_entry("Pinned", pinned=1)
        entries = storage.list_entries()
        assert entries[0]["title"] == "Pinned"


# ── Stats ────────────────────────────────────────────────────


class TestStats:
    def test_empty_stats(self):
        storage.init_db()
        stats = storage.get_stats()
        assert stats["total"] == 0
        assert stats["active"] == 0
        assert stats["done"] == 0

    def test_counts_by_status(self):
        storage.init_db()
        storage.create_entry("A")
        storage.create_entry("B")
        done = storage.create_entry("C")
        storage.update_entry(done["id"], status="done")
        stats = storage.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 2
        assert stats["done"] == 1

    def test_overdue_count(self):
        storage.init_db()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        storage.create_entry("Overdue", due_date=yesterday)
        storage.create_entry("No due")
        stats = storage.get_stats()
        assert stats["overdue"] == 1

    def test_done_not_overdue(self):
        storage.init_db()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        entry = storage.create_entry("DoneOverdue", due_date=yesterday)
        storage.update_entry(entry["id"], status="done")
        stats = storage.get_stats()
        assert stats["overdue"] == 0


# ── Due Reminders ────────────────────────────────────────────


class TestDueReminders:
    def test_returns_due_entries(self):
        storage.init_db()
        past = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        storage.create_entry("Reminder", remind_at=past)
        due = storage.get_due_reminders()
        assert len(due) == 1
        assert due[0]["title"] == "Reminder"

    def test_ignores_future_reminders(self):
        storage.init_db()
        future = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        storage.create_entry("Future", remind_at=future)
        due = storage.get_due_reminders()
        assert len(due) == 0

    def test_ignores_done_entries(self):
        storage.init_db()
        past = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        entry = storage.create_entry("DoneReminder", remind_at=past)
        storage.update_entry(entry["id"], status="done")
        due = storage.get_due_reminders()
        assert len(due) == 0

    def test_ignores_empty_remind_at(self):
        storage.init_db()
        storage.create_entry("NoReminder", remind_at="")
        due = storage.get_due_reminders()
        assert len(due) == 0
