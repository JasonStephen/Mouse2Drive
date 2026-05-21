import configparser
import ctypes
import threading
import time
import tkinter as tk
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

import vgamepad as vg
from pynput import keyboard, mouse


CONFIG_PATH = Path(__file__).with_name("config.cfg")
POLL_INTERVAL = 0.01


@dataclass
class AppConfig:
    control_mode: int = 1
    reference_range_x_px: float = 360.0
    reference_range_y_px: float = 260.0
    min_output_x: float = 0.23
    debug_mode: bool = False
    hud_fps: int = 25
    gear_pulse_ms: int = 45
    toggle_hotkey: str = "shift+v"
    switch_mode_hotkey: str = "alt+shift+v"
    toggle_fullscreen_hotkey: str = "alt+f"
    gas_mouse_button: str = "right"
    brake_mouse_button: str = "left"
    gear_up_button: str = "right_shoulder"
    gear_down_button: str = "left_shoulder"
    hide_cursor_on_enable: bool = True
    windows_scale: float = 1.0
    fullscreen_alpha: float = 0.00


@dataclass
class MapperState:
    enabled: bool = False
    left_x: float = 0.0
    right_y: float = 0.0
    rt: float = 0.0
    lt: float = 0.0
    gas_active: bool = False
    brake_active: bool = False
    debug_text: str = ""
    last_error: str = ""


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def to_xinput_short(v: float) -> int:
    v = clamp(v, -1.0, 1.0)
    return int(v * 32767) if v >= 0 else int(v * 32768)


def parse_hotkey_combo(combo: str) -> set[str]:
    return {p.strip().lower() for p in combo.split("+") if p.strip()}


def normalize_key_token(key) -> str | None:
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return key.char.lower()
        return None
    if isinstance(key, keyboard.Key):
        name = key.name.lower()
        if name.startswith("shift"):
            return "shift"
        if name.startswith("alt"):
            return "alt"
        if name.startswith("ctrl"):
            return "ctrl"
        return name
    return None


def resolve_mouse_button(name: str):
    n = name.strip().lower()
    mapping = {
        "left": mouse.Button.left,
        "right": mouse.Button.right,
        "middle": mouse.Button.middle,
    }
    return mapping.get(n, mouse.Button.right)


def resolve_gamepad_button(name: str):
    n = name.strip().lower()
    mapping = {
        "right_shoulder": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "left_shoulder": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "x": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "dpad_up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "dpad_down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        "dpad_left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "dpad_right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    }
    return mapping.get(n, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)


def set_cursor_visible(visible: bool) -> None:
    try:
        user32 = ctypes.windll.user32
        # ShowCursor uses an internal display counter. Loop to enforce state.
        if visible:
            for _ in range(8):
                if user32.ShowCursor(True) >= 0:
                    break
        else:
            for _ in range(8):
                if user32.ShowCursor(False) < 0:
                    break
    except Exception:
        pass


def set_window_clickthrough(hwnd: int, enabled: bool) -> None:
    try:
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_NOACTIVATE = 0x08000000
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enabled:
            style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        else:
            style = style & ~WS_EX_TRANSPARENT & ~WS_EX_NOACTIVATE
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception:
        pass


def _hex_to_colorref(hex_color: str) -> int:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return 0
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (b << 16) | (g << 8) | r


def set_window_colorkey(hwnd: int, hex_color: str) -> bool:
    try:
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        LWA_COLORKEY = 0x00000001
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        key = _hex_to_colorref(hex_color)
        return bool(user32.SetLayeredWindowAttributes(hwnd, key, 0, LWA_COLORKEY))
    except Exception:
        return False


