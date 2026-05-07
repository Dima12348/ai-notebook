"""Popup menu for robot — view, add, delete entries from a floating panel."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from . import storage


class RobotPopup(Gtk.Window):
    """Floating popup window that appears when robot is clicked."""

    def __init__(self, on_open_main=None):
        super().__init__(Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_default_size(340, 480)
        self.set_position(Gtk.WindowPosition.MOUSE)
        self.get_style_context().add_class("robot-popup")

        self.on_open_main = on_open_main
        self._edit_dlg = None

        # Apply popup CSS
        self._apply_popup_css()

        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(12)
        header.set_margin_end(8)
        header.set_margin_top(10)
        header.set_margin_bottom(8)

        title = Gtk.Label(label="🤖 Robot Assistant")
        title.get_style_context().add_class("popup-title")
        header.pack_start(title, True, True, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.get_style_context().add_class("popup-close")
        close_btn.connect("clicked", lambda b: self.hide())
        header.pack_end(close_btn, False, False, 0)
        vbox.pack_start(header, False, False, 0)

        # Quick add bar
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_box.set_margin_start(12)
        add_box.set_margin_end(12)
        add_box.set_margin_bottom(8)

        self.quick_entry = Gtk.Entry()
        self.quick_entry.set_placeholder_text("✍️ Quick note...")
        self.quick_entry.connect("activate", self._on_quick_add)
        add_box.pack_start(self.quick_entry, True, True, 0)

        add_btn = Gtk.Button(label="➕")
        add_btn.get_style_context().add_class("popup-add-btn")
        add_btn.connect("clicked", self._on_quick_add)
        add_box.pack_start(add_btn, False, False, 0)
        vbox.pack_start(add_box, False, False, 0)

        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        # Filter buttons
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        filter_box.set_margin_start(12)
        filter_box.set_margin_end(12)
        filter_box.set_margin_top(8)
        filter_box.set_margin_bottom(6)

        self.filter_buttons = {}
        for fid, label in [("all", "📋 All"), ("active", "📝 Active"),
                            ("in_progress", "🔄 In Progress"), ("done", "✅ Done")]:
            btn = Gtk.ToggleButton(label=label)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("popup-filter")
            btn.connect("toggled", self._on_filter, fid)
            filter_box.pack_start(btn, True, True, 0)
            self.filter_buttons[fid] = btn
        self.filter_buttons["all"].set_active(True)
        vbox.pack_start(filter_box, False, False, 0)

        # Entries list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.entries_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll.add(self.entries_box)
        vbox.pack_start(scroll, True, True, 0)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.set_margin_start(12)
        footer.set_margin_end(12)
        footer.set_margin_top(8)
        footer.set_margin_bottom(10)

        self.count_label = Gtk.Label(label="")
        self.count_label.get_style_context().add_class("popup-meta")
        footer.pack_start(self.count_label, True, True, 0)

        open_btn = Gtk.Button(label="📂 Open App")
        open_btn.get_style_context().add_class("popup-open-btn")
        open_btn.connect("clicked", lambda b: self._open_main())
        footer.pack_end(open_btn, False, False, 0)
        vbox.pack_end(footer, False, False, 0)

        # Current filter
        self.current_filter = "all"

        # Load entries
        self.refresh()

        # Auto-hide on focus out
        self.connect("focus-out-event", self._on_focus_out)

    def _apply_popup_css(self):
        css = b"""
        .robot-popup {
            background-color: #0f1117;
            border: 1px solid #2a2d3a;
            border-radius: 12px;
        }
        .popup-title {
            font-size: 15px;
            font-weight: bold;
            color: #e2e8f0;
        }
        .popup-close {
            color: #64748b;
            font-size: 16px;
            min-width: 28px;
            min-height: 28px;
            padding: 0;
        }
        .popup-close:hover {
            color: #ef4444;
        }
        .popup-meta {
            color: #64748b;
            font-size: 11px;
        }
        .popup-filter {
            background: transparent;
            color: #94a3b8;
            border: 1px solid #2a2d3a;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
        }
        .popup-filter:checked {
            background: #6366f1;
            color: white;
            border-color: #6366f1;
        }
        .popup-add-btn {
            background: #6366f1;
            color: white;
            border-radius: 6px;
            min-width: 36px;
            font-size: 14px;
        }
        .popup-open-btn {
            background: #1e2030;
            color: #94a3b8;
            border: 1px solid #2a2d3a;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
        }
        .popup-open-btn:hover {
            background: #6366f1;
            color: white;
        }
        .entry-row {
            background: #1a1d27;
            border-radius: 8px;
            padding: 8px;
            margin-left: 8px;
            margin-right: 8px;
        }
        .entry-row:hover {
            background: #222633;
        }
        .entry-title {
            color: #e2e8f0;
            font-size: 13px;
            font-weight: 600;
        }
        .entry-sub {
            color: #64748b;
            font-size: 11px;
        }
        .entry-del-btn {
            color: #475569;
            font-size: 12px;
            min-width: 24px;
            min-height: 24px;
            padding: 0;
        }
        .entry-del-btn:hover {
            color: #ef4444;
        }
        .entry-edit-btn {
            color: #475569;
            font-size: 12px;
            min-width: 24px;
            min-height: 24px;
            padding: 0;
        }
        .entry-edit-btn:hover {
            color: #6366f1;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def refresh(self):
        """Reload entries list."""
        for child in self.entries_box.get_children():
            self.entries_box.remove(child)

        entries = storage.list_entries()
        if self.current_filter != "all":
            entries = [e for e in entries if e["status"] == self.current_filter]

        # Sort: pinned first, then by date
        entries.sort(key=lambda e: (not e.get("pinned"), e.get("created_at", "")), reverse=False)
        entries.sort(key=lambda e: e.get("pinned", 0), reverse=True)

        for entry in entries[:50]:  # limit to 50
            row = self._build_entry_row(entry)
            self.entries_box.pack_start(row, False, False, 0)

        self.count_label.set_text(f"📋 {len(entries)} entries")
        self.entries_box.show_all()

    def _build_entry_row(self, entry):
        """Build a compact row for one entry."""
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.get_style_context().add_class("entry-row")

        # Priority indicator
        prio_icons = {"high": "🟠", "normal": "⚪", "low": "⬇️"}
        prio = Gtk.Label(label=prio_icons.get(entry.get("priority", "normal"), "⚪"))
        hbox.pack_start(prio, False, False, 0)

        # Title + meta
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        title_text = entry.get("title", "Untitled")
        if entry.get("pinned"):
            title_text = "📌 " + title_text
        title = Gtk.Label(label=title_text)
        title.get_style_context().add_class("entry-title")
        title.set_xalign(0)
        title.set_ellipsize(3)  # Pango.EllipsizeMode.END
        vbox.pack_start(title, False, False, 0)

        # Status + category
        status_icons = {"active": "📝", "in_progress": "🔄", "done": "✅", "archived": "📦"}
        status = status_icons.get(entry.get("status", "active"), "📝")
        cat_name = entry.get("category_name", "")
        meta = f"{status}"
        if cat_name:
            meta += f" · {cat_name}"
        if entry.get("due_date"):
            meta += f" · 📅 {entry['due_date']}"
        sub = Gtk.Label(label=meta)
        sub.get_style_context().add_class("entry-sub")
        sub.set_xalign(0)
        vbox.pack_start(sub, False, False, 0)

        hbox.pack_start(vbox, True, True, 0)

        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        edit_btn = Gtk.Button(label="✏️")
        edit_btn.set_relief(Gtk.ReliefStyle.NONE)
        edit_btn.get_style_context().add_class("entry-edit-btn")
        edit_btn.connect("clicked", lambda b, eid=entry["id"]: self._on_edit(eid))
        btn_box.pack_start(edit_btn, False, False, 0)

        del_btn = Gtk.Button(label="🗑️")
        del_btn.set_relief(Gtk.ReliefStyle.NONE)
        del_btn.get_style_context().add_class("entry-del-btn")
        del_btn.connect("clicked", lambda b, eid=entry["id"]: self._on_delete(eid))
        btn_box.pack_start(del_btn, False, False, 0)

        hbox.pack_end(btn_box, False, False, 0)

        # Click to open in main app
        event_box = Gtk.EventBox()
        event_box.add(hbox)
        event_box.connect("button-press-event", lambda w, e, eid=entry["id"]: self._on_entry_click(eid, e))
        event_box.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        return event_box

    def _on_entry_click(self, entry_id, event):
        """Open entry in main app on click (but not on button clicks)."""
        if event.button == 1 and self.on_open_main:
            self.on_open_main("edit", entry_id)
            self.hide()

    def _on_quick_add(self, widget):
        """Quick add entry from text field."""
        text = self.quick_entry.get_text().strip()
        if not text:
            return
        storage.create_entry(
            title=text,
            content="",
            entry_type="note",
            priority="normal",
            status="active",
        )
        self.quick_entry.set_text("")
        self.refresh()

    def _on_filter(self, btn, filter_id):
        """Toggle filter buttons."""
        if not btn.get_active():
            btn.set_active(True)
            return
        for fid, b in self.filter_buttons.items():
            if fid != filter_id:
                b.set_active(False)
        self.current_filter = filter_id
        if hasattr(self, 'entries_box') and self.entries_box:
            self.refresh()

    def _on_delete(self, entry_id):
        """Delete entry with confirmation."""
        dlg = Gtk.MessageDialog(
            parent=self, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete entry?",
        )
        dlg.format_secondary_text("This action cannot be undone.")
        if dlg.run() == Gtk.ResponseType.YES:
            storage.delete_entry(entry_id)
            self.refresh()
        dlg.destroy()

    def _on_edit(self, entry_id):
        """Open entry for editing in main app."""
        if self.on_open_main:
            self.on_open_main("edit", entry_id)
            self.hide()

    def _open_main(self):
        """Open main application window."""
        if self.on_open_main:
            self.on_open_main("show", None)
            self.hide()

    def _on_focus_out(self, widget, event):
        """Hide popup when focus is lost (with small delay)."""
        GLib.timeout_add(350, self._check_focus)
        return False

    def _check_focus(self):
        """Check if we still have focus, hide if not."""
        if self.is_visible() and not self.has_toplevel_focus():
            # Also check if the robot overlay grabbed focus
            # Don't hide if mouse is over the popup
            display = Gdk.Display.get_default()
            seat = display.get_default_seat()
            pointer = seat.get_pointer()
            if pointer:
                win, x, y = pointer.get_position()
                # Get popup window bounds
                pop_win = self.get_window()
                if pop_win and win == pop_win:
                    return False
            self.hide()
        return False
