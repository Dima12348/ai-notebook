#!/usr/bin/env python3
"""AI Notebook — Desktop app with flying robot assistant."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from app import storage
from app.gui import MainWindow, apply_css
from app.robot import RobotOverlay
from app.robot_menu import RobotPopup
from app.scheduler import Scheduler


class NotebookApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="ua.dima.ai-notebook")
        self.robot = None
        self.scheduler = None
        self.win = None
        self.popup = None

    def do_activate(self):
        # Init database
        storage.init_db()

        # Apply dark theme
        apply_css()

        # Set app icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            Gtk.Window.set_default_icon_from_file(icon_path)

        # Settings
        settings = storage.get_all_settings()

        # Create flying robot overlay
        self.robot = RobotOverlay(on_click_callback=self._on_robot_click)
        self.robot.set_config(
            color_hex=settings.get("robot_color", "#6366f1"),
            size=settings.get("robot_size", "60"),
            speed=settings.get("robot_speed", "2"),
            style=settings.get("robot_style", "modern"),
        )
        if settings.get("robot_visible", "1") == "1":
            self.robot.show_all()

        # Create robot popup menu
        self.popup = RobotPopup(on_open_main=self._on_popup_action)

        # Create main window
        self.win = MainWindow(self, robot=self.robot, scheduler=self.scheduler)

        # Start scheduler
        self.scheduler = Scheduler(robot=self.robot)
        self.scheduler.start()

    def _on_robot_click(self, action):
        if action == "menu":
            if self.popup and self.popup.is_visible():
                self.popup.hide()
            elif self.popup:
                self.popup.refresh()
                self.popup.show_all()
                self.popup.present()

    def _on_popup_action(self, action, data):
        if action == "show" and self.win:
            self.win.present()
        elif action == "edit" and self.win:
            self.win.present()
            if hasattr(self.win, '_show_entry_dialog'):
                entry = storage.get_entry(data)
                if entry:
                    self.win._show_entry_dialog(entry)


def main():
    app = NotebookApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