def verify_window_colorkey(hwnd: int) -> bool:
    try:
        LWA_COLORKEY = 0x00000001
        user32 = ctypes.windll.user32
        cr_key = wintypes.DWORD(0)
        alpha = ctypes.c_ubyte(0)
        flags = wintypes.DWORD(0)
        ok = user32.GetLayeredWindowAttributes(hwnd, ctypes.byref(cr_key), ctypes.byref(alpha), ctypes.byref(flags))
        return bool(ok) and bool(flags.value & LWA_COLORKEY)
    except Exception:
        return False


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def get_monitor_rect_from_point(x: int, y: int) -> tuple[int, int, int, int]:
    try:
        user32 = ctypes.windll.user32
        pt = POINT(int(x), int(y))
        MONITOR_DEFAULTTONEAREST = 2
        hmon = user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
        if not hmon:
            raise RuntimeError("MonitorFromPoint failed")
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            raise RuntimeError("GetMonitorInfoW failed")
        left = int(mi.rcMonitor.left)
        top = int(mi.rcMonitor.top)
        width = int(mi.rcMonitor.right - mi.rcMonitor.left)
        height = int(mi.rcMonitor.bottom - mi.rcMonitor.top)
        return (left, top, max(1, width), max(1, height))
    except Exception:
        return (0, 0, 0, 0)


def load_config() -> AppConfig:
    cfg = AppConfig()
    parser = configparser.ConfigParser()

    if not CONFIG_PATH.exists():
        save_default_config(cfg)
        return cfg

    parser.read(CONFIG_PATH, encoding="utf-8-sig")
    section = "mapping"

    if parser.has_section(section):
        cfg.control_mode = parser.getint(section, "control_mode", fallback=cfg.control_mode)
        cfg.reference_range_x_px = parser.getfloat(section, "reference_range_x_px", fallback=cfg.reference_range_x_px)
        cfg.reference_range_y_px = parser.getfloat(section, "reference_range_y_px", fallback=cfg.reference_range_y_px)
        cfg.min_output_x = parser.getfloat(section, "min_output_x", fallback=cfg.min_output_x)
        cfg.debug_mode = parser.getboolean(section, "debug_mode", fallback=cfg.debug_mode)
        cfg.hud_fps = parser.getint(section, "hud_fps", fallback=cfg.hud_fps)
        cfg.gear_pulse_ms = parser.getint(section, "gear_pulse_ms", fallback=cfg.gear_pulse_ms)
        cfg.toggle_hotkey = parser.get(section, "toggle_hotkey", fallback=cfg.toggle_hotkey)
        cfg.switch_mode_hotkey = parser.get(section, "switch_mode_hotkey", fallback=cfg.switch_mode_hotkey)
        cfg.toggle_fullscreen_hotkey = parser.get(section, "toggle_fullscreen_hotkey", fallback=cfg.toggle_fullscreen_hotkey)
        cfg.gas_mouse_button = parser.get(section, "gas_mouse_button", fallback=cfg.gas_mouse_button)
        cfg.brake_mouse_button = parser.get(section, "brake_mouse_button", fallback=cfg.brake_mouse_button)
        cfg.gear_up_button = parser.get(section, "gear_up_button", fallback=cfg.gear_up_button)
        cfg.gear_down_button = parser.get(section, "gear_down_button", fallback=cfg.gear_down_button)
        cfg.hide_cursor_on_enable = parser.getboolean(section, "hide_cursor_on_enable", fallback=cfg.hide_cursor_on_enable)
        cfg.windows_scale = parser.getfloat(section, "windows_scale", fallback=cfg.windows_scale)
        cfg.fullscreen_alpha = parser.getfloat(section, "fullscreen_alpha", fallback=cfg.fullscreen_alpha)

    if cfg.control_mode < 1 or cfg.control_mode > 4:
        cfg.control_mode = 1
    cfg.reference_range_x_px = max(1.0, cfg.reference_range_x_px)
    cfg.reference_range_y_px = max(1.0, cfg.reference_range_y_px)
    cfg.min_output_x = clamp(cfg.min_output_x, 0.0, 0.95)
    cfg.hud_fps = int(clamp(cfg.hud_fps, 5, 240))
    cfg.gear_pulse_ms = int(clamp(cfg.gear_pulse_ms, 10, 300))
    cfg.windows_scale = clamp(cfg.windows_scale, 0.8, 2.0)
    cfg.fullscreen_alpha = clamp(cfg.fullscreen_alpha, 0.0, 0.95)
    return cfg


