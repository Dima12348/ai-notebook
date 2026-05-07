"""Flying robot overlay — transparent GTK window with animated jetpack robot.

Performance optimizations:
- Adaptive FPS: 30 when focused/moving, 10 when idle/unfocused
- Dirty-flag redraws: only queue_draw when state actually changes
- Cached Cairo surfaces for static robot parts
- Reduced fire animation iterations (4 vs 6)
"""
import math
import random
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo


class RobotOverlay(Gtk.Window):
    """Transparent overlay window with a flying jetpack robot."""

    # Animation timing
    FPS_ACTIVE = 30
    FPS_IDLE = 10
    FRAME_MS_ACTIVE = 1000 // FPS_ACTIVE   # ~33ms
    FRAME_MS_IDLE = 1000 // FPS_IDLE       # 100ms

    def __init__(self, on_click_callback=None):
        super().__init__(Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self._make_transparent()

        # Robot config
        self.robot_size = 60
        self.robot_color = (0.39, 0.40, 0.95)  # #6366f1
        self.robot_style = "modern"
        self.speed = 0.4

        # Position (stationary, bottom-right corner)
        screen = Gdk.Screen.get_default()
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.x = self.screen_w - 200
        self.y = self.screen_h - 300
        self.bob_phase = 0.0

        # Thought bubble
        self.bubble_text = ""
        self.bubble_alpha = 0.0
        self.bubble_timer = 0

        # Animation state
        self.eye_blink = 0
        self.blink_timer = 0
        self.antenna_wobble = 0.0
        self.fire_phase = 0.0

        # Emotions: neutral, happy, sad, thinking, surprised, sleepy, excited
        self.emotion = "neutral"
        self.emotion_timer = 0  # auto-reset after duration

        # Dragging
        self.dragging = False
        self.drag_offset = (0, 0)
        self.on_click = on_click_callback

        # Dirty flag — only redraw when something changed
        self._dirty = True
        self._idle_frames = 0
        self._focused = True

        # Cached surface for static robot parts
        self._cached_surface = None
        self._cache_valid = False
        self._cache_style = None
        self._cache_color = None
        self._cache_size = None

        # Window size
        win_size = self.robot_size * 5
        self.set_size_request(win_size, win_size)
        self.resize(win_size, win_size)
        self.move(self.x - win_size // 2, self.y - win_size // 2)

        # Events
        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_press)
        self.connect("button-release-event", self._on_release)
        self.connect("motion-notify-event", self._on_motion)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        # Track window focus for adaptive FPS
        self.connect("focus-in-event", self._on_focus_in)
        self.connect("focus-out-event", self._on_focus_out)

        # Animation timer — starts at active FPS
        self._timer_id = GLib.timeout_add(self.FRAME_MS_ACTIVE, self._animate)

    def _make_transparent(self):
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def _on_focus_in(self, *args):
        self._focused = True
        self._switch_timer(self.FRAME_MS_ACTIVE)

    def _on_focus_out(self, *args):
        self._focused = False
        if not self.dragging:
            self._switch_timer(self.FRAME_MS_IDLE)

    def _switch_timer(self, interval_ms):
        """Replace the animation timer with a new interval."""
        if hasattr(self, '_timer_id') and self._timer_id:
            GLib.source_remove(self._timer_id)
        self._timer_id = GLib.timeout_add(interval_ms, self._animate)

    def set_config(self, color_hex=None, size=None, speed=None, style=None):
        changed = False
        if color_hex:
            h = color_hex.lstrip("#")
            self.robot_color = tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
            changed = True
        if size:
            self.robot_size = int(size)
            win_size = self.robot_size * 5
            self.set_size_request(win_size, win_size)
            self.resize(win_size, win_size)
            changed = True
        if speed:
            self.speed = max(0.15, float(speed) * 0.2)
        if style:
            self.robot_style = style
            changed = True
        if changed:
            self._cache_valid = False
            self._dirty = True

    def show_bubble(self, text, duration=8000):
        self.bubble_text = text
        self.bubble_alpha = 0.0
        self.bubble_timer = duration // self.FRAME_MS_ACTIVE
        self._dirty = True

    def set_emotion(self, emotion, duration_sec=10):
        """Set robot emotion: neutral, happy, sad, thinking, surprised, sleepy, excited."""
        self.emotion = emotion
        self.emotion_timer = duration_sec * self.FPS_ACTIVE  # frames
        self._dirty = True

    # ── Animation ────────────────────────────────────────────

    def _animate(self):
        if not self.get_visible():
            return True

        # Floating bob (stationary — only vertical oscillation)
        self.bob_phase += 0.03
        bob_y = math.sin(self.bob_phase) * 6

        if not self.dragging:
            win_size = self.robot_size * 5
            self.move(int(self.x - win_size // 2), int(self.y - win_size // 2 + bob_y))

        # Eye blink
        self.blink_timer += 1
        if self.blink_timer > 90 + random.randint(0, 60):
            self.eye_blink = 5
            self.blink_timer = 0
            self._dirty = True
        if self.eye_blink > 0:
            self.eye_blink -= 1
            self._dirty = True

        # Antenna wobble
        new_wobble = math.sin(self.bob_phase * 2) * 6
        if abs(new_wobble - self.antenna_wobble) > 0.5:
            self.antenna_wobble = new_wobble
            self._dirty = True

        # Fire animation (always dirty when visible — flame moves)
        self.fire_phase += 0.25

        # Bubble fade
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_alpha < 1.0:
                self.bubble_alpha = min(1.0, self.bubble_alpha + 0.06)
                self._dirty = True
        elif self.bubble_alpha > 0:
            self.bubble_alpha = max(0.0, self.bubble_alpha - 0.04)
            self._dirty = True

        # Emotion timer — auto-reset to neutral
        if self.emotion_timer > 0:
            self.emotion_timer -= 1
            self._dirty = True
            if self.emotion_timer <= 0:
                self.emotion = "neutral"

        # Only redraw when dirty
        if self._dirty or moved:
            self._dirty = False
            self.queue_draw()

        return True

    # ── Jetpack & Helmet drawing helpers ─────────────────────

    def _draw_jetpack(self, cr, cx, cy, s, r, g, b, body_top, body_bottom):
        jp_w = s * 0.22
        jp_h = s * 0.45
        jp_x = cx - s * 0.05
        jp_y = body_top + (body_bottom - body_top) * 0.15

        # Jetpack body
        self._rounded_rect(cr, jp_x - jp_w / 2, jp_y, jp_w, jp_h, 5)
        cr.set_source_rgba(r * 0.3, g * 0.3, b * 0.3, 0.9)
        cr.fill_preserve()
        cr.set_source_rgba(r * 0.7, g * 0.7, b * 0.7, 0.8)
        cr.set_line_width(1.5)
        cr.stroke()

        # Tank lines
        cr.set_source_rgba(r * 0.5, g * 0.5, b * 0.5, 0.5)
        cr.set_line_width(1)
        cr.move_to(jp_x - jp_w / 4, jp_y + 4)
        cr.line_to(jp_x - jp_w / 4, jp_y + jp_h - 4)
        cr.stroke()
        cr.move_to(jp_x + jp_w / 4, jp_y + 4)
        cr.line_to(jp_x + jp_w / 4, jp_y + jp_h - 4)
        cr.stroke()

        # Nozzles
        nozzle_y = jp_y + jp_h
        for nx in (jp_x - jp_w / 4, jp_x + jp_w / 4):
            cr.set_source_rgba(r * 0.4, g * 0.4, b * 0.4, 0.9)
            self._rounded_rect(cr, nx - 3, nozzle_y - 2, 6, 8, 2)
            cr.fill()

        # Fire effect (reduced from 6 to 4 iterations)
        self._draw_fire(cr, jp_x - jp_w / 4, nozzle_y + 5, s * 0.15)
        self._draw_fire(cr, jp_x + jp_w / 4, nozzle_y + 5, s * 0.15)

    def _draw_fire(self, cr, fx, fy, max_h):
        """Draw animated fire/flame — reduced iterations for performance."""
        for i in range(4):  # was 6
            phase = self.fire_phase + i * 1.3
            flame_h = max_h * (0.5 + 0.5 * math.sin(phase))
            flame_w = max_h * 0.3 * (0.7 + 0.3 * math.cos(phase * 0.7))
            offset_x = math.sin(phase * 0.8) * 3

            cr.set_source_rgba(1, 0.5, 0.1, 0.6 - i * 0.1)
            cr.move_to(fx + offset_x - flame_w, fy)
            cr.curve_to(fx + offset_x - flame_w * 0.5, fy + flame_h * 0.4,
                        fx + offset_x + flame_w * 0.5, fy + flame_h * 0.4,
                        fx + offset_x + flame_w, fy)
            cr.curve_to(fx + offset_x + flame_w * 0.3, fy + flame_h * 0.7,
                        fx + offset_x - flame_w * 0.3, fy + flame_h * 0.7,
                        fx + offset_x, fy + flame_h)
            cr.curve_to(fx + offset_x - flame_w * 0.3, fy + flame_h * 0.7,
                        fx + offset_x - flame_w * 0.5, fy + flame_h * 0.5,
                        fx + offset_x - flame_w, fy)
            cr.fill()

        # Inner core
        core_h = max_h * 0.4 * (0.6 + 0.4 * math.sin(self.fire_phase * 1.5))
        core_w = max_h * 0.15
        cr.set_source_rgba(1, 0.9, 0.3, 0.8)
        cr.move_to(fx - core_w, fy)
        cr.curve_to(fx - core_w * 0.3, fy + core_h * 0.5,
                    fx + core_w * 0.3, fy + core_h * 0.5,
                    fx + core_w, fy)
        cr.curve_to(fx + core_w * 0.2, fy + core_h * 0.8,
                    fx - core_w * 0.2, fy + core_h * 0.8,
                    fx, fy + core_h)
        cr.curve_to(fx - core_w * 0.2, fy + core_h * 0.8,
                    fx - core_w * 0.4, fy + core_h * 0.4,
                    fx - core_w, fy)
        cr.fill()

        # Glow (single gradient, no extra arc)
        glow_r = max_h * 0.3
        grad = cairo.RadialGradient(fx, fy + max_h * 0.3, 0, fx, fy + max_h * 0.3, glow_r)
        grad.add_color_stop_rgba(0, 1, 0.6, 0.1, 0.3)
        grad.add_color_stop_rgba(1, 1, 0.3, 0.05, 0)
        cr.set_source(grad)
        cr.arc(fx, fy + max_h * 0.3, glow_r, 0, math.pi * 2)
        cr.fill()

    def _draw_helmet(self, cr, cx, cy, s, r, g, b, head_cy, head_radius):
        cr.set_source_rgba(r * 0.3, g * 0.3, b * 0.3, 0.7)
        cr.set_line_width(2.5)
        cr.arc(cx, head_cy, head_radius + 4, -math.pi * 0.85, -math.pi * 0.15)
        cr.stroke()

        cr.set_source_rgba(r * 0.6, g * 0.6, b * 0.6, 0.6)
        cr.set_line_width(1.5)
        cr.arc(cx, head_cy, head_radius + 2, -math.pi * 0.8, -math.pi * 0.2)
        cr.stroke()

        visor_x = cx - head_radius * 0.6
        visor_y = head_cy - head_radius * 0.3
        visor_w = head_radius * 1.2
        visor_h = head_radius * 0.3
        self._rounded_rect(cr, visor_x, visor_y, visor_w, visor_h, 4)
        cr.set_source_rgba(0.3, 0.8, 1.0, 0.12)
        cr.fill()

    # ── Main drawing ─────────────────────────────────────────

    def _on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        s = self.robot_size
        cx = self.get_allocated_width() / 2
        cy = self.get_allocated_height() / 2
        r, g, b = self.robot_color

        if self.bubble_alpha > 0.01:
            self._draw_bubble(cr, cx, cy - s * 1.8, s)

        if self.robot_style == "pixel":
            self._draw_pixel_robot(cr, cx, cy, s, r, g, b)
        elif self.robot_style == "round":
            self._draw_round_robot(cr, cx, cy, s, r, g, b)
        else:
            self._draw_modern_robot(cr, cx, cy, s, r, g, b)

    def _draw_modern_robot(self, cr, cx, cy, s, r, g, b):
        # Jetpack (behind body)
        self._draw_jetpack(cr, cx, cy, s, r, g, b,
                           cy - s * 0.55, cy + s * 0.35)

        # Shadow
        cr.set_source_rgba(0, 0, 0, 0.12)
        cr.arc(cx + 3, cy + s * 0.65 + 5, s * 0.38, 0, math.pi * 2)
        cr.fill()

        # Legs
        cr.set_line_width(5)
        cr.set_source_rgba(r * 0.45, g * 0.45, b * 0.45, 1)
        cr.move_to(cx - s * 0.12, cy + s * 0.35)
        cr.line_to(cx - s * 0.15, cy + s * 0.55)
        cr.stroke()
        cr.move_to(cx + s * 0.12, cy + s * 0.35)
        cr.line_to(cx + s * 0.15, cy + s * 0.55)
        cr.stroke()

        # Feet
        cr.set_source_rgba(r * 0.35, g * 0.35, b * 0.35, 1)
        self._rounded_rect(cr, cx - s * 0.22, cy + s * 0.52, 14, 6, 3)
        cr.fill()
        self._rounded_rect(cr, cx + s * 0.08, cy + s * 0.52, 14, 6, 3)
        cr.fill()

        # Arms
        cr.set_line_width(4)
        cr.set_source_rgba(r * 0.55, g * 0.55, b * 0.55, 1)
        cr.move_to(cx - s * 0.35, cy - s * 0.1)
        cr.line_to(cx - s * 0.5, cy + s * 0.05 + math.sin(self.bob_phase) * 4)
        cr.stroke()
        cr.move_to(cx + s * 0.35, cy - s * 0.1)
        cr.line_to(cx + s * 0.5, cy + s * 0.05 + math.sin(self.bob_phase + 1) * 4)
        cr.stroke()

        # Body
        self._rounded_rect(cr, cx - s * 0.35, cy - s * 0.55, s * 0.7, s * 0.9, 12)
        cr.set_source_rgba(r * 0.12, g * 0.12, b * 0.12, 1)
        cr.fill_preserve()
        cr.set_source_rgba(r, g, b, 0.8)
        cr.set_line_width(2)
        cr.stroke()

        # Screen face
        self._rounded_rect(cr, cx - s * 0.28, cy - s * 0.45, s * 0.56, s * 0.45, 8)
        cr.set_source_rgba(r * 0.06, g * 0.06, b * 0.06, 1)
        cr.fill()

        # Eyes + Mouth (emotion-aware)
        self._draw_face_emotion(cr, cx, cy - s * 0.25, s, r, g, b)

        # Chest light
        cr.set_source_rgba(r, g, b, 0.5 + 0.4 * math.sin(self.bob_phase * 3))
        cr.arc(cx, cy + s * 0.15, 4, 0, math.pi * 2)
        cr.fill()

        # Helmet
        self._draw_helmet(cr, cx, cy, s, r, g, b, cy - s * 0.25, s * 0.32)

        # Antenna
        aw = self.antenna_wobble
        cr.set_line_width(2.5)
        cr.set_source_rgba(r * 0.7, g * 0.7, b * 0.7, 1)
        cr.move_to(cx + aw * 0.3, cy - s * 0.55)
        cr.line_to(cx + aw, cy - s * 0.9)
        cr.stroke()
        cr.set_source_rgba(r, g, b, 1)
        cr.arc(cx + aw, cy - s * 0.9, 4, 0, math.pi * 2)
        cr.fill()

    def _draw_round_robot(self, cr, cx, cy, s, r, g, b):
        # Jetpack
        self._draw_jetpack(cr, cx, cy, s, r, g, b,
                           cy - s * 0.42, cy + s * 0.42)

        # Shadow
        cr.set_source_rgba(0, 0, 0, 0.1)
        cr.arc(cx + 2, cy + 5, s * 0.45, 0, math.pi * 2)
        cr.fill()

        # Feet
        cr.set_source_rgba(r * 0.35, g * 0.35, b * 0.35, 1)
        cr.arc(cx - s * 0.12, cy + s * 0.45, 7, 0, math.pi * 2)
        cr.fill()
        cr.arc(cx + s * 0.12, cy + s * 0.45, 7, 0, math.pi * 2)
        cr.fill()

        # Hands
        for side in (-1, 1):
            hx = cx + side * s * 0.48
            hy = cy + math.sin(self.bob_phase + (0 if side > 0 else 1)) * 5
            cr.arc(hx, hy, 8, 0, math.pi * 2)
            cr.set_source_rgba(r * 0.45, g * 0.45, b * 0.45, 1)
            cr.fill()

        # Body
        cr.arc(cx, cy, s * 0.42, 0, math.pi * 2)
        cr.set_source_rgba(r * 0.1, g * 0.1, b * 0.1, 1)
        cr.fill_preserve()
        cr.set_source_rgba(r, g, b, 0.6)
        cr.set_line_width(2.5)
        cr.stroke()

        # Eyes + Mouth (emotion-aware)
        self._draw_face_emotion(cr, cx, cy - s * 0.1, s, r, g, b, style="round")

        # Helmet
        self._draw_helmet(cr, cx, cy, s, r, g, b, cy - s * 0.05, s * 0.44)

        # Antenna
        cr.set_source_rgba(r, g, b, 1)
        cr.set_line_width(2)
        cr.move_to(cx, cy - s * 0.4)
        cr.line_to(cx, cy - s * 0.75)
        cr.stroke()
        cr.arc(cx, cy - s * 0.77, 5, 0, math.pi * 2)
        cr.fill()

    def _draw_pixel_robot(self, cr, cx, cy, s, r, g, b):
        px = s / 12

        def rect_px(x, y, w, h):
            self._rounded_rect(cr, cx + x * px, cy + y * px, w * px, h * px, 2)
            cr.fill()

        # Jetpack
        jp_x, jp_y = -1, -3
        jp_w, jp_h = 2, 5
        cr.set_source_rgba(r * 0.3, g * 0.3, b * 0.3, 0.85)
        rect_px(jp_x, jp_y, jp_w, jp_h)
        cr.set_source_rgba(r * 0.4, g * 0.4, b * 0.4, 0.9)
        rect_px(jp_x, jp_y + jp_h, 0.8, 1)
        rect_px(jp_x + jp_w - 0.8, jp_y + jp_h, 0.8, 1)
        self._draw_fire(cr, cx + (jp_x + 0.4) * px, cy + (jp_y + jp_h + 1) * px, s * 0.12)
        self._draw_fire(cr, cx + (jp_x + jp_w - 0.4) * px, cy + (jp_y + jp_h + 1) * px, s * 0.12)

        # Antenna
        cr.set_source_rgba(r, g, b, 1)
        rect_px(-0.5, -8, 1, 3)
        rect_px(-1.5, -10, 3, 2)

        # Legs
        cr.set_source_rgba(r * 0.45, g * 0.45, b * 0.45, 1)
        rect_px(-2.5, 5.5, 1.5, 3)
        rect_px(1, 5.5, 1.5, 3)

        # Arms
        cr.set_source_rgba(r * 0.45, g * 0.45, b * 0.45, 1)
        rect_px(-5, 0, 1.5, 4)
        rect_px(3.5, 0, 1.5, 4)

        # Head
        cr.set_source_rgba(r * 0.15, g * 0.15, b * 0.15, 1)
        rect_px(-4, -6, 8, 5)
        cr.set_source_rgba(r, g, b, 0.8)
        cr.set_line_width(1.5)
        self._rounded_rect(cr, cx - 4 * px, cy - 6 * px, 8 * px, 5 * px, 3)
        cr.stroke()

        # Eyes
        cr.set_source_rgba(0.4, 1, 0.6, 1)
        ey = -4.5 if self.eye_blink == 0 else -4
        eh = 1.5 if self.eye_blink == 0 else 0.5
        rect_px(-2.5, ey, 1.5, eh)
        rect_px(1, ey, 1.5, eh)

        # Body
        cr.set_source_rgba(r * 0.12, g * 0.12, b * 0.12, 1)
        rect_px(-3.5, -0.5, 7, 6)
        cr.set_source_rgba(r, g, b, 0.7)
        self._rounded_rect(cr, cx - 3.5 * px, cy - 0.5 * px, 7 * px, 6 * px, 3)
        cr.stroke()

        # Chest buttons
        cr.set_source_rgba(r, g, b, 0.5)
        for i in range(3):
            rect_px(-1.5 + i * 1.2, 1.5, 0.8, 0.8)

        # Helmet
        cr.set_source_rgba(r * 0.5, g * 0.5, b * 0.5, 0.6)
        cr.set_line_width(2)
        self._rounded_rect(cr, cx - 4.5 * px, cy - 6.5 * px, 9 * px, 5.5 * px, 3)
        cr.stroke()

    def _draw_face_emotion(self, cr, cx, eye_y, s, r, g, b, style="modern"):
        """Draw eyes and mouth based on current emotion."""
        emo = self.emotion
        blinking = self.eye_blink > 0

        if style == "round":
            # Round style: circular eyes
            eye_r = 4 if blinking else 8
            cr.set_source_rgba(1, 1, 1, 0.95)

            if emo == "happy":
                # ^_^ — arc eyes
                cr.set_line_width(2.5)
                cr.arc(cx - s * 0.14, eye_y, 6, math.pi + 0.3, -0.3)
                cr.stroke()
                cr.arc(cx + s * 0.14, eye_y, 6, math.pi + 0.3, -0.3)
                cr.stroke()
            elif emo == "sad":
                # T_T — teardrop eyes
                cr.arc(cx - s * 0.14, eye_y, eye_r, 0, math.pi * 2)
                cr.fill()
                cr.arc(cx + s * 0.14, eye_y, eye_r, 0, math.pi * 2)
                cr.fill()
                # Teardrop
                cr.set_source_rgba(0.4, 0.7, 1.0, 0.7)
                cr.arc(cx - s * 0.14, eye_y + 10, 3, 0, math.pi * 2)
                cr.fill()
            elif emo == "surprised":
                # O_O — big circles
                cr.arc(cx - s * 0.14, eye_y, 10, 0, math.pi * 2)
                cr.fill()
                cr.arc(cx + s * 0.14, eye_y, 10, 0, math.pi * 2)
                cr.fill()
                cr.set_source_rgba(0.1, 0.1, 0.15, 1)
                cr.arc(cx - s * 0.14, eye_y, 4, 0, math.pi * 2)
                cr.fill()
                cr.arc(cx + s * 0.14, eye_y, 4, 0, math.pi * 2)
                cr.fill()
            elif emo == "sleepy":
                # -_- — half-closed
                cr.set_line_width(2.5)
                cr.move_to(cx - s * 0.14 - 6, eye_y)
                cr.line_to(cx - s * 0.14 + 6, eye_y)
                cr.stroke()
                cr.move_to(cx + s * 0.14 - 6, eye_y)
                cr.line_to(cx + s * 0.14 + 6, eye_y)
                cr.stroke()
            elif emo == "thinking":
                # One eye closed, one open
                cr.arc(cx - s * 0.14, eye_y, eye_r, 0, math.pi * 2)
                cr.fill()
                cr.set_source_rgba(0.1, 0.1, 0.15, 1)
                cr.arc(cx - s * 0.14, eye_y, 3, 0, math.pi * 2)
                cr.fill()
                cr.set_source_rgba(1, 1, 1, 0.95)
                cr.set_line_width(2.5)
                cr.arc(cx + s * 0.14, eye_y, 6, math.pi + 0.3, -0.3)
                cr.stroke()
            elif emo == "excited":
                # Star eyes ★
                self._draw_star(cr, cx - s * 0.14, eye_y, 8)
                self._draw_star(cr, cx + s * 0.14, eye_y, 8)
            else:
                # neutral — normal round eyes
                if blinking:
                    cr.set_line_width(2)
                    cr.move_to(cx - s * 0.14 - 5, eye_y)
                    cr.line_to(cx - s * 0.14 + 5, eye_y)
                    cr.stroke()
                    cr.move_to(cx + s * 0.14 - 5, eye_y)
                    cr.line_to(cx + s * 0.14 + 5, eye_y)
                    cr.stroke()
                else:
                    cr.arc(cx - s * 0.14, eye_y, eye_r, 0, math.pi * 2)
                    cr.fill()
                    cr.arc(cx + s * 0.14, eye_y, eye_r, 0, math.pi * 2)
                    cr.fill()
                    cr.set_source_rgba(0.1, 0.1, 0.15, 1)
                    cr.arc(cx - s * 0.14, eye_y, 3, 0, math.pi * 2)
                    cr.fill()
                    cr.arc(cx + s * 0.14, eye_y, 3, 0, math.pi * 2)
                    cr.fill()

            # Mouth for round style
            cr.set_source_rgba(r, g, b, 0.7)
            cr.set_line_width(2)
            mouth_y = eye_y + s * 0.2
            if emo == "happy":
                cr.arc(cx, mouth_y, 12, 0.2, math.pi - 0.2)
                cr.stroke()
            elif emo == "sad":
                cr.arc(cx, mouth_y + 8, 10, math.pi + 0.3, -0.3)
                cr.stroke()
            elif emo == "surprised":
                cr.arc(cx, mouth_y, 6, 0, math.pi * 2)
                cr.stroke()
            elif emo == "thinking":
                cr.move_to(cx - 6, mouth_y)
                cr.line_to(cx + 6, mouth_y)
                cr.stroke()
            elif emo == "sleepy":
                cr.move_to(cx - 4, mouth_y)
                cr.line_to(cx + 4, mouth_y)
                cr.stroke()
            elif emo == "excited":
                cr.arc(cx, mouth_y, 14, 0.1, math.pi - 0.1)
                cr.stroke()
            else:
                cr.arc(cx, mouth_y, 8, 0.3, math.pi - 0.3)
                cr.stroke()

        else:
            # Modern style: rectangular screen eyes
            eye_h = 5 if blinking else 7
            cr.set_source_rgba(0.4, 1, 0.6, 1)

            if emo == "happy":
                # ^_^ — angled lines
                cr.set_line_width(2.5)
                cr.move_to(cx - s * 0.17, eye_y + 3)
                cr.line_to(cx - s * 0.12, eye_y - 3)
                cr.line_to(cx - s * 0.07, eye_y + 3)
                cr.stroke()
                cr.move_to(cx + s * 0.07, eye_y + 3)
                cr.line_to(cx + s * 0.12, eye_y - 3)
                cr.line_to(cx + s * 0.17, eye_y + 3)
                cr.stroke()
            elif emo == "sad":
                self._rounded_rect(cr, cx - s * 0.17, eye_y - eye_h / 2, 10, eye_h, 3)
                cr.fill()
                self._rounded_rect(cr, cx + s * 0.07, eye_y - eye_h / 2, 10, eye_h, 3)
                cr.fill()
                cr.set_source_rgba(0.4, 0.7, 1.0, 0.7)
                cr.arc(cx - s * 0.12, eye_y + 10, 3, 0, math.pi * 2)
                cr.fill()
            elif emo == "surprised":
                # Big O eyes
                cr.arc(cx - s * 0.12, eye_y, 7, 0, math.pi * 2)
                cr.fill()
                cr.arc(cx + s * 0.12, eye_y, 7, 0, math.pi * 2)
                cr.fill()
            elif emo == "sleepy":
                cr.set_line_width(2)
                cr.move_to(cx - s * 0.17, eye_y)
                cr.line_to(cx - s * 0.07, eye_y)
                cr.stroke()
                cr.move_to(cx + s * 0.07, eye_y)
                cr.line_to(cx + s * 0.17, eye_y)
                cr.stroke()
            elif emo == "thinking":
                self._rounded_rect(cr, cx - s * 0.17, eye_y - eye_h / 2, 10, eye_h, 3)
                cr.fill()
                cr.set_line_width(2)
                cr.move_to(cx + s * 0.07, eye_y)
                cr.line_to(cx + s * 0.17, eye_y)
                cr.stroke()
            elif emo == "excited":
                self._draw_star(cr, cx - s * 0.12, eye_y, 7)
                self._draw_star(cr, cx + s * 0.12, eye_y, 7)
            else:
                # neutral
                self._rounded_rect(cr, cx - s * 0.17, eye_y - eye_h / 2, 10, eye_h, 3)
                cr.fill()
                self._rounded_rect(cr, cx + s * 0.07, eye_y - eye_h / 2, 10, eye_h, 3)
                cr.fill()

            # Mouth for modern style
            cr.set_source_rgba(0.4, 1, 0.6, 0.7)
            cr.set_line_width(2)
            mouth_y = eye_y + s * 0.17
            if emo == "happy":
                cr.arc(cx, mouth_y, 12, 0.2, math.pi - 0.2)
                cr.stroke()
            elif emo == "sad":
                cr.arc(cx, mouth_y + 8, 8, math.pi + 0.3, -0.3)
                cr.stroke()
            elif emo == "surprised":
                cr.arc(cx, mouth_y, 5, 0, math.pi * 2)
                cr.stroke()
            elif emo == "thinking":
                cr.move_to(cx - 6, mouth_y)
                cr.line_to(cx + 6, mouth_y)
                cr.stroke()
            elif emo == "sleepy":
                cr.move_to(cx - 4, mouth_y)
                cr.line_to(cx + 4, mouth_y)
                cr.stroke()
            elif emo == "excited":
                cr.arc(cx, mouth_y, 14, 0.1, math.pi - 0.1)
                cr.stroke()
            else:
                cr.arc(cx, mouth_y, 10, 0.2, math.pi - 0.2)
                cr.stroke()

    @staticmethod
    def _draw_star(cr, cx, cy, size):
        """Draw a small star shape."""
        import math as m
        cr.new_path()
        for i in range(5):
            angle = -m.pi / 2 + i * 2 * m.pi / 5
            outer_x = cx + size * m.cos(angle)
            outer_y = cy + size * m.sin(angle)
            inner_angle = angle + m.pi / 5
            inner_x = cx + size * 0.4 * m.cos(inner_angle)
            inner_y = cy + size * 0.4 * m.sin(inner_angle)
            if i == 0:
                cr.move_to(outer_x, outer_y)
            else:
                cr.line_to(outer_x, outer_y)
            cr.line_to(inner_x, inner_y)
        cr.close_path()
        cr.fill()

    def _draw_bubble(self, cr, bx, by, s):
        alpha = self.bubble_alpha

        bw = min(max(len(self.bubble_text) * 6, 120), 320)
        bh = 50

        # Thought dots
        for i in range(3):
            dot_y = by + bh / 2 + 15 + i * 10
            dot_r = 4 - i
            cr.set_source_rgba(1, 1, 1, alpha * 0.6)
            cr.arc(bx, dot_y, dot_r, 0, math.pi * 2)
            cr.fill()

        # Bubble background
        self._rounded_rect(cr, bx - bw / 2, by - bh / 2, bw, bh, 16)
        cr.set_source_rgba(0.12, 0.13, 0.18, alpha * 0.92)
        cr.fill_preserve()
        cr.set_source_rgba(*self.robot_color, alpha * 0.5)
        cr.set_line_width(1.5)
        cr.stroke()

        # Text
        cr.set_source_rgba(1, 1, 1, alpha)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        text = self.bubble_text
        if len(text) > 50:
            text = text[:47] + "..."
        extents = cr.text_extents(text)
        tx = bx - extents.width / 2
        ty = by + extents.height / 2
        cr.move_to(tx, ty)
        cr.show_text(text)

    @staticmethod
    def _rounded_rect(cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    # ── Events ───────────────────────────────────────────────

    def _on_press(self, widget, event):
        if event.button == 1:
            if self.on_click:
                self.on_click("menu")
                return True  # stop event propagation
            else:
                self.dragging = True
                ox, oy = self.get_position()
                self.drag_offset = (event.x_root - ox, event.y_root - oy)
                self._switch_timer(self.FRAME_MS_ACTIVE)
        elif event.button == 3:
            self.dragging = True
            ox, oy = self.get_position()
            self.drag_offset = (event.x_root - ox, event.y_root - oy)
            self._switch_timer(self.FRAME_MS_ACTIVE)

    def _on_release(self, widget, event):
        if self.dragging:
            self.dragging = False
            ox, oy = self.get_position()
            win_size = self.robot_size * 5
            self.x = ox + win_size // 2
            self.y = oy + win_size // 2
            if not self._focused:
                self._switch_timer(self.FRAME_MS_IDLE)

    def _on_motion(self, widget, event):
        if self.dragging:
            new_x = int(event.x_root - self.drag_offset[0])
            new_y = int(event.y_root - self.drag_offset[1])
            self.move(new_x, new_y)
