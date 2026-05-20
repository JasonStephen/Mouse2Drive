import configparser
import ctypes
import threading
import time
import tkinter as tk
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
    gas_mouse_button: str = "right"
    brake_mouse_button: str = "left"
    gear_up_button: str = "right_shoulder"
    gear_down_button: str = "left_shoulder"
    hide_cursor_on_enable: bool = True
    windows_scale: float = 1.0


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
        cfg.gas_mouse_button = parser.get(section, "gas_mouse_button", fallback=cfg.gas_mouse_button)
        cfg.brake_mouse_button = parser.get(section, "brake_mouse_button", fallback=cfg.brake_mouse_button)
        cfg.gear_up_button = parser.get(section, "gear_up_button", fallback=cfg.gear_up_button)
        cfg.gear_down_button = parser.get(section, "gear_down_button", fallback=cfg.gear_down_button)
        cfg.hide_cursor_on_enable = parser.getboolean(section, "hide_cursor_on_enable", fallback=cfg.hide_cursor_on_enable)
        cfg.windows_scale = parser.getfloat(section, "windows_scale", fallback=cfg.windows_scale)

    if cfg.control_mode < 1 or cfg.control_mode > 4:
        cfg.control_mode = 1
    cfg.reference_range_x_px = max(1.0, cfg.reference_range_x_px)
    cfg.reference_range_y_px = max(1.0, cfg.reference_range_y_px)
    cfg.min_output_x = clamp(cfg.min_output_x, 0.0, 0.95)
    cfg.hud_fps = int(clamp(cfg.hud_fps, 5, 240))
    cfg.gear_pulse_ms = int(clamp(cfg.gear_pulse_ms, 10, 300))
    cfg.windows_scale = clamp(cfg.windows_scale, 0.8, 2.0)
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
        "gas_mouse_button": cfg.gas_mouse_button,
        "brake_mouse_button": cfg.brake_mouse_button,
        "gear_up_button": cfg.gear_up_button,
        "gear_down_button": cfg.gear_down_button,
        "hide_cursor_on_enable": str(cfg.hide_cursor_on_enable).lower(),
        "windows_scale": f"{cfg.windows_scale:.2f}",
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
    ) -> None:
        self.debug_mode = debug_mode
        self.hud_fps = int(clamp(hud_fps, 5, 240))
        self.hud_interval_ms = max(1, int(1000 / self.hud_fps))
        self.min_output_x = clamp(min_output_x, 0.0, 0.95)
        # Keep text larger even at 100% scale to improve readability.
        self.ui_scale = max(1.15, windows_scale * 1.15)
        self.base_width = 390
        self.base_height_normal = 180
        self.base_height_debug = 205
        self.win_width = int(round(self.base_width * self.ui_scale))
        self.win_height = int(round((self.base_height_debug if self.debug_mode else self.base_height_normal) * self.ui_scale))
        self.canvas_width = max(360, int(round(360 * self.ui_scale)))
        self.canvas_height = max(98, int(round(98 * self.ui_scale)))
        self.pad_x = max(8, int(round(10 * self.ui_scale)))
        self.pad_y = max(3, int(round(4 * self.ui_scale)))
        self.locked = True
        self.drag_start_mouse_x = 0
        self.drag_start_mouse_y = 0
        self.drag_start_win_x = 0
        self.drag_start_win_y = 0
        self.root = tk.Tk()
        self.root.title("Mouse -> Virtual Gamepad")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        frame = tk.Frame(self.root, bg="#1f1f1f", bd=1, relief="solid")
        frame.pack(fill="both", expand=True)
        self.frame = frame

        self.header = tk.Frame(frame, bg="#1f1f1f")
        self.header.pack(fill="x")

        self.status_label = tk.Label(self.header, text="状态: OFF", fg="#ff6b6b", bg="#1f1f1f", font=("Segoe UI", self._font(10), "bold"), anchor="w", padx=self.pad_x, pady=self.pad_y)
        self.status_label.pack(side="left", fill="x", expand=True)

        self.lock_button = tk.Button(
            self.header,
            text="锁定",
            command=self.toggle_lock,
            bg="#2b2b2b",
            fg="#f0f0f0",
            activebackground="#3a3a3a",
            activeforeground="#ffffff",
            bd=0,
            padx=max(6, int(round(8 * self.ui_scale))),
            pady=max(1, int(round(2 * self.ui_scale))),
            font=("Segoe UI", self._font(8), "bold"),
        )
        self.lock_button.pack(side="right", padx=self.pad_x, pady=self.pad_y)

        self.mode_label = tk.Label(
            frame,
            text="模式: 1",
            fg="#b7d8ff",
            bg="#1f1f1f",
            font=("Segoe UI", self._font(9)),
            anchor="w",
            justify="left",
            wraplength=max(200, self.win_width - self.pad_x * 2),
            padx=self.pad_x,
            pady=max(1, int(round(2 * self.ui_scale))),
        )
        self.mode_label.pack(fill="x")

        self.canvas = tk.Canvas(frame, width=self.canvas_width, height=self.canvas_height, bg="#171717", highlightthickness=0)
        self.canvas.pack(fill="x", padx=self.pad_x, pady=self.pad_y)

        self.error_label = tk.Label(frame, text="", fg="#ffcc66", bg="#1f1f1f", font=("Segoe UI", self._font(8)), anchor="w", justify="left", wraplength=max(200, self.win_width - self.pad_x * 2), padx=self.pad_x, pady=max(1, int(round(2 * self.ui_scale))))
        self.error_label.pack(fill="x")
        self.debug_label = tk.Label(frame, text="", fg="#9fd6ff", bg="#1f1f1f", font=("Consolas", self._font(8)), anchor="w", justify="left", wraplength=max(200, self.win_width - self.pad_x * 2), padx=self.pad_x, pady=max(1, int(round(2 * self.ui_scale))))
        self.debug_label.pack(fill="x")

        self.root.update_idletasks()
        self.position_bottom_right()
        self._init_scene()
        self._bind_drag_for_widget(self.frame)
        self.root.bind("<Configure>", lambda _e: self.ensure_on_screen())

    def position_bottom_right(self) -> None:
        self.root.update_idletasks()
        w, h = self.win_width, self.win_height
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{sw - w - 18}+{sh - h - 58}")
        self.ensure_on_screen()

    def toggle_lock(self) -> None:
        self.locked = not self.locked
        self.lock_button.config(text="锁定" if self.locked else "解锁")

    def _bind_drag_for_widget(self, widget: tk.Widget) -> None:
        widget.bind("<ButtonPress-1>", self._on_drag_start, add="+")
        widget.bind("<B1-Motion>", self._on_drag_move, add="+")
        for child in widget.winfo_children():
            self._bind_drag_for_widget(child)

    def _on_drag_start(self, event) -> None:
        if self.locked:
            return
        self.drag_start_mouse_x = event.x_root
        self.drag_start_mouse_y = event.y_root
        self.drag_start_win_x = self.root.winfo_x()
        self.drag_start_win_y = self.root.winfo_y()

    def _on_drag_move(self, event) -> None:
        if self.locked:
            return
        dx = event.x_root - self.drag_start_mouse_x
        dy = event.y_root - self.drag_start_mouse_y
        new_x = self.drag_start_win_x + dx
        new_y = self.drag_start_win_y + dy
        self.root.geometry(f"+{new_x}+{new_y}")
        self.ensure_on_screen()

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

    def _init_scene(self) -> None:
        c = self.canvas
        s = self.ui_scale
        x = lambda v: int(round(v * s))
        y = lambda v: int(round(v * s))

        lx_text_x = x(24)
        lx_text_y = y(17)
        lx_x0, lx_y0, lx_x1, lx_y1 = x(40), y(10), x(340), y(24)
        lx_center_x = x(190)
        lx_fill_y0, lx_fill_y1 = y(11), y(23)
        brake_label_x, brake_label_y = x(34), y(68)
        brake_x0, brake_y0, brake_x1, brake_y1 = x(60), y(60), x(150), y(74)
        brake_box_x0, brake_box_x1 = x(154), x(166)
        gas_label_x, gas_label_y = x(222), y(68)
        gas_x0, gas_y0, gas_x1, gas_y1 = x(248), y(60), x(338), y(74)
        gas_box_x0, gas_box_x1 = x(342), x(354)

        # LX horizontal slider
        c.create_text(lx_text_x, lx_text_y, text="L", fill="#cfd8dc", font=("Segoe UI", self._font(9), "bold"))
        self.lx_track = c.create_rectangle(lx_x0, lx_y0, lx_x1, lx_y1, outline="#4a4a4a", fill="#262626")
        self.lx_center = c.create_line(lx_center_x, y(8), lx_center_x, y(26), fill="#9e9e9e", width=max(1, int(round(2 * s))))
        self.lx_fill = c.create_rectangle(lx_center_x, lx_fill_y0, lx_center_x, lx_fill_y1, outline="", fill="#67b7ff")

        # LT/RT value sliders + active indicators
        c.create_text(brake_label_x, brake_label_y, text="刹车", fill="#ffcdd2", font=("Segoe UI", self._font(9)))
        self.brake_track = c.create_rectangle(brake_x0, brake_y0, brake_x1, brake_y1, outline="#8a8a8a", fill="#2a2a2a")
        self.brake_fill = c.create_rectangle(brake_x0 + 1, brake_y0 + 1, brake_x0 + 1, brake_y1 - 1, outline="", fill="#ff6b6b")
        self.brake_box = c.create_rectangle(brake_box_x0, brake_y0, brake_box_x1, brake_y1, outline="#8a8a8a", fill="#2a2a2a")

        c.create_text(gas_label_x, gas_label_y, text="油门", fill="#c8e6c9", font=("Segoe UI", self._font(9)))
        self.gas_track = c.create_rectangle(gas_x0, gas_y0, gas_x1, gas_y1, outline="#8a8a8a", fill="#2a2a2a")
        self.gas_fill = c.create_rectangle(gas_x0 + 1, gas_y0 + 1, gas_x0 + 1, gas_y1 - 1, outline="", fill="#37d45c")
        self.gas_box = c.create_rectangle(gas_box_x0, gas_y0, gas_box_x1, gas_y1, outline="#8a8a8a", fill="#2a2a2a")

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
        x0, y0, x1, y1 = self.canvas.coords(self.lx_track)
        cx = (x0 + x1) / 2.0
        half = (x1 - x0) / 2.0
        left = cx + (half * min(0.0, view))
        right = cx + (half * max(0.0, view))
        self.canvas.coords(self.lx_fill, left, y0 + 1, right, y1 - 1)

    def _draw_pedals(self, gas: bool, brake: bool, rt: float, lt: float) -> None:
        lt = clamp(lt, 0.0, 1.0)
        rt = clamp(rt, 0.0, 1.0)

        brake_x0, brake_y0, brake_x1, brake_y1 = self.canvas.coords(self.brake_track)
        gas_x0, gas_y0, gas_x1, gas_y1 = self.canvas.coords(self.gas_track)

        brake_fill_x1 = brake_x0 + (brake_x1 - brake_x0) * lt
        gas_fill_x1 = gas_x0 + (gas_x1 - gas_x0) * rt

        self.canvas.coords(self.brake_fill, brake_x0 + 1, brake_y0 + 1, brake_fill_x1 - 1 if brake_fill_x1 > brake_x0 + 2 else brake_x0 + 1, brake_y1 - 1)
        self.canvas.coords(self.gas_fill, gas_x0 + 1, gas_y0 + 1, gas_fill_x1 - 1 if gas_fill_x1 > gas_x0 + 2 else gas_x0 + 1, gas_y1 - 1)

        self.canvas.itemconfig(self.gas_box, fill="#37d45c" if gas else "#2a2a2a")
        self.canvas.itemconfig(self.brake_box, fill="#ff6b6b" if brake else "#2a2a2a")

    def update(self, state: MapperState, mode: int) -> None:
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
        self.root.update_idletasks()
        needed_h = self.frame.winfo_reqheight()
        cur_w = self.root.winfo_width()
        cur_h = self.root.winfo_height()
        target_h = max(self.win_height, needed_h)
        if target_h != cur_h:
            self.root.geometry(f"{cur_w}x{target_h}+{self.root.winfo_x()}+{self.root.winfo_y()}")
            self.ensure_on_screen()

    def loop(self, state_getter, mode_getter, stop_event: threading.Event) -> None:
        def tick() -> None:
            if stop_event.is_set():
                self.root.destroy()
                return
            self.update(state_getter(), mode_getter())
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
        self.reference_pos: tuple[int, int] | None = None
        self.current_pos: tuple[int, int] | None = None

        self.right_button_down = False
        self.left_button_down = False
        self.gear_up_until = 0.0
        self.gear_down_until = 0.0

        self.mouse_controller = mouse.Controller()
        self.toggle_combo = parse_hotkey_combo(self.config.toggle_hotkey)
        self.switch_mode_combo = parse_hotkey_combo(self.config.switch_mode_hotkey)
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
        try:
            user32 = ctypes.windll.user32
            vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            return (int(vx + vw // 2), int(vy + vh // 2))
        except Exception:
            x, y = self.mouse_controller.position
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

        if self.switch_mode_combo and token in self.switch_mode_combo and self.switch_mode_combo.issubset(self.pressed_keys):
            self.config.control_mode += 1
            if self.config.control_mode > 4:
                self.config.control_mode = 1
            self.state.last_error = f"已切换到模式{self.config.control_mode}"
            return

        if self.toggle_combo and token in self.toggle_combo and self.toggle_combo.issubset(self.pressed_keys):
            self._set_mapper_enabled(not self.state.enabled)

    def on_key_release(self, key) -> None:
        token = normalize_key_token(key)
        if token is not None:
            self.pressed_keys.discard(token)

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
        )
        indicator.root.protocol("WM_DELETE_WINDOW", self.stop_event.set)

        worker = threading.Thread(target=self.worker_loop, daemon=True)
        worker.start()

        try:
            indicator.loop(lambda: self.state, lambda: self.config.control_mode, self.stop_event)
        finally:
            self.stop_event.set()
            worker.join(timeout=1.0)


if __name__ == "__main__":
    app = MouseToVirtualGamepad()
    app.run()