def save_default_config(cfg: AppConfig) -> None:
    parser = configparser.ConfigParser()
    parser["mapping"] = {
        "control_mode": str(cfg.control_mode),
        "reference_range_x_px": str(cfg.reference_range_x_px),
        "reference_range_y_px": str(cfg.reference_range_y_px),
        "min_output_x": str(cfg.min_output_x),
        "debug_mode": str(cfg.debug_mode).lower(),
        "hud_fps": str(cfg.hud_fps),
        "gear_pulse_ms": str(cfg.gear_pulse_ms),
        "toggle_hotkey": cfg.toggle_hotkey,
        "switch_mode_hotkey": cfg.switch_mode_hotkey,
        "toggle_fullscreen_hotkey": cfg.toggle_fullscreen_hotkey,
        "gas_mouse_button": cfg.gas_mouse_button,
        "brake_mouse_button": cfg.brake_mouse_button,
        "gear_up_button": cfg.gear_up_button,
        "gear_down_button": cfg.gear_down_button,
        "hide_cursor_on_enable": str(cfg.hide_cursor_on_enable).lower(),
        "windows_scale": f"{cfg.windows_scale:.2f}",
        "fullscreen_alpha": f"{cfg.fullscreen_alpha:.2f}",
    }
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        parser.write(f)


