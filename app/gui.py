"""Main application window — modern dark GTK3 UI."""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
from datetime import datetime

from . import storage


# ── CSS Theme ────────────────────────────────────────────────

CSS = b"""
@define-color bg #0f1117;
@define-color bg2 #1a1d27;
@define-color bg3 #222633;
@define-color border #2a2d3a;
@define-color text #e2e8f0;
@define-color dim #94a3b8;
@define-color muted #64748b;
@define-color accent #6366f1;
@define-color green #10b981;
@define-color orange #f59e0b;
@define-color red #ef4444;

* {
    -gtk-icon-style: symbolic;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

window, .main-bg {
    background-color: @bg;
    color: @text;
}

.sidebar {
    background-color: @bg2;
    border-right: 1px solid @border;
}

.sidebar-btn {
    background: transparent;
    color: @dim;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

.sidebar-btn:hover {
    background: alpha(@accent, 0.1);
    color: @text;
}

.sidebar-btn.active {
    background: alpha(@accent, 0.15);
    color: @accent;
    font-weight: bold;
}

.sidebar-label {
    color: @muted;
    font-size: 10px;
    font-weight: bold;
    padding: 8px 12px 4px;
}

.card {
    background-color: @bg2;
    border: 1px solid @border;
    border-radius: 12px;
    padding: 16px;
}

.card:hover {
    border-color: alpha(@accent, 0.5);
}

.card-done {
    opacity: 0.5;
}

.card-pinned {
    border-left: 3px solid @orange;
}

.stat-card {
    background-color: @bg2;
    border: 1px solid @border;
    border-radius: 12px;
    padding: 20px;
}

.entry-title {
    font-size: 14px;
    font-weight: 600;
    color: @text;
}

.entry-content {
    font-size: 12px;
    color: @dim;
}

.entry-meta {
    font-size: 11px;
    color: @muted;
}

.badge {
    background: alpha(@accent, 0.15);
    color: @accent;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

.badge-green { background: alpha(@green, 0.15); color: @green; }
.badge-orange { background: alpha(@orange, 0.15); color: @orange; }
.badge-red { background: alpha(@red, 0.15); color: @red; }

.btn-primary {
    background: @accent;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
}

.btn-primary:hover {
    background: alpha(@accent, 0.8);
}

.btn-secondary {
    background: @bg3;
    color: @dim;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

.btn-secondary:hover {
    background: alpha(@bg3, 0.8);
    color: @text;
}

.btn-danger {
    background: @red;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

.btn-icon {
    background: transparent;
    border: none;
    color: @muted;
    border-radius: 6px;
    padding: 4px 8px;
}

.btn-icon:hover {
    background: alpha(@accent, 0.1);
    color: @text;
}

.search-entry {
    background: @bg2;
    border: 1px solid @border;
    border-radius: 10px;
    color: @text;
    padding: 8px 12px;
    font-size: 13px;
}

.search-entry:focus {
    border-color: @accent;
}

.topbar {
    background: @bg;
    border-bottom: 1px solid @border;
    padding: 12px 20px;
}

.header-title {
    font-size: 18px;
    font-weight: 700;
    color: @text;
}

/* Dialog styling */
dialog {
    background: @bg2;
    color: @text;
}

dialog .dialog-vbox {
    background: @bg2;
}

dialog .dialog-action-area {
    background: @bg2;
    border-top: 1px solid @border;
}

dialog entry, dialog textview, dialog combobox button {
    background: @bg;
    border: 1px solid @border;
    border-radius: 8px;
    color: @text;
    padding: 8px;
    font-size: 13px;
}

dialog entry:focus, dialog textview:focus {
    border-color: @accent;
}

dialog label {
    color: @dim;
    font-size: 12px;
}

dialog combobox button {
    background: @bg;
    color: @text;
}

/* Scrollbar */
scrollbar {
    background: transparent;
}

scrollbar slider {
    background: @border;
    border-radius: 4px;
    min-width: 6px;
}

scrollbar slider:hover {
    background: @muted;
}

/* TreeView / ListBox */
list {
    background: transparent;
}

list row {
    background: transparent;
    padding: 0;
}

list row:hover {
    background: alpha(@accent, 0.04);
}

list row:selected {
    background: alpha(@accent, 0.08);
}

/* Switch */
switch {
    background: @border;
    border-radius: 14px;
    min-height: 24px;
    min-width: 48px;
}

switch:checked {
    background: @accent;
}

switch slider {
    background: white;
    border-radius: 12px;
    min-height: 20px;
    min-width: 20px;
}

/* Scale */
scale trough {
    background: @border;
    border-radius: 4px;
    min-height: 6px;
}

scale highlight {
    background: @accent;
    border-radius: 4px;
}

scale slider {
    background: white;
    border-radius: 10px;
    min-height: 18px;
    min-width: 18px;
}

/* Notebook (tabs) */
notebook header {
    background: @bg;
    border-bottom: 1px solid @border;
}

notebook tab {
    background: transparent;
    color: @dim;
    padding: 8px 16px;
    border: none;
}

notebook tab:checked {
    color: @accent;
    border-bottom: 2px solid @accent;
}

/* Spin button */
spinbutton {
    background: @bg;
    border: 1px solid @border;
    border-radius: 8px;
    color: @text;
}

spinbutton button {
    background: @bg3;
    color: @dim;
    border: none;
}

/* Color button */
colorbutton {
    border-radius: 8px;
}

/* Menu */
menu, .menu {
    background: @bg2;
    border: 1px solid @border;
    border-radius: 10px;
    padding: 6px;
    color: @text;
}

menuitem {
    padding: 6px 12px;
    border-radius: 6px;
}

menuitem:hover {
    background: alpha(@accent, 0.1);
}

tooltip {
    background: @bg3;
    color: @text;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 6px 10px;
}
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


# ── Helpers ──────────────────────────────────────────────────

PRIORITY_MAP = {
    "urgent": ("🔴", "badge-red"),
    "high":   ("🟠", "badge-orange"),
    "normal": ("", ""),
    "low":    ("⚪", ""),
}

STATUS_MAP = {
    "active":      ("📝", "Активне"),
    "in_progress": ("🔄", "В роботі"),
    "done":        ("✅", "Виконано"),
    "archived":    ("📦", "Архів"),
}


def _label(text, css_classes=None, xalign=0):
    lbl = Gtk.Label(label=text, xalign=xalign)
    if css_classes:
        for c in css_classes:
            lbl.get_style_context().add_class(c)
    lbl.set_line_wrap(True)
    lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    return lbl


def _btn(label, css_class="btn-primary", on_click=None):
    btn = Gtk.Button(label=label)
    btn.get_style_context().add_class(css_class)
    if on_click:
        btn.connect("clicked", on_click)
    return btn


# ── Main Window ──────────────────────────────────────────────

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app, robot=None, scheduler=None):
        super().__init__(application=app, title="📒 AI Записник")
        self.set_default_size(1100, 720)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Set window icon
        import os
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)

        self.robot = robot
        self.scheduler = scheduler
        self.current_filter = {}
        self.categories = []

        # Main layout
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(hbox)

        # Sidebar
        self.sidebar = self._build_sidebar()
        hbox.pack_start(self.sidebar, False, False, 0)

        # Main content
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(self.main_vbox, True, True, 0)

        # Top bar
        self.topbar = self._build_topbar()
        self.main_vbox.pack_start(self.topbar, False, False, 0)

        # Stack for pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)
        self.main_vbox.pack_start(self.stack, True, True, 0)

        # Pages
        self.stack.add_named(self._build_dashboard(), "dashboard")
        self.stack.add_named(self._build_entries_page(), "entries")
        self.stack.add_named(self._build_settings_page(), "settings")

        self.show_all()
        self._refresh_all()

    # ── Sidebar ──────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.set_size_request(220, -1)
        sidebar.get_style_context().add_class("sidebar")

        # Logo
        logo = _label("  📒 AI Записник", ["header-title"])
        logo.set_margin_top(16)
        logo.set_margin_bottom(8)
        sidebar.pack_start(logo, False, False, 0)

        # Nav section
        sidebar.pack_start(_label("  НАВІГАЦІЯ", ["sidebar-label"]), False, False, 0)

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 Дашборд"),
            ("entries",   "📋 Всі записи"),
            ("settings",  "⚙️ Налаштування"),
        ]
        for key, text in nav_items:
            btn = Gtk.Button(label=text)
            btn.get_style_context().add_class("sidebar-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_halign(Gtk.Align.FILL)
            btn.connect("clicked", lambda b, k=key: self._switch_page(k))
            sidebar.pack_start(btn, False, False, 0)
            self.nav_buttons[key] = btn

        # Categories section
        sidebar.pack_start(_label("  КАТЕГОРІЇ", ["sidebar-label"]), False, False, 4)
        self.cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar.pack_start(self.cat_box, False, False, 0)

        add_cat_btn = Gtk.Button(label="  ＋ Додати категорію")
        add_cat_btn.get_style_context().add_class("sidebar-btn")
        add_cat_btn.set_relief(Gtk.ReliefStyle.NONE)
        add_cat_btn.set_halign(Gtk.Align.FILL)
        add_cat_btn.connect("clicked", self._on_add_category)
        sidebar.pack_start(add_cat_btn, False, False, 0)

        # Spacer
        sidebar.pack_start(Gtk.Label(), True, True, 0)

        # About button
        about_btn = Gtk.Button(label="  ℹ️ Про додаток")
        about_btn.get_style_context().add_class("sidebar-btn")
        about_btn.set_relief(Gtk.ReliefStyle.NONE)
        about_btn.set_halign(Gtk.Align.FILL)
        about_btn.connect("clicked", self._on_about)
        sidebar.pack_end(about_btn, False, False, 0)

        # Quick stats at bottom
        self.sidebar_stats = _label("", ["entry-meta"])
        self.sidebar_stats.set_margin_bottom(12)
        self.sidebar_stats.set_line_wrap(False)
        sidebar.pack_end(self.sidebar_stats, False, False, 0)

        return sidebar

    def _refresh_sidebar_categories(self):
        for child in self.cat_box.get_children():
            self.cat_box.remove(child)
        self.categories = storage.list_categories()
        for c in self.categories:
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn = Gtk.Button(label=f"{c['icon']} {c['name']}  ({c['entry_count']})")
            btn.get_style_context().add_class("sidebar-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_halign(Gtk.Align.FILL)
            cat_id = c["id"]
            btn.connect("clicked", lambda b, cid=cat_id: self._filter_by_category(cid))
            hbox.pack_start(btn, True, True, 0)

            # Edit/delete buttons
            edit_btn = Gtk.Button(label="✏")
            edit_btn.get_style_context().add_class("btn-icon")
            edit_btn.set_relief(Gtk.ReliefStyle.NONE)
            edit_btn.connect("clicked", lambda b, cid=cat_id: self._on_edit_category(cid))
            hbox.pack_start(edit_btn, False, False, 0)

            del_btn = Gtk.Button(label="🗑")
            del_btn.get_style_context().add_class("btn-icon")
            del_btn.set_relief(Gtk.ReliefStyle.NONE)
            del_btn.connect("clicked", lambda b, cid=cat_id: self._on_delete_category(cid))
            hbox.pack_start(del_btn, False, False, 0)

            self.cat_box.pack_start(hbox, False, False, 0)
        self.cat_box.show_all()

    def _switch_page(self, key):
        self.stack.set_visible_child_name(key)
        for k, btn in self.nav_buttons.items():
            ctx = btn.get_style_context()
            if k == key:
                ctx.add_class("active")
            else:
                ctx.remove_class("active")

    def _filter_by_category(self, cat_id):
        self.current_filter = {"category_id": cat_id}
        self._refresh_entries()
        self._switch_page("entries")

    # ── Top Bar ──────────────────────────────────────────────

    def _build_topbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.get_style_context().add_class("topbar")

        self.header_label = _label("📊 Дашборд", ["header-title"])
        bar.pack_start(self.header_label, False, False, 0)

        # Spacer
        bar.pack_start(Gtk.Label(), True, True, 0)

        # Search
        self.search_entry = Gtk.Entry()
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.set_placeholder_text("🔍 Пошук записів...")
        self.search_entry.set_size_request(280, -1)
        self.search_entry.connect("changed", self._on_search)
        bar.pack_start(self.search_entry, False, False, 0)

        # New entry button
        new_btn = _btn("＋ Новий запис", "btn-primary", self._on_new_entry)
        bar.pack_start(new_btn, False, False, 0)

        return bar

    # ── Dashboard Page ───────────────────────────────────────

    def _build_dashboard(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_margin_top(24)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        # Welcome header with robot image
        import os
        robot_img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "robot.png")
        if os.path.exists(robot_img_path):
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            header_box.set_valign(Gtk.Align.START)
            img = Gtk.Image.new_from_file(robot_img_path)
            img.set_pixel_size(80)
            header_box.pack_start(img, False, False, 0)
            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            text_box.set_valign(Gtk.Align.CENTER)
            text_box.pack_start(_label("🚀 Привіт! Я твій робот з реактивним ранцем", ["header-title"]), False, False, 0)
            text_box.pack_start(_label("Створюй нотатки, задачі та нагадування", ["entry-meta"]), False, False, 0)
            header_box.pack_start(text_box, True, True, 0)
            vbox.pack_start(header_box, False, False, 0)

        # Stats cards row
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.stat_cards = {}
        stat_items = [
            ("total",       "📋", "Всього"),
            ("active",      "📝", "Активних"),
            ("in_progress", "🔄", "В роботі"),
            ("done",        "✅", "Виконано"),
            ("overdue",     "⚠️", "Прострочено"),
        ]
        for key, icon, label in stat_items:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.get_style_context().add_class("stat-card")
            card.set_size_request(170, -1)
            lbl = _label(f"{icon} {label}", ["entry-meta"])
            val = _label("0", ["header-title"])
            card.pack_start(lbl, False, False, 0)
            card.pack_start(val, False, False, 0)
            stats_box.pack_start(card, False, False, 0)
            self.stat_cards[key] = val
        vbox.pack_start(stats_box, False, False, 0)

        # Recent entries section
        vbox.pack_start(_label("📋 Останні записи", ["header-title"]), False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.recent_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(self.recent_list)
        vbox.pack_start(scroll, True, True, 0)

        return vbox

    # ── Entries Page ─────────────────────────────────────────

    def _build_entries_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Filter bar
        filter_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        filter_bar.set_margin_top(12)
        filter_bar.set_margin_start(20)
        filter_bar.set_margin_end(20)
        filter_bar.set_margin_bottom(12)

        filter_bar.pack_start(_label("Фільтр:", ["entry-meta"]), False, False, 0)

        self.filter_status = Gtk.ComboBoxText()
        for val, label in [("", "Всі статуси"), ("active", "Активні"),
                           ("in_progress", "В роботі"), ("done", "Виконані"),
                           ("archived", "Архів")]:
            self.filter_status.append(val, label)
        self.filter_status.set_active(0)
        self.filter_status.connect("changed", self._on_filter_changed)
        filter_bar.pack_start(self.filter_status, False, False, 0)

        self.filter_priority = Gtk.ComboBoxText()
        for val, label in [("", "Всі пріоритети"), ("urgent", "🔴 Терміново"),
                           ("high", "🟠 Високий"), ("normal", "⚪ Звичайний"),
                           ("low", "⬇️ Низький")]:
            self.filter_priority.append(val, label)
        self.filter_priority.set_active(0)
        self.filter_priority.connect("changed", self._on_filter_changed)
        filter_bar.pack_start(self.filter_priority, False, False, 0)

        self.filter_type = Gtk.ComboBoxText()
        for val, label in [("", "Всі типи"), ("note", "📝 Нотатки"), ("task", "☑️ Задачі")]:
            self.filter_type.append(val, label)
        self.filter_type.set_active(0)
        self.filter_type.connect("changed", self._on_filter_changed)
        filter_bar.pack_start(self.filter_type, False, False, 0)

        # Clear filters
        clear_btn = _btn("✕ Очистити", "btn-secondary")
        clear_btn.connect("clicked", self._clear_filters)
        filter_bar.pack_start(clear_btn, False, False, 0)

        vbox.pack_start(filter_bar, False, False, 0)

        # Entries list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.entries_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.entries_list.set_margin_start(20)
        self.entries_list.set_margin_end(20)
        scroll.add(self.entries_list)
        vbox.pack_start(scroll, True, True, 0)

        return vbox

    # ── Settings Page ────────────────────────────────────────

    def _build_settings_page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_margin_top(24)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)
        vbox.set_margin_bottom(24)

        # Robot section
        vbox.pack_start(_label("🤖 Робот-помічник", ["header-title"]), False, False, 0)

        # Visibility
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Показати робота"), False, False, 0)
        self.robot_visible_sw = Gtk.Switch()
        self.robot_visible_sw.set_active(storage.get_setting("robot_visible", "1") == "1")
        self.robot_visible_sw.connect("state-set", self._on_robot_visible)
        row.pack_end(self.robot_visible_sw, False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Robot style
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Стиль робота"), False, False, 0)
        self.robot_style_combo = Gtk.ComboBoxText()
        for val, label in [("modern", "🤖 Сучасний"), ("round", "🔵 Круглий"), ("pixel", "👾 Піксельний")]:
            self.robot_style_combo.append(val, label)
        current_style = storage.get_setting("robot_style", "modern")
        self.robot_style_combo.set_active_id(current_style)
        self.robot_style_combo.connect("changed", self._on_robot_style)
        row.pack_end(self.robot_style_combo, False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Color
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Колір робота"), False, False, 0)
        self.robot_color_btn = Gtk.ColorButton()
        color_hex = storage.get_setting("robot_color", "#6366f1")
        h = color_hex.lstrip("#")
        rgba = Gdk.RGBA()
        rgba.red = int(h[0:2], 16) / 255
        rgba.green = int(h[2:4], 16) / 255
        rgba.blue = int(h[4:6], 16) / 255
        rgba.alpha = 1.0
        self.robot_color_btn.set_rgba(rgba)
        self.robot_color_btn.connect("color-set", self._on_robot_color)
        row.pack_end(self.robot_color_btn, False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Size
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Розмір робота"), False, False, 0)
        self.robot_size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 30, 120, 5)
        self.robot_size_scale.set_value(int(storage.get_setting("robot_size", "60")))
        self.robot_size_scale.set_size_request(200, -1)
        self.robot_size_scale.connect("value-changed", self._on_robot_size)
        row.pack_end(self.robot_size_scale, False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Speed
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Швидкість руху"), False, False, 0)
        self.robot_speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 5, 0.5)
        self.robot_speed_scale.set_value(float(storage.get_setting("robot_speed", "2")))
        self.robot_speed_scale.set_size_request(200, -1)
        self.robot_speed_scale.connect("value-changed", self._on_robot_speed)
        row.pack_end(self.robot_speed_scale, False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Test bubble
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Тестова думка робота"), False, False, 0)
        test_btn = _btn("💬 Показати думку", "btn-secondary")
        test_btn.connect("clicked", self._on_test_bubble)
        row.pack_end(test_btn, False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Telegram section
        vbox.pack_start(_label("🤖 Telegram бот", ["header-title"]), False, False, 8)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label("Статус бота:"), False, False, 0)
        tg_status = "✅ Активний" if storage.get_setting("telegram_token") else "❌ Не налаштовано"
        row.pack_start(_label(tg_status), False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        # Data section
        vbox.pack_start(_label("💾 Дані", ["header-title"]), False, False, 8)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.pack_start(_label(f"База даних: {storage.DB_PATH}"), False, False, 0)
        vbox.pack_start(self._settings_card(row), False, False, 0)

        scroll.add(vbox)
        return scroll

    @staticmethod
    def _settings_card(content_widget):
        card = Gtk.Box()
        card.get_style_context().add_class("card")
        card.set_margin_bottom(4)
        content_widget.set_margin_top(4)
        content_widget.set_margin_bottom(4)
        content_widget.set_margin_start(8)
        content_widget.set_margin_end(8)
        card.add(content_widget)
        return card

    # ── Data Refresh ─────────────────────────────────────────

    def _refresh_all(self):
        self._refresh_stats()
        self._refresh_sidebar_categories()
        self._refresh_entries()
        self._refresh_recent()
        self._refresh_sidebar_stats()

    def _refresh_stats(self):
        s = storage.get_stats()
        for key in ("total", "active", "in_progress", "done", "overdue"):
            self.stat_cards[key].set_text(str(s.get(key, 0)))

    def _refresh_sidebar_stats(self):
        s = storage.get_stats()
        self.sidebar_stats.set_markup(
            f'<span size="small" foreground="#94a3b8">'
            f'📝 {s["active"]}  🔄 {s["in_progress"]}  ✅ {s["done"]}'
            f'</span>'
        )

    def _refresh_recent(self):
        for child in self.recent_list.get_children():
            self.recent_list.remove(child)
        entries = storage.list_entries(limit=8)
        if not entries:
            self.recent_list.pack_start(_label("  Записів поки немає", ["entry-meta"]), False, False, 8)
        else:
            for e in entries:
                self.recent_list.pack_start(self._entry_row(e), False, False, 0)
        self.recent_list.show_all()

    def _refresh_entries(self):
        for child in self.entries_list.get_children():
            self.entries_list.remove(child)
        entries = storage.list_entries(**self.current_filter)
        if not entries:
            self.entries_list.pack_start(
                _label("  Записів не знайдено", ["entry-meta"]), False, False, 16
            )
        else:
            for e in entries:
                self.entries_list.pack_start(self._entry_card(e), False, False, 0)
        self.entries_list.show_all()

    # ── Entry Widgets ────────────────────────────────────────

    def _entry_row(self, e):
        """Compact row for dashboard."""
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.get_style_context().add_class("card")
        if e["status"] == "done":
            hbox.get_style_context().add_class("card-done")
        if e["pinned"]:
            hbox.get_style_context().add_class("card-pinned")

        # Status dot
        status_icon = STATUS_MAP.get(e["status"], ("📝", ""))[0]
        hbox.pack_start(_label(status_icon), False, False, 0)

        # Priority
        prio_icon = PRIORITY_MAP.get(e["priority"], ("", ""))[0]
        if prio_icon:
            hbox.pack_start(_label(prio_icon), False, False, 0)

        # Title
        title = e["title"]
        if len(title) > 50:
            title = title[:47] + "..."
        hbox.pack_start(_label(title, ["entry-title"]), True, True, 0)

        # Category
        if e.get("category_name"):
            hbox.pack_start(_label(f'{e.get("category_icon", "")} {e["category_name"]}',
                                   ["entry-meta"]), False, False, 0)

        # Date
        hbox.pack_start(_label(e["created_at"][:16], ["entry-meta"]), False, False, 0)

        # Actions
        edit_btn = Gtk.Button(label="✏")
        edit_btn.get_style_context().add_class("btn-icon")
        edit_btn.set_relief(Gtk.ReliefStyle.NONE)
        edit_btn.connect("clicked", lambda b, eid=e["id"]: self._on_edit_entry(eid))
        hbox.pack_start(edit_btn, False, False, 0)

        if e["status"] != "done":
            done_btn = Gtk.Button(label="✅")
            done_btn.get_style_context().add_class("btn-icon")
            done_btn.set_relief(Gtk.ReliefStyle.NONE)
            done_btn.connect("clicked", lambda b, eid=e["id"]: self._on_quick_done(eid))
            hbox.pack_start(done_btn, False, False, 0)

        return hbox

    def _entry_card(self, e):
        """Full card for entries page."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")
        if e["status"] == "done":
            card.get_style_context().add_class("card-done")
        if e["pinned"]:
            card.get_style_context().add_class("card-pinned")

        # Top row
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_icon, status_text = STATUS_MAP.get(e["status"], ("📝", ""))
        top.pack_start(_label(f"{status_icon} {status_text}", ["badge"]), False, False, 0)

        type_text = "☑️ Задача" if e["entry_type"] == "task" else "📝 Нотатка"
        top.pack_start(_label(type_text, ["badge"]), False, False, 0)

        prio_icon, prio_cls = PRIORITY_MAP.get(e["priority"], ("", ""))
        if prio_icon:
            top.pack_start(_label(prio_icon, [prio_cls] if prio_cls else []), False, False, 0)

        if e.get("category_name"):
            top.pack_start(_label(f'{e.get("category_icon", "")} {e["category_name"]}',
                                  ["badge"]), False, False, 0)

        # Spacer
        top.pack_start(Gtk.Label(), True, True, 0)

        # Actions
        if e["status"] != "done":
            done_btn = Gtk.Button(label="✅ Виконано")
            done_btn.get_style_context().add_class("btn-icon")
            done_btn.set_relief(Gtk.ReliefStyle.NONE)
            done_btn.connect("clicked", lambda b, eid=e["id"]: self._on_quick_done(eid))
            top.pack_start(done_btn, False, False, 0)

        edit_btn = Gtk.Button(label="✏ Редагувати")
        edit_btn.get_style_context().add_class("btn-icon")
        edit_btn.set_relief(Gtk.ReliefStyle.NONE)
        edit_btn.connect("clicked", lambda b, eid=e["id"]: self._on_edit_entry(eid))
        top.pack_start(edit_btn, False, False, 0)

        del_btn = Gtk.Button(label="🗑")
        del_btn.get_style_context().add_class("btn-icon")
        del_btn.set_relief(Gtk.ReliefStyle.NONE)
        del_btn.connect("clicked", lambda b, eid=e["id"]: self._on_delete_entry(eid))
        top.pack_start(del_btn, False, False, 0)

        card.pack_start(top, False, False, 0)

        # Title
        card.pack_start(_label(e["title"], ["entry-title"]), False, False, 0)

        # Content preview
        if e.get("content"):
            content = e["content"]
            if len(content) > 150:
                content = content[:147] + "..."
            card.pack_start(_label(content, ["entry-content"]), False, False, 0)

        # Tags
        if e.get("tags"):
            tags_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            for t in e["tags"]:
                tags_box.pack_start(_label(f"#{t}", ["badge"]), False, False, 0)
            card.pack_start(tags_box, False, False, 0)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        footer.pack_start(_label(f"📅 {e['created_at'][:16]}", ["entry-meta"]), False, False, 0)
        if e.get("due_date"):
            is_overdue = e["due_date"] < datetime.now().strftime("%Y-%m-%d") and e["status"] not in ("done", "archived")
            cls = "badge-red" if is_overdue else "badge-orange"
            footer.pack_start(_label(f"⏰ {e['due_date']}", [cls]), False, False, 0)
        if e.get("remind_at"):
            footer.pack_start(_label(f"🔔 {e['remind_at'][:16]}", ["badge"]), False, False, 0)
        card.pack_start(footer, False, False, 0)

        return card

    # ── Entry Dialog ─────────────────────────────────────────

    def _show_entry_dialog(self, entry=None):
        dlg = Gtk.Dialog(
            title="Редагувати запис" if entry else "Новий запис",
            parent=self,
            modal=True,
        )
        dlg.add_button("Скасувать", Gtk.ResponseType.CANCEL)
        dlg.add_button("Зберегти", Gtk.ResponseType.OK)
        dlg.set_default_size(520, 560)
        dlg.set_resizable(False)

        content = dlg.get_content_area()
        content.set_spacing(12)
        content.set_margin_top(16)
        content.set_margin_start(20)
        content.set_margin_end(20)

        # Title
        content.pack_start(_label("Заголовок *"), False, False, 0)
        title_entry = Gtk.Entry()
        title_entry.set_text(entry["title"] if entry else "")
        title_entry.set_placeholder_text("Введіть заголовок...")
        content.pack_start(title_entry, False, False, 0)

        # Type + Priority row
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.pack_start(_label("Тип:"), False, False, 0)
        type_combo = Gtk.ComboBoxText()
        type_combo.append("note", "📝 Нотатка")
        type_combo.append("task", "☑️ Задача")
        type_combo.set_active_id(entry["entry_type"] if entry else "note")
        hbox.pack_start(type_combo, True, True, 0)

        hbox.pack_start(_label("Пріоритет:"), False, False, 0)
        prio_combo = Gtk.ComboBoxText()
        prio_combo.append("normal", "⚪ Звичайний")
        prio_combo.append("low", "⬇️ Низький")
        prio_combo.append("high", "🟠 Високий")
        prio_combo.append("urgent", "🔴 Терміново")
        prio_combo.set_active_id(entry["priority"] if entry else "normal")
        hbox.pack_start(prio_combo, True, True, 0)
        content.pack_start(hbox, False, False, 0)

        # Content
        content.pack_start(_label("Зміст"), False, False, 0)
        content_view = Gtk.TextView()
        content_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        content_view.set_size_request(-1, 100)
        buf = content_view.get_buffer()
        if entry and entry.get("content"):
            buf.set_text(entry["content"])
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(-1, 100)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(content_view)
        content.pack_start(scroll, False, False, 0)

        # Category + Status row
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox2.pack_start(_label("Категорія:"), False, False, 0)
        cat_combo = Gtk.ComboBoxText()
        cat_combo.append("", "Без категорії")
        for c in self.categories:
            cat_combo.append(str(c["id"]), f"{c['icon']} {c['name']}")
        cat_combo.set_active_id(str(entry["category_id"]) if entry and entry.get("category_id") else "")
        hbox2.pack_start(cat_combo, True, True, 0)

        hbox2.pack_start(_label("Статус:"), False, False, 0)
        status_combo = Gtk.ComboBoxText()
        for val, label in [("active", "📝 Активний"), ("in_progress", "🔄 В роботі"),
                           ("done", "✅ Виконано"), ("archived", "📦 Архів")]:
            status_combo.append(val, label)
        status_combo.set_active_id(entry["status"] if entry else "active")
        hbox2.pack_start(status_combo, True, True, 0)
        content.pack_start(hbox2, False, False, 0)

        # Due date + Remind at — with calendar/time pickers
        hbox3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        # Due date picker
        hbox3.pack_start(_label("Дата виконання:"), False, False, 0)
        due_cal_btn = Gtk.Button(label="📅 Обрати дату")
        due_cal_btn.get_style_context().add_class("sidebar-btn")
        self._selected_due_date = entry.get("due_date") if entry and entry.get("due_date") else None
        if self._selected_due_date:
            due_cal_btn.set_label(f"📅 {self._selected_due_date}")
        due_cal_btn.connect("clicked", lambda b: self._pick_date(b, "_selected_due_date"))
        hbox3.pack_start(due_cal_btn, True, True, 0)

        # Remind date+time picker
        hbox3.pack_start(_label("Нагадати:"), False, False, 0)
        remind_cal_btn = Gtk.Button(label="📅 Обрати дату і час")
        remind_cal_btn.get_style_context().add_class("sidebar-btn")
        self._selected_remind_date = None
        self._selected_remind_hour = 9
        self._selected_remind_minute = 0
        if entry and entry.get("remind_at"):
            parts = entry["remind_at"].split()
            if len(parts) == 2:
                self._selected_remind_date = parts[0]
                time_parts = parts[1].split(":")
                if len(time_parts) == 2:
                    self._selected_remind_hour = int(time_parts[0])
                    self._selected_remind_minute = int(time_parts[1])
                remind_cal_btn.set_label(f"📅 {self._selected_remind_date} {self._selected_remind_hour:02d}:{self._selected_remind_minute:02d}")
        remind_cal_btn.connect("clicked", lambda b: self._pick_datetime(b))
        hbox3.pack_start(remind_cal_btn, True, True, 0)

        content.pack_start(hbox3, False, False, 0)

        # Tags
        content.pack_start(_label("Теги (через кому)"), False, False, 0)
        tags_entry = Gtk.Entry()
        tags_entry.set_placeholder_text("робота, термінове, ідея...")
        if entry and entry.get("tags"):
            tags_entry.set_text(", ".join(entry["tags"]))
        content.pack_start(tags_entry, False, False, 0)

        # Pinned
        pinned_cb = Gtk.CheckButton(label="📌 Закріпити запис")
        if entry:
            pinned_cb.set_active(bool(entry.get("pinned")))
        content.pack_start(pinned_cb, False, False, 0)

        dlg.show_all()
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            title = title_entry.get_text().strip()
            if not title:
                dlg.destroy()
                return

            start_iter, end_iter = buf.get_bounds()
            content_text = buf.get_text(start_iter, end_iter, True)

            cat_id = cat_combo.get_active_id()
            due_date_val = self._selected_due_date
            remind_at_val = None
            if self._selected_remind_date:
                remind_at_val = f"{self._selected_remind_date} {self._selected_remind_hour:02d}:{self._selected_remind_minute:02d}"
            data = {
                "title": title,
                "content": content_text,
                "entry_type": type_combo.get_active_id(),
                "priority": prio_combo.get_active_id(),
                "status": status_combo.get_active_id(),
                "category_id": int(cat_id) if cat_id else None,
                "due_date": due_date_val,
                "remind_at": remind_at_val,
                "pinned": 1 if pinned_cb.get_active() else 0,
                "tags": [t.strip() for t in tags_entry.get_text().split(",") if t.strip()],
            }

            if entry:
                storage.update_entry(entry["id"], **data)
            else:
                storage.create_entry(**data)

            self._refresh_all()

        dlg.destroy()

    # ── Event Handlers ───────────────────────────────────────

    def _on_new_entry(self, btn):
        self._show_entry_dialog()

    def _on_edit_entry(self, entry_id):
        entry = storage.get_entry(entry_id)
        if entry:
            self._show_entry_dialog(entry)

    def _on_quick_done(self, entry_id):
        storage.update_entry(entry_id, status="done")
        if self.scheduler:
            self.scheduler.dismiss(entry_id)
        self._refresh_all()

    def _on_delete_entry(self, entry_id):
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Видалити запис?",
        )
        dlg.format_secondary_text("Цю дію не можна скасувати.")
        resp = dlg.run()
        dlg.destroy()
        if resp == Gtk.ResponseType.YES:
            storage.delete_entry(entry_id)
            self._refresh_all()

    def _on_search(self, entry):
        text = entry.get_text().strip()
        if text:
            self.current_filter = {"search": text}
        else:
            self.current_filter = {}
        self._refresh_entries()

    def _on_filter_changed(self, combo):
        f = {}
        s = self.filter_status.get_active_id()
        p = self.filter_priority.get_active_id()
        t = self.filter_type.get_active_id()
        if s:
            f["status"] = s
        if p:
            f["priority"] = p
        if t:
            f["entry_type"] = t
        self.current_filter = f
        self._refresh_entries()

    def _clear_filters(self, btn):
        self.current_filter = {}
        self.filter_status.set_active(0)
        self.filter_priority.set_active(0)
        self.filter_type.set_active(0)
        self.search_entry.set_text("")
        self._refresh_entries()

    # ── Category Handlers ────────────────────────────────────

    def _on_add_category(self, btn):
        self._show_category_dialog()

    def _pick_date(self, btn, attr_name):
        """Open a calendar dialog to pick a date."""
        dlg = Gtk.Dialog(title="Оберіть дату", parent=self, modal=True)
        dlg.add_button("Скасувати", Gtk.ResponseType.CANCEL)
        dlg.add_button("OK", Gtk.ResponseType.OK)
        dlg.set_default_size(300, 300)

        cal = Gtk.Calendar()
        cal.set_display_options(
            Gtk.CalendarDisplayOptions.SHOW_HEADING |
            Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES |
            Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS
        )
        dlg.get_content_area().pack_start(cal, True, True, 8)
        dlg.show_all()

        if dlg.run() == Gtk.ResponseType.OK:
            y, m, d = cal.get_date()
            m += 1  # Calendar months are 0-indexed
            date_str = f"{y:04d}-{m:02d}-{d:02d}"
            setattr(self, attr_name, date_str)
            btn.set_label(f"📅 {date_str}")
        dlg.destroy()

    def _pick_datetime(self, btn):
        """Open a calendar + time dialog to pick date and time."""
        dlg = Gtk.Dialog(title="Оберіть дату та час нагадування", parent=self, modal=True)
        dlg.add_button("Скасувати", Gtk.ResponseType.CANCEL)
        dlg.add_button("Очистити", Gtk.ResponseType.REJECT)
        dlg.add_button("OK", Gtk.ResponseType.OK)
        dlg.set_default_size(350, 400)

        content = dlg.get_content_area()
        content.set_spacing(8)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)

        # Calendar
        content.pack_start(_label("📅 Дата:"), False, False, 0)
        cal = Gtk.Calendar()
        cal.set_display_options(
            Gtk.CalendarDisplayOptions.SHOW_HEADING |
            Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES |
            Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS
        )
        # Pre-select if we have a saved date
        if self._selected_remind_date:
            try:
                parts = self._selected_remind_date.split("-")
                cal.select_month(int(parts[1]) - 1, int(parts[0]))
                cal.select_day(int(parts[2]))
            except (ValueError, IndexError):
                pass
        content.pack_start(cal, True, True, 0)

        # Time picker
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        time_box.pack_start(_label("🕐 Час:"), False, False, 0)

        hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        hour_spin.set_value(self._selected_remind_hour)
        hour_spin.set_wrap(True)
        time_box.pack_start(hour_spin, False, False, 0)
        time_box.pack_start(_label(":"), False, False, 0)

        minute_spin = Gtk.SpinButton.new_with_range(0, 59, 5)
        minute_spin.set_value(self._selected_remind_minute)
        minute_spin.set_wrap(True)
        time_box.pack_start(minute_spin, False, False, 0)

        # Quick time buttons
        quick_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for label, h, m in [("9:00", 9, 0), ("12:00", 12, 0), ("15:00", 15, 0),
                             ("18:00", 18, 0), ("21:00", 21, 0)]:
            qb = Gtk.Button(label=label)
            qb.set_relief(Gtk.ReliefStyle.NONE)
            qb.connect("clicked", lambda b, hh=h, mm=m: (hour_spin.set_value(hh), minute_spin.set_value(mm)))
            quick_box.pack_start(qb, True, True, 0)

        content.pack_start(time_box, False, False, 0)
        content.pack_start(quick_box, False, False, 0)

        dlg.show_all()
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            y, mo, d = cal.get_date()
            mo += 1
            date_str = f"{y:04d}-{mo:02d}-{d:02d}"
            h = int(hour_spin.get_value())
            mi = int(minute_spin.get_value())
            self._selected_remind_date = date_str
            self._selected_remind_hour = h
            self._selected_remind_minute = mi
            btn.set_label(f"📅 {date_str} {h:02d}:{mi:02d}")
        elif response == Gtk.ResponseType.REJECT:
            self._selected_remind_date = None
            self._selected_remind_hour = 9
            self._selected_remind_minute = 0
            btn.set_label("📅 Обрати дату і час")

        dlg.destroy()

    def _on_about(self, btn):
        import os
        dlg = Gtk.AboutDialog(parent=self, modal=True)
        dlg.set_program_name("AI Записник")
        dlg.set_version("1.0.0")
        dlg.set_comments("Настільний додаток з літаючим роботом-помічником")
        dlg.set_website("https://github.com/Dima12348/ai-notebook")
        dlg.set_website_label("GitHub")
        dlg.set_license_type(Gtk.License.MIT_X11)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 128, 128)
                dlg.set_logo(pixbuf)
            except Exception:
                pass
        dlg.run()
        dlg.destroy()

    def _on_edit_category(self, cat_id):
        cat = next((c for c in self.categories if c["id"] == cat_id), None)
        if cat:
            self._show_category_dialog(cat)

    def _show_category_dialog(self, cat=None):
        dlg = Gtk.Dialog(
            title="Редагувати категорію" if cat else "Нова категорія",
            parent=self, modal=True,
        )
        dlg.add_button("Скасувать", Gtk.ResponseType.CANCEL)
        dlg.add_button("Зберегти", Gtk.ResponseType.OK)
        dlg.set_default_size(360, 200)

        content = dlg.get_content_area()
        content.set_spacing(10)
        content.set_margin_top(12)
        content.set_margin_start(16)
        content.set_margin_end(16)

        content.pack_start(_label("Назва *"), False, False, 0)
        name_entry = Gtk.Entry()
        name_entry.set_text(cat["name"] if cat else "")
        content.pack_start(name_entry, False, False, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.pack_start(_label("Іконка:"), False, False, 0)
        icon_entry = Gtk.Entry()
        icon_entry.set_text(cat["icon"] if cat else "📁")
        icon_entry.set_width_chars(4)
        icon_entry.set_max_width_chars(4)
        hbox.pack_start(icon_entry, False, False, 0)

        hbox.pack_start(_label("Колір:"), False, False, 0)
        color_btn = Gtk.ColorButton()
        if cat:
            h = cat["color"].lstrip("#")
            rgba = Gdk.RGBA()
            rgba.red = int(h[0:2], 16) / 255
            rgba.green = int(h[2:4], 16) / 255
            rgba.blue = int(h[4:6], 16) / 255
            rgba.alpha = 1.0
            color_btn.set_rgba(rgba)
        hbox.pack_start(color_btn, False, False, 0)
        content.pack_start(hbox, False, False, 0)

        dlg.show_all()
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            if name:
                rgba = color_btn.get_rgba()
                color = "#{:02x}{:02x}{:02x}".format(
                    int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
                )
                icon = icon_entry.get_text() or "📁"
                if cat:
                    storage.update_category(cat["id"], name=name, color=color, icon=icon)
                else:
                    storage.create_category(name, color, icon)
                self._refresh_all()

        dlg.destroy()

    def _on_delete_category(self, cat_id):
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Видалити категорію?",
        )
        dlg.format_secondary_text("Записи в ній збережуться.")
        resp = dlg.run()
        dlg.destroy()
        if resp == Gtk.ResponseType.YES:
            storage.delete_category(cat_id)
            self._refresh_all()

    # ── Robot Settings Handlers ──────────────────────────────

    def _on_robot_visible(self, sw, state):
        storage.set_setting("robot_visible", "1" if state else "0")
        if self.robot:
            if state:
                self.robot.show_all()
            else:
                self.robot.hide()

    def _on_robot_style(self, combo):
        style = combo.get_active_id()
        storage.set_setting("robot_style", style)
        if self.robot:
            self.robot.set_config(style=style)

    def _on_robot_color(self, btn):
        rgba = btn.get_rgba()
        color = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        )
        storage.set_setting("robot_color", color)
        if self.robot:
            self.robot.set_config(color_hex=color)

    def _on_robot_size(self, scale):
        val = int(scale.get_value())
        storage.set_setting("robot_size", str(val))
        if self.robot:
            self.robot.set_config(size=val)

    def _on_robot_speed(self, scale):
        val = scale.get_value()
        storage.set_setting("robot_speed", str(val))
        if self.robot:
            self.robot.set_config(speed=val)

    def _on_test_bubble(self, btn):
        if self.robot:
            self.robot.show_bubble("Привіт! Я твій робот-помічник! 🤖")
