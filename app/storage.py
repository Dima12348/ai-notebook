"""SQLite storage layer for AI Notebook desktop app."""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "notebook.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#6366f1',
            icon TEXT DEFAULT '📁',
            sort_order INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            category_id INTEGER,
            entry_type TEXT NOT NULL DEFAULT 'note'
                CHECK(entry_type IN ('note','task')),
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','in_progress','done','archived')),
            priority TEXT NOT NULL DEFAULT 'normal'
                CHECK(priority IN ('low','normal','high','urgent')),
            due_date TEXT,
            remind_at TEXT,
            pinned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (entry_id, tag_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_entries_status ON entries(status);
        CREATE INDEX IF NOT EXISTS idx_entries_remind ON entries(remind_at);
    """)
    # Seed default categories
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO categories (name, color, icon, sort_order) VALUES (?,?,?,?)",
            [
                ("Справи",  "#6366f1", "📋", 1),
                ("Нотатки", "#10b981", "📝", 2),
                ("Ідеї",    "#f59e0b", "💡", 3),
                ("Зустрічі","#ef4444", "📅", 4),
                ("Покупки", "#8b5cf6", "🛒", 5),
            ],
        )
    # Seed default robot settings
    defaults = {
        "robot_color": "#6366f1",
        "robot_size": "60",
        "robot_speed": "2",
        "robot_visible": "1",
        "robot_style": "modern",
    }
    for k, v in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", (k, v)
        )
    conn.commit()
    conn.close()


# ── Settings ─────────────────────────────────────────────────

def get_setting(key, default=None):
    conn = _conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value))
    )
    conn.commit()
    conn.close()


def get_all_settings():
    conn = _conn()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ── Categories ───────────────────────────────────────────────

def list_categories():
    conn = _conn()
    rows = conn.execute("""
        SELECT c.*, COUNT(e.id) as entry_count
        FROM categories c LEFT JOIN entries e ON e.category_id = c.id
        GROUP BY c.id ORDER BY c.sort_order
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_category(name, color="#6366f1", icon="📁"):
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO categories (name, color, icon) VALUES (?,?,?)",
        (name, color, icon),
    )
    conn.commit()
    cat_id = cur.lastrowid
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cat_id,)).fetchone()
    conn.close()
    return dict(row)


def update_category(cat_id, **kw):
    conn = _conn()
    fields = ", ".join(f"{k}=?" for k in kw)
    conn.execute(f"UPDATE categories SET {fields} WHERE id=?", (*kw.values(), cat_id))
    conn.commit()
    conn.close()


def delete_category(cat_id):
    conn = _conn()
    conn.execute("UPDATE entries SET category_id=NULL WHERE category_id=?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


# ── Entries ──────────────────────────────────────────────────

def _row_to_entry(conn, row):
    e = dict(row)
    tags = conn.execute(
        "SELECT t.name FROM tags t JOIN entry_tags et ON t.id=et.tag_id WHERE et.entry_id=?",
        (e["id"],),
    ).fetchall()
    e["tags"] = [t[0] for t in tags]
    return e


def list_entries(status=None, category_id=None, search=None,
                 entry_type=None, priority=None, limit=200):
    conn = _conn()
    clauses, params = [], []
    if status:
        clauses.append("e.status=?"); params.append(status)
    if category_id:
        clauses.append("e.category_id=?"); params.append(category_id)
    if entry_type:
        clauses.append("e.entry_type=?"); params.append(entry_type)
    if priority:
        clauses.append("e.priority=?"); params.append(priority)
    if search:
        clauses.append("(e.title LIKE ? OR e.content LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(f"""
        SELECT e.*, c.name as category_name, c.color as category_color, c.icon as category_icon
        FROM entries e LEFT JOIN categories c ON e.category_id = c.id
        {where}
        ORDER BY e.pinned DESC, e.updated_at DESC
        LIMIT {limit}
    """, params).fetchall()
    result = [_row_to_entry(conn, r) for r in rows]
    conn.close()
    return result


def get_entry(entry_id):
    conn = _conn()
    row = conn.execute("""
        SELECT e.*, c.name as category_name, c.color as category_color, c.icon as category_icon
        FROM entries e LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.id=?
    """, (entry_id,)).fetchone()
    if not row:
        conn.close()
        return None
    result = _row_to_entry(conn, row)
    conn.close()
    return result


def create_entry(title, content="", category_id=None, entry_type="note",
                 status="active", priority="normal", due_date=None,
                 remind_at=None, pinned=0, tags=None):
    conn = _conn()
    cur = conn.execute(
        """INSERT INTO entries
           (title, content, category_id, entry_type, status, priority, due_date, remind_at, pinned)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (title, content, category_id, entry_type, status, priority, due_date, remind_at, pinned),
    )
    entry_id = cur.lastrowid
    if tags:
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            t = conn.execute("SELECT id FROM tags WHERE name=?", (tag_name,)).fetchone()
            if t:
                tag_id = t[0]
            else:
                tag_id = conn.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,)).lastrowid
            conn.execute("INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?,?)",
                         (entry_id, tag_id))
    conn.commit()
    result = _row_to_entry(conn, conn.execute(
        """SELECT e.*, c.name as category_name, c.color as category_color, c.icon as category_icon
           FROM entries e LEFT JOIN categories c ON e.category_id = c.id
           WHERE e.id=?""", (entry_id,)).fetchone())
    conn.close()
    return result


def update_entry(entry_id, **kw):
    conn = _conn()
    tags = kw.pop("tags", None)
    if kw:
        kw["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = ", ".join(f"{k}=?" for k in kw)
        conn.execute(f"UPDATE entries SET {fields} WHERE id=?", (*kw.values(), entry_id))
    if tags is not None:
        conn.execute("DELETE FROM entry_tags WHERE entry_id=?", (entry_id,))
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            t = conn.execute("SELECT id FROM tags WHERE name=?", (tag_name,)).fetchone()
            if t:
                tag_id = t[0]
            else:
                tag_id = conn.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,)).lastrowid
            conn.execute("INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?,?)",
                         (entry_id, tag_id))
    conn.commit()
    conn.close()


def delete_entry(entry_id):
    conn = _conn()
    conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()


# ── Stats ────────────────────────────────────────────────────

def get_stats():
    conn = _conn()
    stats = {}
    for s in ("active", "in_progress", "done", "archived"):
        stats[s] = conn.execute("SELECT COUNT(*) FROM entries WHERE status=?", (s,)).fetchone()[0]
    stats["total"] = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    stats["overdue"] = conn.execute(
        "SELECT COUNT(*) FROM entries WHERE due_date < date('now','localtime') AND status NOT IN ('done','archived')"
    ).fetchone()[0]
    stats["reminders_today"] = conn.execute(
        "SELECT COUNT(*) FROM entries WHERE remind_at IS NOT NULL AND remind_at != '' AND status NOT IN ('done','archived')"
    ).fetchone()[0]
    conn.close()
    return stats


# ── Due reminders ────────────────────────────────────────────

def get_due_reminders():
    """Return entries whose remind_at <= now and haven't been dismissed."""
    conn = _conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute("""
        SELECT e.*, c.name as category_name, c.color as category_color, c.icon as category_icon
        FROM entries e LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.remind_at IS NOT NULL AND e.remind_at != ''
          AND e.remind_at <= ? AND e.status NOT IN ('done','archived')
        ORDER BY e.remind_at ASC
    """, (now,)).fetchall()
    result = [_row_to_entry(conn, r) for r in rows]
    conn.close()
    return result