class Indicator:
    def __init__(
        self,
        debug_mode: bool = False,
        hud_fps: int = 25,
        min_output_x: float = 0.23,
        windows_scale: float = 1.0,
        fullscreen_alpha: float = 0.00,
    ) -> None:
        self.debug_mode = debug_mode
        self.hud_fps = int(clamp(hud_fps, 5, 240))
        self.hud_interval_ms = max(1, int(1000 / self.hud_fps))
        self.min_output_x = clamp(min_output_x, 0.0, 0.95)
        self.ui_scale = max(1.15, windows_scale * 1.15)
        self.fullscreen_alpha = clamp(fullscreen_alpha, 0.0, 0.95)
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
        self.root.title("Mouse -> Virtual Gamepad")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        self.frame = tk.Frame(self.root, bg="#1f1f1f", bd=1, relief="solid")
        self.frame.pack(fill="both", expand=True)
        self.header = tk.Frame(self.frame, bg="#1f1f1f")
        self.header.pack(fill="x")
        self.status_label = tk.Label(self.header, text="状态: OFF", fg="#ff6b6b", bg="#1f1f1f", font=("Segoe UI", self._font(10), "bold"), anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.lock_button = tk.Button(self.header, text="锁定", command=self.toggle_lock, bg="#2b2b2b", fg="#f0f0f0", activebackground="#3a3a3a", activeforeground="#ffffff", bd=0, font=("Segoe UI", self._font(8), "bold"))
        self.lock_button.pack(side="right")
        self.mode_label = tk.Label(self.frame, text="模式: 1", fg="#b7d8ff", bg="#1f1f1f", font=("Segoe UI", self._font(9)), anchor="w", justify="left")
        self.mode_label.pack(fill="x")
        self.canvas = tk.Canvas(self.frame, width=100, height=100, bg="#171717", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.error_label = tk.Label(self.frame, text="", fg="#ffcc66", bg="#1f1f1f", font=("Segoe UI", self._font(8)), anchor="w", justify="left")
        self.error_label.pack(fill="x")
        self.debug_label = tk.Label(self.frame, text="", fg="#9fd6ff", bg="#1f1f1f", font=("Consolas", self._font(8)), anchor="w", justify="left")
        self.debug_label.pack(fill="x")
        self.window_pad_x = max(8, int(round(10 * self.ui_scale)))
        self.window_pad_y = max(3, int(round(4 * self.ui_scale)))
        self.lock_button_pack_kwargs = {"side": "right", "padx": max(8, int(round(10 * self.ui_scale))), "pady": max(3, int(round(4 * self.ui_scale)))}
        self._bind_drag_for_widget(self.frame)
        self.root.bind("<Configure>", lambda _e: self.ensure_on_screen())
        self.root.update_idletasks()
        self.apply_view_mode(False)
        self._init_scene()

    def position_bottom_right(self) -> None:
        self.root.update_idletasks()
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
        self.lock_button.config(text="锁定" if self.locked else "解锁")

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

    def _on_fullscreen_drag_start(self, event) -> None:
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
        c.create_text(x(34), y(68), text="刹车", fill="#ffcdd2", font=("Segoe UI", self._font(9)))
        self.scene["brake_track"] = c.create_rectangle(x(60), y(60), x(150), y(74), outline="#8a8a8a", fill="#2a2a2a")
        self.scene["brake_fill"] = c.create_rectangle(x(61), y(61), x(61), y(73), outline="", fill="#ff6b6b")
        self.scene["brake_box"] = c.create_rectangle(x(154), y(60), x(166), y(74), outline="#8a8a8a", fill="#2a2a2a")
        c.create_text(x(222), y(68), text="油门", fill="#c8e6c9", font=("Segoe UI", self._font(9)))
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
        self.scene["status_text"] = c.create_text(28, 28, text="状态: OFF", fill="#ffffff", font=("Segoe UI", self._font(20), "bold"), anchor="nw")
        self.scene["mode_text"] = c.create_text(28, 28 + self._font(20) + 14, text="模式: -", fill="#ffffff", font=("Segoe UI", self._font(16), "bold"), anchor="nw")
        self.scene["error_text"] = c.create_text(28, sh - 28, text="", fill="#ffffff", font=("Segoe UI", self._font(16), "bold"), anchor="sw")
        self.scene["debug_text"] = c.create_text(28, sh - 28 - self._font(16) - 10, text="", fill="#d6f0ff", font=("Consolas", self._font(12)), anchor="sw")
        # Fullscreen lock toggle (top-right)
        lock_w, lock_h = 116, 44
        lock_x1 = sw - 24
        lock_y0 = 24
        lock_x0 = lock_x1 - lock_w
        lock_y1 = lock_y0 + lock_h
        self.fs_lock_bounds = (lock_x0, lock_y0, lock_x1, lock_y1)
        self.scene["fs_lock_bg"] = c.create_rectangle(lock_x0, lock_y0, lock_x1, lock_y1, outline="#d0d0d0", width=2)
        self.scene["fs_lock_text"] = c.create_text((lock_x0 + lock_x1) // 2, (lock_y0 + lock_y1) // 2, text="", fill="#ffffff", font=("Segoe UI", self._font(11), "bold"))
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
        lx_w = int(sw * 0.34)
        lx_h = max(20, int(sh * 0.028))
        lx_y = int(sh * 0.75)
        self.scene["lx_track"] = c.create_rectangle(center_x - lx_w // 2 + lx_ox, lx_y - lx_h // 2 + lx_oy, center_x + lx_w // 2 + lx_ox, lx_y + lx_h // 2 + lx_oy, outline="#c7c7c7", fill="#000000", stipple="gray50")
        c.create_line(center_x + lx_ox, lx_y - lx_h // 2 - 8 + lx_oy, center_x + lx_ox, lx_y + lx_h // 2 + 8 + lx_oy, fill="#e7eef5", width=2)
        self.scene["lx_fill"] = c.create_rectangle(center_x + lx_ox, lx_y - lx_h // 2 + 2 + lx_oy, center_x + lx_ox, lx_y + lx_h // 2 - 2 + lx_oy, outline="", fill="#67b7ff")
        bar_h = int(sh * 0.26)
        bar_w = max(18, int(sw * 0.012))
        bars_y0 = int(sh * 0.64) - bar_h // 2
        bars_y1 = bars_y0 + bar_h
        bx = int(sw * 0.70)
        gx = int(sw * 0.77)
        self.scene["brake_track"] = c.create_rectangle(bx + brake_ox, bars_y0 + brake_oy, bx + bar_w + brake_ox, bars_y1 + brake_oy, outline="#c7c7c7", fill="#000000", stipple="gray50")
        self.scene["brake_fill"] = c.create_rectangle(bx + 1 + brake_ox, bars_y1 - 1 + brake_oy, bx + bar_w - 1 + brake_ox, bars_y1 - 1 + brake_oy, outline="", fill="#ff6b6b")
        self.scene["gas_track"] = c.create_rectangle(gx + gas_ox, bars_y0 + gas_oy, gx + bar_w + gas_ox, bars_y1 + gas_oy, outline="#c7c7c7", fill="#000000", stipple="gray50")
        self.scene["gas_fill"] = c.create_rectangle(gx + 1 + gas_ox, bars_y1 - 1 + gas_oy, gx + bar_w - 1 + gas_ox, bars_y1 - 1 + gas_oy, outline="", fill="#37d45c")
        c.create_text(bx + bar_w // 2 + brake_ox, bars_y1 + 36 + brake_oy, text="刹车", fill="#ffffff", font=("Segoe UI", self._font(13), "bold"))
        c.create_text(gx + bar_w // 2 + gas_ox, bars_y1 + 36 + gas_oy, text="油门", fill="#ffffff", font=("Segoe UI", self._font(13), "bold"))
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
        self.canvas.itemconfig(self.scene["fs_lock_text"], text=("锁定" if self.locked else "解锁"))
        self.canvas.itemconfig(self.scene["fs_lock_bg"], fill=("#2d2d2d" if self.locked else "#196d2d"))

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
            self.mode_label.configure(bg=self.fullscreen_bg_key)
            self.error_label.configure(bg=self.fullscreen_bg_key)
            self.debug_label.configure(bg=self.fullscreen_bg_key)
            self.canvas.configure(bg=self.fullscreen_bg_key)
            self.lock_button.pack_forget()
            self.header.pack_forget()
            self.mode_label.pack_forget()
            self.error_label.pack_forget()
            self.debug_label.pack_forget()
            self.canvas.pack_forget()
            self.canvas.pack(fill="both", expand=True, padx=0, pady=0)
            self.fullscreen_available = True
            self.position_fullscreen_overlay()
            set_window_clickthrough(self.root.winfo_id(), False)
        else:
            self.root.attributes("-alpha", 0.92)
            try:
                self.root.attributes("-transparentcolor", "")
            except Exception:
                pass
            self.frame.configure(bg="#1f1f1f", bd=1, relief="solid")
            self.header.configure(bg="#1f1f1f")
            self.status_label.configure(bg="#1f1f1f")
            self.mode_label.configure(bg="#1f1f1f")
            self.error_label.configure(bg="#1f1f1f")
            self.debug_label.configure(bg="#1f1f1f")
            self.canvas.configure(bg="#171717")
            if not self.header.winfo_manager():
                self.header.pack(fill="x")
            if not self.lock_button.winfo_manager():
                self.lock_button.pack(**self.lock_button_pack_kwargs)
            if not self.mode_label.winfo_manager():
                self.mode_label.pack(fill="x")
            self.canvas.pack_forget()
            self.canvas.pack(fill="both", expand=True)
            if not self.error_label.winfo_manager():
                self.error_label.pack(fill="x")
            if not self.debug_label.winfo_manager():
                self.debug_label.pack(fill="x")
            set_window_clickthrough(self.root.winfo_id(), False)
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
        mode_names = {
            1: "方向+线性油刹",
            2: "方向+按键油刹",
            3: "仅线性油刹",
            4: "仅按键油刹",
        }
        self.status_label.config(text="状态: ON" if state.enabled else "状态: OFF", fg="#7dff9b" if state.enabled else "#ff6b6b")
        self.mode_label.config(text=f"模式{mode}: {mode_names.get(mode, '未知')}  (Shift+V开关 / Alt+Shift+V切模式)")
        self._draw_lx(state.left_x)
        self._draw_pedals(state.gas_active, state.brake_active, state.rt, state.lt)
        self.error_label.config(text=state.last_error)
        if self.debug_mode:
            self.debug_label.config(text=state.debug_text)
        else:
            self.debug_label.config(text="")
        if self.fullscreen_mode:
            self.canvas.itemconfig(self.scene["status_text"], text=("状态: ON" if state.enabled else "状态: OFF"), fill=("#7dff9b" if state.enabled else "#ff6b6b"))
            self.canvas.itemconfig(self.scene["mode_text"], text=f"模式{mode}: {mode_names.get(mode, '未知')}")
            self.canvas.itemconfig(self.scene["error_text"], text=state.last_error)
            self.canvas.itemconfig(self.scene["debug_text"], text=(state.debug_text if self.debug_mode else ""))
    def loop(
        self,
        state_getter,
        mode_getter,
        fullscreen_getter,
        fullscreen_rect_getter,
        fullscreen_state_setter,
        stop_event: threading.Event,
    ) -> None:
        def tick() -> None:
            if stop_event.is_set():
                self.root.destroy()
                return
            self.update(
                state_getter(),
                mode_getter(),
                fullscreen_getter(),
                fullscreen_rect_getter(),
            )
            fullscreen_state_setter(self.fullscreen_mode, self.fullscreen_available)
            self.root.after(self.hud_interval_ms, tick)

        tick()
        self.root.mainloop()


class MouseToVirtualGamepad:
    def __init__(self) -> None:
        self.config = load_config()
        self.state = MapperState()
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        self.pressed_keys: set[str] = set()
        self.handled_combos: set[str] = set()
        self.reference_pos: tuple[int, int] | None = None
        self.current_pos: tuple[int, int] | None = None

        self.right_button_down = False
        self.left_button_down = False
        self.gear_up_until = 0.0
        self.gear_down_until = 0.0

        self.mouse_controller = mouse.Controller()
        self.toggle_combo = parse_hotkey_combo(self.config.toggle_hotkey)
        self.switch_mode_combo = parse_hotkey_combo(self.config.switch_mode_hotkey)
        self.toggle_fullscreen_combo = parse_hotkey_combo(self.config.toggle_fullscreen_hotkey)
        self.gas_mouse_btn = resolve_mouse_button(self.config.gas_mouse_button)
        self.brake_mouse_btn = resolve_mouse_button(self.config.brake_mouse_button)
        self.gear_up_btn = resolve_gamepad_button(self.config.gear_up_button)
        self.gear_down_btn = resolve_gamepad_button(self.config.gear_down_button)
        self.cursor_hidden = False
        self.relative_center = None
        self.ignore_move_events = 0
        self.raw_last_pos = None
        self.axis_x = 0.0
        self.axis_y = 0.0
        self.hud_fullscreen_enabled = False
        self.hud_fullscreen_rect: tuple[int, int, int, int] | None = None
        self.hud_fullscreen_supported = True

        try:
            self.pad = vg.VX360Gamepad()
            self.state.last_error = "虚拟手柄已创建"
        except Exception as exc:
            self.pad = None
            self.state.last_error = f"虚拟手柄创建失败: {exc}"

    def set_reference_to_current_mouse(self) -> None:
        x, y = self.mouse_controller.position
        with self.lock:
            self.reference_pos = (int(x), int(y))
            self.current_pos = (int(x), int(y))
            self.state.left_x = 0.0
            self.state.right_y = 0.0

    def _virtual_screen_center(self) -> tuple[int, int]:
        x, y = self.mouse_controller.position
        left, top, width, height = get_monitor_rect_from_point(int(x), int(y))
        if width > 0 and height > 0:
            return (int(left + width // 2), int(top + height // 2))
        return (int(x), int(y))

    def _warp_to_center(self) -> None:
        if self.relative_center is None:
            self.relative_center = self._virtual_screen_center()
        cx, cy = self.relative_center
        self.ignore_move_events = 2
        self.mouse_controller.position = (cx, cy)
        self.raw_last_pos = (cx, cy)

    def _set_mapper_enabled(self, enabled: bool) -> None:
        self.state.enabled = enabled
        if enabled:
            self.axis_x = 0.0
            self.axis_y = 0.0
            self.set_reference_to_current_mouse()
            if self.config.hide_cursor_on_enable and not self.cursor_hidden:
                set_cursor_visible(False)
                self.cursor_hidden = True
            self.relative_center = self._virtual_screen_center()
            self._warp_to_center()
            self.state.last_error = "已开启"
        else:
            if self.cursor_hidden:
                set_cursor_visible(True)
                self.cursor_hidden = False
            self.reset_all()
            self.state.last_error = "已关闭并回中"

    def reset_all(self) -> None:
        self.set_reference_to_current_mouse()
        self.right_button_down = False
        self.left_button_down = False
        self.gear_up_until = 0.0
        self.gear_down_until = 0.0
        self.axis_x = 0.0
        self.axis_y = 0.0
        self.state.gas_active = False
        self.state.brake_active = False
        self.state.rt = 0.0
        self.state.lt = 0.0
        self.push_to_gamepad()

    def on_key_press(self, key) -> None:
        token = normalize_key_token(key)
        if token is None:
            return
        self.pressed_keys.add(token)

        if self._combo_just_pressed("switch_mode", self.switch_mode_combo):
            self.config.control_mode += 1
            if self.config.control_mode > 4:
                self.config.control_mode = 1
            self.state.last_error = f"已切换到模式{self.config.control_mode}"
            return

        if self._combo_just_pressed("toggle_mapper", self.toggle_combo):
            self._set_mapper_enabled(not self.state.enabled)
            return

        if self._combo_just_pressed("toggle_fullscreen", self.toggle_fullscreen_combo):
            want_fullscreen = not self.hud_fullscreen_enabled
            self.hud_fullscreen_enabled = want_fullscreen
            if self.hud_fullscreen_enabled:
                mx, my = self.mouse_controller.position
                rect = get_monitor_rect_from_point(int(mx), int(my))
                self.hud_fullscreen_rect = rect if rect[2] > 0 and rect[3] > 0 else None
            else:
                self.hud_fullscreen_rect = None
            self.state.last_error = "HUD全屏已开启 (Alt+F退出)" if self.hud_fullscreen_enabled else "HUD小窗模式"
            return

    def on_key_release(self, key) -> None:
        token = normalize_key_token(key)
        if token is not None:
            self.pressed_keys.discard(token)
            if token in {"alt", "shift", "ctrl"}:
                self.handled_combos.clear()

    def _combo_just_pressed(self, combo_id: str, combo_tokens: set[str]) -> bool:
        if not combo_tokens:
            return False
        if not combo_tokens.issubset(self.pressed_keys):
            self.handled_combos.discard(combo_id)
            return False
        if combo_id in self.handled_combos:
            return False
        self.handled_combos.add(combo_id)
        return True

    def on_mouse_move(self, x: int, y: int) -> None:
        do_warp = False
        with self.lock:
            if self.state.enabled:
                if self.ignore_move_events > 0:
                    self.ignore_move_events -= 1
                    self.raw_last_pos = (x, y)
                    return
                if self.raw_last_pos is None:
                    self.raw_last_pos = (x, y)
                    return
                dx = x - self.raw_last_pos[0]
                dy = y - self.raw_last_pos[1]
                self.raw_last_pos = (x, y)
                self.axis_x = clamp(self.axis_x + (dx / self.config.reference_range_x_px), -1.0, 1.0)
                self.axis_y = clamp(self.axis_y + (dy / self.config.reference_range_y_px), -1.0, 1.0)
                do_warp = True
            else:
                self.current_pos = (x, y)
        if do_warp:
            self._warp_to_center()
            return

    def on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        if button == self.gas_mouse_btn:
            self.right_button_down = pressed
        elif button == self.brake_mouse_btn:
            self.left_button_down = pressed

    def on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self.state.enabled:
            return
        now = time.time()
        pulse = self.config.gear_pulse_ms / 1000.0
        if dy > 0:
            self.gear_up_until = max(self.gear_up_until, now + pulse)
        elif dy < 0:
            self.gear_down_until = max(self.gear_down_until, now + pulse)

    def compute_state(self) -> None:
        if self.reference_pos is None or self.current_pos is None:
            return

        dx = self.current_pos[0] - self.reference_pos[0]
        dy = self.current_pos[1] - self.reference_pos[1]

        # Steering:
        # mode1/mode2: steering enabled by mouse X
        # mode3/mode4: pedal-only, no steering
        if self.config.control_mode in (1, 2):
            base_lx = self.axis_x
            abs_base_lx = abs(base_lx)
            if abs_base_lx > 0.0:
                abs_lx = self.config.min_output_x + (1.0 - self.config.min_output_x) * abs_base_lx
                lx = (1.0 if base_lx >= 0 else -1.0) * clamp(abs_lx, 0.0, 1.0)
            else:
                lx = 0.0
        else:
            lx = 0.0

        # Pedals are now RT/LT in all modes.
        # mode1/mode3: linear RT/LT by mouse Y
        # mode2/mode4: digital RT/LT by mouse buttons
        if self.config.control_mode in (1, 3):
            pedal = self.axis_y
            if pedal < 0.0:
                self.state.rt = abs(pedal)
                self.state.lt = 0.0
            elif pedal > 0.0:
                self.state.rt = 0.0
                self.state.lt = abs(pedal)
            else:
                self.state.rt = 0.0
                self.state.lt = 0.0
            self.state.gas_active = self.state.rt > 0.0
            self.state.brake_active = self.state.lt > 0.0
        else:
            if self.right_button_down and not self.left_button_down:
                self.state.rt = 1.0
                self.state.lt = 0.0
                self.state.gas_active = True
                self.state.brake_active = False
            elif self.left_button_down and not self.right_button_down:
                self.state.rt = 0.0
                self.state.lt = 1.0
                self.state.gas_active = False
                self.state.brake_active = True
            else:
                self.state.rt = 0.0
                self.state.lt = 0.0
                self.state.gas_active = False
                self.state.brake_active = False

        self.state.left_x = lx
        # RY no longer controls pedals; keep centered for compatibility.
        self.state.right_y = 0.0
        self.state.debug_text = (
            f"dx={dx:+d}px dy={dy:+d}px ax={self.axis_x:+.3f} ay={self.axis_y:+.3f} | "
            f"lx={self.state.left_x:+.3f} rt={self.state.rt:.3f} lt={self.state.lt:.3f}"
        )

    def push_to_gamepad(self) -> None:
        if self.pad is None:
            return

        lx = to_xinput_short(self.state.left_x)
        ry = to_xinput_short(0.0)
        rt = int(clamp(self.state.rt, 0.0, 1.0) * 255)
        lt = int(clamp(self.state.lt, 0.0, 1.0) * 255)
        now = time.time()
        gear_up_pressed = now < self.gear_up_until
        gear_down_pressed = now < self.gear_down_until

        self.pad.left_joystick(x_value=lx, y_value=0)
        self.pad.right_joystick(x_value=0, y_value=ry)
        self.pad.right_trigger(value=rt)
        self.pad.left_trigger(value=lt)
        self.pad.press_button(button=self.gear_up_btn) if gear_up_pressed else self.pad.release_button(button=self.gear_up_btn)
        self.pad.press_button(button=self.gear_down_btn) if gear_down_pressed else self.pad.release_button(button=self.gear_down_btn)
        self.pad.update()

    def worker_loop(self) -> None:
        kb_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        ms_listener = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll)
        kb_listener.start()
        ms_listener.start()

        try:
            self.set_reference_to_current_mouse()
            while not self.stop_event.is_set():
                if self.state.enabled:
                    with self.lock:
                        self.compute_state()
                    self.push_to_gamepad()
                time.sleep(POLL_INTERVAL)
        finally:
            try:
                kb_listener.stop()
                ms_listener.stop()
            except Exception:
                pass
            if self.cursor_hidden:
                set_cursor_visible(True)
                self.cursor_hidden = False
            self.reset_all()

    def run(self) -> None:
        indicator = Indicator(
            debug_mode=self.config.debug_mode,
            hud_fps=self.config.hud_fps,
            min_output_x=self.config.min_output_x,
            windows_scale=self.config.windows_scale,
            fullscreen_alpha=self.config.fullscreen_alpha,
        )
        indicator.root.protocol("WM_DELETE_WINDOW", self.stop_event.set)

        worker = threading.Thread(target=self.worker_loop, daemon=True)
        worker.start()

        try:
            indicator.loop(
                lambda: self.state,
                lambda: self.config.control_mode,
                lambda: self.hud_fullscreen_enabled,
                lambda: self.hud_fullscreen_rect,
                self._on_hud_fullscreen_state,
                self.stop_event,
            )
        finally:
            self.stop_event.set()
            worker.join(timeout=1.0)

    def _on_hud_fullscreen_state(self, active: bool, available: bool) -> None:
        self.hud_fullscreen_supported = bool(available)
        if self.hud_fullscreen_enabled and not active:
            self.hud_fullscreen_enabled = False
            self.hud_fullscreen_rect = None
            if not available:
                self.state.last_error = "透明全屏HUD初始化失败，已自动回到小窗模式"


if __name__ == "__main__":
    app = MouseToVirtualGamepad()
    app.run()





