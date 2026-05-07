"""Reminder scheduler — checks for due reminders and fires notifications."""
import os
import subprocess
import threading
import time
from datetime import datetime

import gi
gi.require_version("Notify", "0.7")
from gi.repository import Notify, GLib

from . import storage

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
NOTIFY_WAV = os.path.join(ASSETS_DIR, "notify.wav")


def _play_sound():
    """Play notification sound in background (non-blocking)."""
    if not os.path.exists(NOTIFY_WAV):
        return
    try:
        # Try paplay (PulseAudio) first, then aplay (ALSA)
        for cmd in [["paplay", NOTIFY_WAV], ["aplay", "-q", NOTIFY_WAV]]:
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except FileNotFoundError:
                continue
    except Exception:
        pass


class Scheduler:
    """Background thread that polls for due reminders."""

    def __init__(self, robot=None, on_reminder=None, interval=5):
        self.robot = robot
        self.on_reminder = on_reminder  # callback(entry_dict)
        self.interval = interval  # seconds between checks
        self._running = False
        self._thread = None
        self._notified_ids = set()  # avoid spamming same reminder
        Notify.init("AI Notebook")

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self._check()
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
            time.sleep(self.interval)

    def _check(self):
        due = storage.get_due_reminders()
        for entry in due:
            eid = entry["id"]
            if eid in self._notified_ids:
                continue
            self._notified_ids.add(eid)

            text = f"⏰ {entry['title']}"
            if entry.get("content"):
                text += f"\n{entry['content'][:80]}"

            # Play sound
            _play_sound()

            # System notification
            try:
                n = Notify.Notification.new("AI Notebook — Reminder", text, "dialog-information")
                n.set_timeout(10000)
                n.show()
            except Exception:
                pass

            # Robot thought bubble + emotion
            if self.robot:
                GLib.idle_add(self.robot.show_bubble, entry["title"])
                GLib.idle_add(self.robot.set_emotion, "excited", 15)

            # Custom callback
            if self.on_reminder:
                GLib.idle_add(self.on_reminder, entry)

    def dismiss(self, entry_id):
        """Mark a reminder as notified so it won't fire again."""
        self._notified_ids.discard(entry_id)

    def clear_dismissed(self):
        self._notified_ids.clear()
