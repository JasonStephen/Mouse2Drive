from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path

from app.shared.i18n import load_i18n
from app.shared.paths import APP_BASE_DIR
try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = None
    ImageDraw = None

ICON_FONT_FAMILY = "Segoe MDL2 Assets"
ICON_SETTINGS = "\uE713"
ICON_LOCK = "\uE72E"
ICON_UNLOCK = "\uE785"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class Indicator:
    def __init__(
        self,
        debug_mode: bool = False,
        hud_fps: int = 25,
        min_output_x: float = 0.235,
        windows_scale: float = 1.0,
        fullscreen_scale: float = 1.0,
        fullscreen_alpha: float = 0.5,
        language: str = "zh-CN",
        i18n_map: dict[str, str] | None = None,
        settings_getter=None,
        settings_apply_callback=None,
        settings_open_callback=None,
        exit_callback=None,
        i18n_loader=load_i18n,
        hud_fps_options_getter=None,
        window_clickthrough_setter=None,
    ) -> None:
        self.debug_mode = debug_mode
        self.hud_fps = int(clamp(hud_fps, 5, 240))
        self.hud_interval_ms = max(1, int(1000 / self.hud_fps))
        self.min_output_x = clamp(min_output_x, 0.0, 1.0)
        self.window_scale = clamp(windows_scale, 0.8, 1.5)
        self.fullscreen_scale = clamp(fullscreen_scale, 0.8, 1.5)
        self.fullscreen_alpha = clamp(fullscreen_alpha, 0.0, 1.0)
        self.language = language if language in {"zh-CN", "en-US"} else "zh-CN"
        self.i18n = dict(i18n_map or {})
        self.ui_scale = max(1.15, self.window_scale * 1.15)
        self.settings_getter = settings_getter
        self.settings_apply_callback = settings_apply_callback
        self.settings_open_callback = settings_open_callback
        self.exit_callback = exit_callback
        self.i18n_loader = i18n_loader
        self.hud_fps_options_getter = hud_fps_options_getter or (lambda: (15, 30, 60, 90, 120))
        self.window_clickthrough_setter = window_clickthrough_setter or (lambda *_args, **_kwargs: None)
        self.settings_window: tk.Toplevel | None = None
        self.settings_window_scale_var: tk.StringVar | None = None
        self.settings_fullscreen_scale_var: tk.StringVar | None = None
        self.settings_min_output_var: tk.StringVar | None = None
        self.settings_panel_widgets: list[tk.Widget] = []
        self.settings_category_list: tk.Listbox | None = None
        self.settings_webview_proc = None
        self.settings_ipc_path = str(Path(tempfile.gettempdir()) / "fh_liner_settings_ipc.json")
        self.settings_state_path = str(Path(tempfile.gettempdir()) / "fh_liner_settings_state.json")
        self.settings_debug_log_path = str(Path(tempfile.gettempdir()) / "fh_liner_settings_webview.log")
        self.settings_webview_log_handle = None
        self.settings_ipc_last_ts = 0.0
        self.local_error_text = ""
        self.fullscreen_mode = False
        self.fullscreen_available = True
        self.fullscreen_rect: tuple[int, int, int, int] | None = None
        self.scene = {}
        self.fullscreen_bg_key = "#101010"
        self.locked = True
        self.fs_module_offset_x = 0
        self.fs_module_offset_y = 0
        self.fs_lx_offset_x = 0
        self.fs_lx_offset_y = 0
        self.fs_brake_offset_x = 0
        self.fs_brake_offset_y = 0
        self.fs_gas_offset_x = 0
        self.fs_gas_offset_y = 0
        self.fs_dragging_module = False
        self.fs_drag_target = ""
        self.fs_drag_start_mouse_x = 0
        self.fs_drag_start_mouse_y = 0
        self.fs_drag_start_offset_x = 0
        self.fs_drag_start_offset_y = 0
        self.drag_start_mouse_x = 0
        self.drag_start_mouse_y = 0
        self.drag_start_win_x = 0
        self.drag_start_win_y = 0
        self.root = tk.Tk()
        self.root.title(self._t("app.window.title", "Mouse -> Virtual Gamepad"))
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        self.frame = tk.Frame(self.root, bg="#1f1f1f", bd=1, relief="solid")
        self.frame.pack(fill="both", expand=True)
        self.header = tk.Frame(self.frame, bg="#1f1f1f")
        self.header.pack(fill="x")
        self.status_label = tk.Label(self.header, text=self._t("app.status.off", "Status: OFF"), fg="#ff6b6b", bg="#1f1f1f", font=("Segoe UI", self._font(14), "bold"), anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.lock_button = tk.Button(self.header, text=ICON_LOCK, width=2, command=self.toggle_lock, bg="#2b2b2b", fg="#f0f0f0", activebackground="#3a3a3a", activeforeground="#ffffff", bd=0, font=(ICON_FONT_FAMILY, self._font(10), "normal"))
        self.lock_button.pack(side="right")
        self.settings_button = tk.Button(self.header, text=ICON_SETTINGS, width=2, command=self.open_settings_panel, bg="#2b2b2b", fg="#f0f0f0", activebackground="#3a3a3a", activeforeground="#ffffff", bd=0, font=(ICON_FONT_FAMILY, self._font(10), "normal"))
        self.settings_button.pack(side="right", padx=(0, 6))
        self.canvas = tk.Canvas(self.frame, width=100, height=100, bg="#171717", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.error_label = tk.Label(self.frame, text="", fg="#ffcc66", bg="#1f1f1f", font=("Segoe UI", self._font(8)), anchor="w", justify="left")
        self.error_label.pack(fill="x")
        self.debug_label = tk.Label(self.frame, text="", fg="#9fd6ff", bg="#1f1f1f", font=("Consolas", self._font(8)), anchor="w", justify="left")
        self.debug_label.pack(fill="x")
        self.window_pad_x = max(8, int(round(10 * self.ui_scale)))
        self.window_pad_y = max(3, int(round(4 * self.ui_scale)))
        self.lock_button_pack_kwargs = {"side": "right", "padx": max(8, int(round(10 * self.ui_scale))), "pady": max(3, int(round(4 * self.ui_scale)))}
        self.settings_button_pack_kwargs = {"side": "right", "padx": (0, 6), "pady": max(3, int(round(4 * self.ui_scale)))}
        self._bind_drag_for_widget(self.frame)
        self.root.bind("<Configure>", lambda _e: self.ensure_on_screen())
        self.root.update_idletasks()
        self.apply_view_mode(False)
        self._init_scene()
        self.root.after(250, self._poll_settings_ipc)
        self.tray_icon = None
        self.tray_enabled = False
        self._start_tray_icon()

    def _build_tray_image(self):
        if Image is None or ImageDraw is None:
            return None
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((4, 4, 60, 60), radius=12, fill=(25, 25, 25, 255))
        draw.rectangle((18, 18, 46, 46), outline=(120, 255, 155, 255), width=4)
        draw.rectangle((30, 10, 34, 18), fill=(255, 107, 107, 255))
        return img

    def _request_exit(self) -> None:
        try:
            if callable(self.exit_callback):
                self.exit_callback()
        except Exception:
            pass

    def _start_tray_icon(self) -> None:
        if pystray is None:
            return
        try:
            icon_image = self._build_tray_image()
            if icon_image is None:
                return
            title = self._t("app.window.title", "Mouse_Controller")
            menu = pystray.Menu(
                pystray.MenuItem(self._t("app.tray.exit", "退出"), lambda _icon, _item: self._request_exit())
            )
            self.tray_icon = pystray.Icon("mouse_controller_tray", icon_image, title, menu)
            self.tray_icon.run_detached()
            self.tray_enabled = True
        except Exception:
            self.tray_icon = None
            self.tray_enabled = False

    def _stop_tray_icon(self) -> None:
        if not self.tray_enabled or self.tray_icon is None:
            return
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        finally:
            self.tray_icon = None
            self.tray_enabled = False

    def _t(self, key: str, fallback: str) -> str:
        val = self.i18n.get(key)
        if val is None or str(val).strip() == "":
            return fallback
        return str(val)

    def position_bottom_right(self) -> None:
        self.root.update_idletasks()
        # Keep windowed HUD at a deterministic compact size.
        # Do not use reqwidth/reqheight here; after fullscreen mode they can stay huge.
        w = int(round(390 * self.ui_scale))
        h = int(round((205 if self.debug_mode else 180) * self.ui_scale))
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{sw - w - 18}+{sh - h - 58}")
        self.ensure_on_screen()

    def set_fullscreen_rect(self, rect: tuple[int, int, int, int] | None) -> None:
        self.fullscreen_rect = rect

    def position_fullscreen_overlay(self) -> None:
        if self.fullscreen_rect is not None:
            vx, vy, vw, vh = self.fullscreen_rect
        else:
            vx, vy, vw, vh = 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{int(vw)}x{int(vh)}+{int(vx)}+{int(vy)}")

    def toggle_lock(self) -> None:
        self.locked = not self.locked
        self.lock_button.config(text=(ICON_LOCK if self.locked else ICON_UNLOCK))

    def _bind_drag_for_widget(self, widget: tk.Widget) -> None:
        widget.bind("<ButtonPress-1>", self._on_drag_start, add="+")
        widget.bind("<B1-Motion>", self._on_drag_move, add="+")
        widget.bind("<ButtonRelease-1>", self._on_drag_release, add="+")
        for child in widget.winfo_children():
            self._bind_drag_for_widget(child)

    def _on_drag_start(self, event) -> None:
        if self.fullscreen_mode:
            self._on_fullscreen_drag_start(event)
            return
        if self.locked:
            return
        self.drag_start_mouse_x = event.x_root
        self.drag_start_mouse_y = event.y_root
        self.drag_start_win_x = self.root.winfo_x()
        self.drag_start_win_y = self.root.winfo_y()

    def _on_drag_move(self, event) -> None:
        if self.fullscreen_mode:
            self._on_fullscreen_drag_move(event)
            return
        if self.locked:
            return
        dx = event.x_root - self.drag_start_mouse_x
        dy = event.y_root - self.drag_start_mouse_y
        new_x = self.drag_start_win_x + dx
        new_y = self.drag_start_win_y + dy
        self.root.geometry(f"+{new_x}+{new_y}")
        self.ensure_on_screen()

    def _on_drag_release(self, _event) -> None:
        self.fs_dragging_module = False
        self.fs_drag_target = ""

    def _on_ctrl_o(self, _event=None) -> str:
        self.open_settings_panel()
        return "break"

    def _on_fullscreen_drag_start(self, event) -> None:
        if self._in_fs_settings_bounds(event.x, event.y):
            self.open_settings_panel()
            return
        if self._in_fs_lock_bounds(event.x, event.y):
            self.locked = not self.locked
            self._update_fs_lock_visual()
            return
        if self.locked:
            return
        if self._in_fs_lx_bounds(event.x, event.y):
            self.fs_dragging_module = True
            self.fs_drag_target = "lx"
            self.fs_drag_start_mouse_x = event.x
            self.fs_drag_start_mouse_y = event.y
            self.fs_drag_start_offset_x = self.fs_lx_offset_x
            self.fs_drag_start_offset_y = self.fs_lx_offset_y
            return
        if self._in_fs_brake_bounds(event.x, event.y):
            self.fs_dragging_module = True
            self.fs_drag_target = "brake"
            self.fs_drag_start_mouse_x = event.x
            self.fs_drag_start_mouse_y = event.y
            self.fs_drag_start_offset_x = self.fs_brake_offset_x
            self.fs_drag_start_offset_y = self.fs_brake_offset_y
            return
        if self._in_fs_gas_bounds(event.x, event.y):
            self.fs_dragging_module = True
            self.fs_drag_target = "gas"
            self.fs_drag_start_mouse_x = event.x
            self.fs_drag_start_mouse_y = event.y
            self.fs_drag_start_offset_x = self.fs_gas_offset_x
            self.fs_drag_start_offset_y = self.fs_gas_offset_y
            return
        if self._in_fs_module_bounds(event.x, event.y):
            self.fs_dragging_module = True
            self.fs_drag_target = "module"
            self.fs_drag_start_mouse_x = event.x
            self.fs_drag_start_mouse_y = event.y
            self.fs_drag_start_offset_x = self.fs_module_offset_x
            self.fs_drag_start_offset_y = self.fs_module_offset_y

    def _on_fullscreen_drag_move(self, event) -> None:
        if not self.fs_dragging_module:
            return
        dx = event.x - self.fs_drag_start_mouse_x
        dy = event.y - self.fs_drag_start_mouse_y
        if self.fs_drag_target == "lx":
            self.fs_lx_offset_x = self.fs_drag_start_offset_x + dx
            self.fs_lx_offset_y = self.fs_drag_start_offset_y + dy
        elif self.fs_drag_target == "brake":
            self.fs_brake_offset_x = self.fs_drag_start_offset_x + dx
            self.fs_brake_offset_y = self.fs_drag_start_offset_y + dy
        elif self.fs_drag_target == "gas":
            self.fs_gas_offset_x = self.fs_drag_start_offset_x + dx
            self.fs_gas_offset_y = self.fs_drag_start_offset_y + dy
        else:
            self.fs_module_offset_x = self.fs_drag_start_offset_x + dx
            self.fs_module_offset_y = self.fs_drag_start_offset_y + dy
        self._init_scene()

    def ensure_on_screen(self) -> None:
        self.root.update_idletasks()
        win_w = self.root.winfo_width()
        win_h = self.root.winfo_height()
        x = self.root.winfo_x()
        y = self.root.winfo_y()

        # Multi-monitor friendly: clamp inside the virtual desktop, not only primary screen.
        try:
            user32 = ctypes.windll.user32
            vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        except Exception:
            vx, vy = 0, 0
            vw = self.root.winfo_screenwidth()
            vh = self.root.winfo_screenheight()

        min_x = vx
        min_y = vy
        max_x = vx + max(0, vw - win_w)
        max_y = vy + max(0, vh - win_h)
        nx = int(clamp(x, min_x, max_x))
        ny = int(clamp(y, min_y, max_y))
        if nx != x or ny != y:
            self.root.geometry(f"+{nx}+{ny}")

    def _clear_scene(self) -> None:
        self.canvas.delete("all")
        self.scene = {}

    def _init_scene_windowed(self) -> None:
        c = self.canvas
        s = self.ui_scale
        x = lambda v: int(round(v * s))
        y = lambda v: int(round(v * s))
        c.configure(width=max(360, x(360)), height=max(98, y(98)))
        c.create_text(x(24), y(17), text="L", fill="#cfd8dc", font=("Segoe UI", self._font(9), "bold"))
        self.scene["lx_track"] = c.create_rectangle(x(40), y(10), x(340), y(24), outline="#4a4a4a", fill="#262626")
        cx = x(190)
        c.create_line(cx, y(8), cx, y(26), fill="#9e9e9e", width=max(1, int(round(2 * s))))
        self.scene["lx_fill"] = c.create_rectangle(cx, y(11), cx, y(23), outline="", fill="#67b7ff")
        c.create_text(x(34), y(68), text=self._t("app.label.brake", "刹车"), fill="#ffcdd2", font=("Segoe UI", self._font(9)))
        self.scene["brake_track"] = c.create_rectangle(x(60), y(60), x(150), y(74), outline="#8a8a8a", fill="#2a2a2a")
        self.scene["brake_fill"] = c.create_rectangle(x(61), y(61), x(61), y(73), outline="", fill="#ff6b6b")
        self.scene["brake_box"] = c.create_rectangle(x(154), y(60), x(166), y(74), outline="#8a8a8a", fill="#2a2a2a")
        c.create_text(x(222), y(68), text=self._t("app.label.gas", "油门"), fill="#c8e6c9", font=("Segoe UI", self._font(9)))
        self.scene["gas_track"] = c.create_rectangle(x(248), y(60), x(338), y(74), outline="#8a8a8a", fill="#2a2a2a")
        self.scene["gas_fill"] = c.create_rectangle(x(249), y(61), x(249), y(73), outline="", fill="#37d45c")
        self.scene["gas_box"] = c.create_rectangle(x(342), y(60), x(354), y(74), outline="#8a8a8a", fill="#2a2a2a")

    def _init_scene_fullscreen(self) -> None:
        c = self.canvas
        self.root.update_idletasks()
        sw = max(1, self.root.winfo_width())
        sh = max(1, self.root.winfo_height())
        c.configure(width=sw, height=sh)
        c.configure(bg=self.fullscreen_bg_key, highlightthickness=0, bd=0)
        # HUD text anchors
        self.scene["status_text"] = c.create_text(28, 28, text=self._t("app.status.off", "Status: OFF"), fill="#ffffff", font=("Segoe UI", self._font(24), "bold"), anchor="nw")
        self.scene["error_text"] = c.create_text(28, sh - 28, text="", fill="#ffffff", font=("Segoe UI", self._font(16), "bold"), anchor="sw")
        self.scene["debug_text"] = c.create_text(28, sh - 28 - self._font(16) - 10, text="", fill="#d6f0ff", font=("Consolas", self._font(12)), anchor="sw")
        # Fullscreen top-right icons: settings + lock
        lock_w, lock_h = 52, 44
        lock_x1 = sw - 24
        lock_y0 = 24
        lock_x0 = lock_x1 - lock_w
        lock_y1 = lock_y0 + lock_h
        self.fs_lock_bounds = (lock_x0, lock_y0, lock_x1, lock_y1)
        self.scene["fs_lock_bg"] = c.create_rectangle(lock_x0, lock_y0, lock_x1, lock_y1, outline="#d0d0d0", width=2)
        self.scene["fs_lock_text"] = c.create_text((lock_x0 + lock_x1) // 2, (lock_y0 + lock_y1) // 2, text="", fill="#ffffff", font=(ICON_FONT_FAMILY, self._font(15), "normal"))
        set_gap = 8
        set_x1 = lock_x0 - set_gap
        set_x0 = set_x1 - lock_w
        self.fs_settings_bounds = (set_x0, lock_y0, set_x1, lock_y1)
        self.scene["fs_settings_bg"] = c.create_rectangle(set_x0, lock_y0, set_x1, lock_y1, outline="#d0d0d0", width=2, fill="#2d2d2d")
        self.scene["fs_settings_text"] = c.create_text((set_x0 + set_x1) // 2, (lock_y0 + lock_y1) // 2, text=ICON_SETTINGS, fill="#ffffff", font=(ICON_FONT_FAMILY, self._font(15), "normal"))
        self._update_fs_lock_visual()

        ox = int(self.fs_module_offset_x)
        oy = int(self.fs_module_offset_y)
        lx_ox = ox + int(self.fs_lx_offset_x)
        lx_oy = oy + int(self.fs_lx_offset_y)
        brake_ox = ox + int(self.fs_brake_offset_x)
        brake_oy = oy + int(self.fs_brake_offset_y)
        gas_ox = ox + int(self.fs_gas_offset_x)
        gas_oy = oy + int(self.fs_gas_offset_y)
        center_x = sw // 2
        alpha = clamp(self.fullscreen_alpha, 0.0, 1.0)
        if alpha >= 0.85:
            fs_stipple = ""
        elif alpha >= 0.65:
            fs_stipple = "gray75"
        elif alpha >= 0.45:
            fs_stipple = "gray50"
        elif alpha >= 0.25:
            fs_stipple = "gray25"
        else:
            fs_stipple = "gray12"
        lx_w = int(sw * 0.34)
        lx_h = max(20, int(sh * 0.028))
        lx_y = int(sh * 0.75)
        self.scene["lx_track"] = c.create_rectangle(center_x - lx_w // 2 + lx_ox, lx_y - lx_h // 2 + lx_oy, center_x + lx_w // 2 + lx_ox, lx_y + lx_h // 2 + lx_oy, outline="#c7c7c7", fill="#000000", stipple=fs_stipple)
        c.create_line(center_x + lx_ox, lx_y - lx_h // 2 - 8 + lx_oy, center_x + lx_ox, lx_y + lx_h // 2 + 8 + lx_oy, fill="#e7eef5", width=2)
        self.scene["lx_fill"] = c.create_rectangle(center_x + lx_ox, lx_y - lx_h // 2 + 2 + lx_oy, center_x + lx_ox, lx_y + lx_h // 2 - 2 + lx_oy, outline="", fill="#67b7ff")
        bar_h = int(sh * 0.26)
        bar_w = max(18, int(sw * 0.012))
        bars_y0 = int(sh * 0.64) - bar_h // 2
        bars_y1 = bars_y0 + bar_h
        bx = int(sw * 0.70)
        gx = int(sw * 0.77)
        self.scene["brake_track"] = c.create_rectangle(bx + brake_ox, bars_y0 + brake_oy, bx + bar_w + brake_ox, bars_y1 + brake_oy, outline="#c7c7c7", fill="#000000", stipple=fs_stipple)
        self.scene["brake_fill"] = c.create_rectangle(bx + 1 + brake_ox, bars_y1 - 1 + brake_oy, bx + bar_w - 1 + brake_ox, bars_y1 - 1 + brake_oy, outline="", fill="#ff6b6b")
        self.scene["gas_track"] = c.create_rectangle(gx + gas_ox, bars_y0 + gas_oy, gx + bar_w + gas_ox, bars_y1 + gas_oy, outline="#c7c7c7", fill="#000000", stipple=fs_stipple)
        self.scene["gas_fill"] = c.create_rectangle(gx + 1 + gas_ox, bars_y1 - 1 + gas_oy, gx + bar_w - 1 + gas_ox, bars_y1 - 1 + gas_oy, outline="", fill="#37d45c")
        c.create_text(bx + bar_w // 2 + brake_ox, bars_y1 + 36 + brake_oy, text=self._t("app.label.brake", "刹车"), fill="#ffffff", font=("Segoe UI", self._font(13), "bold"))
        c.create_text(gx + bar_w // 2 + gas_ox, bars_y1 + 36 + gas_oy, text=self._t("app.label.gas", "油门"), fill="#ffffff", font=("Segoe UI", self._font(13), "bold"))
        self.scene["brake_box"] = c.create_rectangle(bx - 22 + brake_ox, bars_y0 + brake_oy, bx - 8 + brake_ox, bars_y0 + 14 + brake_oy, outline="#c7c7c7", fill="")
        self.scene["gas_box"] = c.create_rectangle(gx + bar_w + 8 + gas_ox, bars_y0 + gas_oy, gx + bar_w + 22 + gas_ox, bars_y0 + 14 + gas_oy, outline="#c7c7c7", fill="")
        self.fs_lx_bounds = (
            center_x - lx_w // 2 + lx_ox - 10,
            lx_y - lx_h // 2 + lx_oy - 14,
            center_x + lx_w // 2 + lx_ox + 10,
            lx_y + lx_h // 2 + lx_oy + 14,
        )
        self.fs_brake_bounds = (
            bx - 26 + brake_ox,
            bars_y0 - 8 + brake_oy,
            bx + bar_w + 26 + brake_ox,
            bars_y1 + 54 + brake_oy,
        )
        self.fs_gas_bounds = (
            gx - 26 + gas_ox,
            bars_y0 - 8 + gas_oy,
            gx + bar_w + 26 + gas_ox,
            bars_y1 + 54 + gas_oy,
        )
        self.fs_module_bounds = (
            min(self.fs_lx_bounds[0], self.fs_brake_bounds[0], self.fs_gas_bounds[0]),
            min(self.fs_lx_bounds[1], self.fs_brake_bounds[1], self.fs_gas_bounds[1]),
            max(self.fs_lx_bounds[2], self.fs_brake_bounds[2], self.fs_gas_bounds[2]),
            max(self.fs_lx_bounds[3], self.fs_brake_bounds[3], self.fs_gas_bounds[3]),
        )

    def _update_fs_lock_visual(self) -> None:
        if "fs_lock_text" not in self.scene:
            return
        alpha = clamp(self.fullscreen_alpha, 0.0, 1.0)
        if alpha >= 0.85:
            fs_stipple = ""
        elif alpha >= 0.65:
            fs_stipple = "gray75"
        elif alpha >= 0.45:
            fs_stipple = "gray50"
        elif alpha >= 0.25:
            fs_stipple = "gray25"
        else:
            fs_stipple = "gray12"
        self.canvas.itemconfig(self.scene["fs_lock_text"], text=(ICON_LOCK if self.locked else ICON_UNLOCK))
        self.canvas.itemconfig(self.scene["fs_lock_bg"], fill=("#2d2d2d" if self.locked else "#196d2d"), stipple=fs_stipple)
        if "fs_settings_bg" in self.scene:
            self.canvas.itemconfig(self.scene["fs_settings_bg"], stipple=fs_stipple)

    def _in_fs_settings_bounds(self, x: int, y: int) -> bool:
        if not hasattr(self, "fs_settings_bounds"):
            return False
        x0, y0, x1, y1 = self.fs_settings_bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def _in_fs_lock_bounds(self, x: int, y: int) -> bool:
        if not hasattr(self, "fs_lock_bounds"):
            return False
        x0, y0, x1, y1 = self.fs_lock_bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def _in_fs_module_bounds(self, x: int, y: int) -> bool:
        if not hasattr(self, "fs_module_bounds"):
            return False
        x0, y0, x1, y1 = self.fs_module_bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def _in_fs_lx_bounds(self, x: int, y: int) -> bool:
        if not hasattr(self, "fs_lx_bounds"):
            return False
        x0, y0, x1, y1 = self.fs_lx_bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def _in_fs_brake_bounds(self, x: int, y: int) -> bool:
        if not hasattr(self, "fs_brake_bounds"):
            return False
        x0, y0, x1, y1 = self.fs_brake_bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def _in_fs_gas_bounds(self, x: int, y: int) -> bool:
        if not hasattr(self, "fs_gas_bounds"):
            return False
        x0, y0, x1, y1 = self.fs_gas_bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def _init_scene(self) -> None:
        self._clear_scene()
        if self.fullscreen_mode:
            self._init_scene_fullscreen()
        else:
            self._init_scene_windowed()

    def _font(self, base_size: int) -> int:
        return max(8, int(round(base_size * self.ui_scale)))

    def _effective_scale(self, base_scale: float) -> float:
        return max(1.15, base_scale * 1.15)

    def _apply_ui_scale(self) -> None:
        self.ui_scale = self._effective_scale(self.fullscreen_scale if self.fullscreen_mode else self.window_scale)
        self.window_pad_x = max(8, int(round(10 * self.ui_scale)))
        self.window_pad_y = max(3, int(round(4 * self.ui_scale)))
        self.lock_button_pack_kwargs = {"side": "right", "padx": self.window_pad_x, "pady": self.window_pad_y}
        self.settings_button_pack_kwargs = {"side": "right", "padx": (0, 6), "pady": self.window_pad_y}
        self.status_label.configure(font=("Segoe UI", self._font(14), "bold"))
        self.lock_button.configure(font=(ICON_FONT_FAMILY, self._font(9), "normal"))
        self.settings_button.configure(font=(ICON_FONT_FAMILY, self._font(9), "normal"))
        self.error_label.configure(font=("Segoe UI", self._font(8)))
        self.debug_label.configure(font=("Consolas", self._font(8)))

    def _get_live_settings(self) -> dict:
        if callable(self.settings_getter):
            return dict(self.settings_getter())
        return {
            "language": self.language,
            "hud_fps": self.hud_fps,
            "window_scale": self.window_scale,
            "fullscreen_scale": self.fullscreen_scale,
            "fullscreen_alpha": self.fullscreen_alpha,
            "min_output_x": self.min_output_x,
        }

    def open_settings_panel(self) -> None:
        self._settings_debug_log("open_settings_panel called")
        if self.settings_webview_proc is not None and self.settings_webview_proc.poll() is None:
            self._settings_debug_log("webview already running")
            self.local_error_text = self._t("app.error.settings_window_running", "设置窗口已在运行")
            return
        baseline = self._get_live_settings()
        self._settings_debug_log(f"baseline={baseline}")
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            candidates = [
                exe_dir / "settings_webview.exe",
                exe_dir / "settings_webview" / "settings_webview.exe",
                exe_dir.parent / "settings_webview" / "settings_webview.exe",
            ]
            settings_entry = None
            for p in candidates:
                if p.exists():
                    settings_entry = p
                    break
            launch_cmd = [str(settings_entry)] if settings_entry is not None else []
            missing_text = "未找到 settings_webview.exe"
            missing_log = "settings_webview.exe missing"
        else:
            settings_entry = APP_BASE_DIR / "settings_webview.py"
            launch_cmd = [sys.executable, str(settings_entry)]
            missing_text = "未找到 settings_webview.py"
            missing_log = "settings_webview.py missing"

        if settings_entry is None or not settings_entry.exists():
            self.local_error_text = self._t("app.error.settings_script_missing", missing_text)
            self._settings_debug_log(missing_log)
            return
        try:
            with open(self.settings_state_path, "w", encoding="utf-8") as f:
                json.dump(baseline, f, ensure_ascii=False)
            if self.settings_webview_log_handle is not None:
                try:
                    self.settings_webview_log_handle.close()
                except Exception:
                    pass
                self.settings_webview_log_handle = None
            self._settings_debug_log("starting settings_webview subprocess")
            self.settings_webview_proc = subprocess.Popen(
                launch_cmd + ["--ipc", self.settings_ipc_path, "--state-file", self.settings_state_path],
                cwd=str(APP_BASE_DIR),
            )
            self.local_error_text = f"{self._t('app.error.settings_window_starting', '设置窗口启动中')} pid={self.settings_webview_proc.pid}"
            if callable(self.settings_open_callback):
                self.settings_open_callback(True)
            self.root.after(900, self._check_settings_webview_started)
        except Exception as exc:
            self.local_error_text = f"{self._t('app.error.settings_window_open_fail', '打开Web设置窗口失败')}: {exc}"
            self._settings_debug_log(f"subprocess start failed: {exc}")

    def _settings_debug_log(self, msg: str) -> None:
        try:
            line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
            with open(self.settings_debug_log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def _check_settings_webview_started(self) -> None:
        try:
            p = self.settings_webview_proc
            if p is None:
                self.local_error_text = self._t("app.error.settings_window_process_empty", "设置窗口未启动(进程对象为空)")
                self._settings_debug_log("check: process is None")
                return
            rc = p.poll()
            if rc is None:
                self.local_error_text = f"{self._t('app.error.settings_window_running', '设置窗口已在运行')} pid={p.pid}"
                self._settings_debug_log(f"check: running pid={p.pid}")
                return
            if callable(self.settings_open_callback):
                self.settings_open_callback(False)
            self._settings_debug_log(f"check: exited rc={rc}")
            tail = ""
            try:
                with open(self.settings_debug_log_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()
                tail = data[-240:].replace("\n", " | ")
            except Exception:
                pass
            self.local_error_text = f"{self._t('app.error.settings_window_start_fail', '设置窗口启动失败')} rc={rc} log:{tail}"
        except Exception as exc:
            self.local_error_text = f"{self._t('app.error.settings_window_check_fail', '检查设置窗口状态失败')}: {exc}"

    def _apply_settings_values(self, values: dict, save_to_file: bool) -> None:
        try:
            requested_fps = int(values.get("hud_fps", self.hud_fps))
        except Exception:
            requested_fps = self.hud_fps
        self.hud_fps = requested_fps if requested_fps in self.hud_fps_options_getter() else 60
        self.hud_interval_ms = max(1, int(1000 / self.hud_fps))
        lang = str(values.get("language", self.language)).strip()
        self.language = lang if lang in {"zh-CN", "en-US"} else "zh-CN"
        self.i18n = self.i18n_loader(self.language)
        self.window_scale = clamp(float(values["window_scale"]), 0.8, 1.5)
        self.fullscreen_scale = clamp(float(values["fullscreen_scale"]), 0.8, 1.5)
        self.fullscreen_alpha = clamp(float(values.get("fullscreen_alpha", self.fullscreen_alpha)), 0.0, 1.0)
        self.min_output_x = clamp(float(values["min_output_x"]), 0.0, 1.0)
        if callable(self.settings_apply_callback):
            self.settings_apply_callback(dict(values), save_to_file)
        self.root.title(self._t("app.window.title", "Mouse -> Virtual Gamepad"))
        self._apply_ui_scale()
        self._init_scene()
        if not self.fullscreen_mode:
            self.root.attributes("-alpha", 0.92)
        if not self.fullscreen_mode:
            self.position_bottom_right()

    def _draw_lx(self, lx: float) -> None:
        # Display scale for steering:
        # [-1, -min); 0; (min, 1]
        # i.e. re-normalize non-zero output so min_output starts visually near center.
        ax = abs(lx)
        if ax <= 0.0:
            view = 0.0
        elif ax <= self.min_output_x:
            view = 0.0
        else:
            den = max(1e-6, 1.0 - self.min_output_x)
            view = clamp((ax - self.min_output_x) / den, 0.0, 1.0)
            view = view if lx >= 0 else -view
        x0, y0, x1, y1 = self.canvas.coords(self.scene["lx_track"])
        cx = (x0 + x1) / 2.0
        half = (x1 - x0) / 2.0
        left = cx + (half * min(0.0, view))
        right = cx + (half * max(0.0, view))
        self.canvas.coords(self.scene["lx_fill"], left, y0 + 1, right, y1 - 1)

    def _poll_settings_ipc(self) -> None:
        try:
            if self.settings_webview_proc is not None:
                rc = self.settings_webview_proc.poll()
                if rc is not None:
                    self._settings_debug_log(f"settings process exited rc={rc}")
                    self.settings_webview_proc = None
                    if callable(self.settings_open_callback):
                        self.settings_open_callback(False)
            if os.path.exists(self.settings_ipc_path):
                with open(self.settings_ipc_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                ts = float(payload.get("ts", 0.0))
                if ts > self.settings_ipc_last_ts:
                    self.settings_ipc_last_ts = ts
                    values = payload.get("values")
                    if isinstance(values, dict):
                        self._apply_settings_values(values, save_to_file=True)
                        self.local_error_text = "设置已应用"
                    if payload.get("close", False) and self.settings_webview_proc is not None:
                        if self.settings_webview_proc.poll() is None:
                            self.settings_webview_proc = None
                        if callable(self.settings_open_callback):
                            self.settings_open_callback(False)
        except Exception:
            pass
        finally:
            self.root.after(250, self._poll_settings_ipc)

    def _draw_pedals(self, gas: bool, brake: bool, rt: float, lt: float) -> None:
        lt = clamp(lt, 0.0, 1.0)
        rt = clamp(rt, 0.0, 1.0)

        brake_x0, brake_y0, brake_x1, brake_y1 = self.canvas.coords(self.scene["brake_track"])
        gas_x0, gas_y0, gas_x1, gas_y1 = self.canvas.coords(self.scene["gas_track"])
        if self.fullscreen_mode:
            brake_fill_y0 = brake_y1 - (brake_y1 - brake_y0) * lt
            gas_fill_y0 = gas_y1 - (gas_y1 - gas_y0) * rt
            self.canvas.coords(self.scene["brake_fill"], brake_x0 + 1, brake_fill_y0 + 1, brake_x1 - 1, brake_y1 - 1)
            self.canvas.coords(self.scene["gas_fill"], gas_x0 + 1, gas_fill_y0 + 1, gas_x1 - 1, gas_y1 - 1)
        else:
            brake_fill_x1 = brake_x0 + (brake_x1 - brake_x0) * lt
            gas_fill_x1 = gas_x0 + (gas_x1 - gas_x0) * rt
            self.canvas.coords(self.scene["brake_fill"], brake_x0 + 1, brake_y0 + 1, brake_fill_x1 - 1 if brake_fill_x1 > brake_x0 + 2 else brake_x0 + 1, brake_y1 - 1)
            self.canvas.coords(self.scene["gas_fill"], gas_x0 + 1, gas_y0 + 1, gas_fill_x1 - 1 if gas_fill_x1 > gas_x0 + 2 else gas_x0 + 1, gas_y1 - 1)
        self.canvas.itemconfig(self.scene["gas_box"], fill="#37d45c" if gas else "#2a2a2a")
        self.canvas.itemconfig(self.scene["brake_box"], fill="#ff6b6b" if brake else "#2a2a2a")

    def apply_view_mode(self, fullscreen_enabled: bool) -> None:
        changed = self.fullscreen_mode != fullscreen_enabled
        self.fullscreen_mode = fullscreen_enabled
        self._apply_ui_scale()
        if not changed and self.scene:
            return
        if self.fullscreen_mode:
            self.root.attributes("-alpha", 1.0)
            self.root.configure(bg=self.fullscreen_bg_key)
            try:
                self.root.attributes("-transparentcolor", self.fullscreen_bg_key)
            except Exception:
                pass
            self.frame.configure(bg=self.fullscreen_bg_key, bd=0)
            self.header.configure(bg=self.fullscreen_bg_key)
            self.status_label.configure(bg=self.fullscreen_bg_key)
            self.error_label.configure(bg=self.fullscreen_bg_key)
            self.debug_label.configure(bg=self.fullscreen_bg_key)
            self.canvas.configure(bg=self.fullscreen_bg_key)
            self.lock_button.pack_forget()
            self.settings_button.pack_forget()
            self.header.pack_forget()
            self.error_label.pack_forget()
            self.debug_label.pack_forget()
            self.canvas.pack_forget()
            self.canvas.pack(fill="both", expand=True, padx=0, pady=0)
            self.fullscreen_available = True
            self.position_fullscreen_overlay()
            self.window_clickthrough_setter(self.root.winfo_id(), False)
        else:
            self.root.attributes("-alpha", 0.92)
            try:
                self.root.attributes("-transparentcolor", "")
            except Exception:
                pass
            self.frame.configure(bg="#1f1f1f", bd=1, relief="solid")
            self.header.configure(bg="#1f1f1f")
            self.status_label.configure(bg="#1f1f1f")
            self.error_label.configure(bg="#1f1f1f")
            self.debug_label.configure(bg="#1f1f1f")
            self.canvas.configure(bg="#171717")
            if not self.header.winfo_manager():
                self.header.pack(fill="x")
            if not self.lock_button.winfo_manager():
                self.lock_button.pack(**self.lock_button_pack_kwargs)
            if not self.settings_button.winfo_manager():
                self.settings_button.pack(**self.settings_button_pack_kwargs)
            self.canvas.pack_forget()
            self.canvas.pack(fill="both", expand=True)
            if not self.error_label.winfo_manager():
                self.error_label.pack(fill="x")
            if not self.debug_label.winfo_manager():
                self.debug_label.pack(fill="x")
            self.window_clickthrough_setter(self.root.winfo_id(), False)
            self.position_bottom_right()
        self._init_scene()

    def update(
        self,
        state: MapperState,
        mode: int,
        fullscreen_enabled: bool,
        fullscreen_rect: tuple[int, int, int, int] | None,
    ) -> None:
        self.set_fullscreen_rect(fullscreen_rect)
        self.apply_view_mode(fullscreen_enabled)
        self.status_label.config(text=(self._t("app.status.on", "Status: ON") if state.enabled else self._t("app.status.off", "Status: OFF")), fg="#7dff9b" if state.enabled else "#ff6b6b")
        self._draw_lx(state.left_x)
        self._draw_pedals(state.gas_active, state.brake_active, state.rt, state.lt)
        shown_error = self.local_error_text if self.local_error_text else state.last_error
        self.error_label.config(text=shown_error)
        if self.debug_mode:
            self.debug_label.config(text=state.debug_text)
        else:
            self.debug_label.config(text="")
        if self.fullscreen_mode:
            self.canvas.itemconfig(self.scene["status_text"], text=(self._t("app.status.on", "Status: ON") if state.enabled else self._t("app.status.off", "Status: OFF")), fill=("#7dff9b" if state.enabled else "#ff6b6b"))
            self.canvas.itemconfig(self.scene["error_text"], text=shown_error)
            self.canvas.itemconfig(self.scene["debug_text"], text=(state.debug_text if self.debug_mode else ""))
    def loop(
        self,
        state_getter,
        mode_getter,
        fullscreen_getter,
        fullscreen_rect_getter,
        fullscreen_state_setter,
        open_settings_request_getter,
        stop_event: threading.Event,
    ) -> None:
        def tick() -> None:
            if stop_event.is_set():
                self._stop_tray_icon()
                self.root.destroy()
                return
            if callable(open_settings_request_getter):
                try:
                    if open_settings_request_getter():
                        self.open_settings_panel()
                except Exception:
                    pass
            self.update(
                state_getter(),
                mode_getter(),
                fullscreen_getter(),
                fullscreen_rect_getter(),
            )
            fullscreen_state_setter(self.fullscreen_mode, self.fullscreen_available)
            self.root.after(self.hud_interval_ms, tick)

        tick()
        try:
            self.root.mainloop()
        finally:
            self._stop_tray_icon()

