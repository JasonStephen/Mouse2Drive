import configparser
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

import vgamepad as vg
from pynput import keyboard, mouse


CONFIG_PATH = Path(__file__).with_name("config.cfg")
RESET_HOTKEY = keyboard.Key.f10
POLL_INTERVAL = 0.01


@dataclass
class AppConfig:
    control_mode: int = 1
    reference_range_x_px: float = 360.0
    reference_range_y_px: float = 260.0
    min_output_x: float = 0.23
    debug_mode: bool = False


@dataclass
class MapperState:
    enabled: bool = False
    left_x: float = 0.0
    right_y: float = 0.0
    gas_active: bool = False
    brake_active: bool = False
    debug_text: str = ""
    last_error: str = ""


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def to_xinput_short(v: float) -> int:
    v = clamp(v, -1.0, 1.0)
    return int(v * 32767) if v >= 0 else int(v * 32768)


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

    if cfg.control_mode < 1 or cfg.control_mode > 4:
        cfg.control_mode = 1
    cfg.reference_range_x_px = max(1.0, cfg.reference_range_x_px)
    cfg.reference_range_y_px = max(1.0, cfg.reference_range_y_px)
    cfg.min_output_x = clamp(cfg.min_output_x, 0.0, 0.95)
    return cfg


def save_default_config(cfg: AppConfig) -> None:
    parser = configparser.ConfigParser()
    parser["mapping"] = {
        "control_mode": str(cfg.control_mode),
        "reference_range_x_px": str(cfg.reference_range_x_px),
        "reference_range_y_px": str(cfg.reference_range_y_px),
        "min_output_x": str(cfg.min_output_x),
        "debug_mode": str(cfg.debug_mode).lower(),
    }
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        parser.write(f)


class Indicator:
    def __init__(self, debug_mode: bool = False) -> None:
        self.debug_mode = debug_mode
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

        self.status_label = tk.Label(self.header, text="状态: OFF", fg="#ff6b6b", bg="#1f1f1f", font=("Segoe UI", 10, "bold"), anchor="w", padx=10, pady=4)
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
            padx=8,
            pady=2,
            font=("Segoe UI", 8, "bold"),
        )
        self.lock_button.pack(side="right", padx=8, pady=4)

        self.mode_label = tk.Label(frame, text="模式: 1", fg="#b7d8ff", bg="#1f1f1f", font=("Segoe UI", 9), anchor="w", padx=10, pady=2)
        self.mode_label.pack(fill="x")

        self.canvas = tk.Canvas(frame, width=360, height=140, bg="#171717", highlightthickness=0)
        self.canvas.pack(fill="x", padx=10, pady=6)

        self.error_label = tk.Label(frame, text="", fg="#ffcc66", bg="#1f1f1f", font=("Segoe UI", 8), anchor="w", padx=10, pady=2)
        self.error_label.pack(fill="x")
        self.debug_label = tk.Label(frame, text="", fg="#9fd6ff", bg="#1f1f1f", font=("Consolas", 8), anchor="w", padx=10, pady=2)
        self.debug_label.pack(fill="x")

        self.root.update_idletasks()
        self.position_bottom_right()
        self._init_scene()
        self._bind_drag_for_widget(self.frame)
        self.root.bind("<Configure>", lambda _e: self.ensure_on_screen())

    def position_bottom_right(self) -> None:
        self.root.update_idletasks()
        w, h = 390, (255 if self.debug_mode else 230)
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
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = self.root.winfo_x()
        y = self.root.winfo_y()

        max_x = max(0, sw - win_w)
        max_y = max(0, sh - win_h)
        nx = int(clamp(x, 0, max_x))
        ny = int(clamp(y, 0, max_y))
        if nx != x or ny != y:
            self.root.geometry(f"+{nx}+{ny}")

    def _init_scene(self) -> None:
        c = self.canvas
        # LX horizontal slider
        c.create_text(24, 20, text="L", fill="#cfd8dc", font=("Segoe UI", 9, "bold"))
        self.lx_track = c.create_rectangle(40, 12, 340, 28, outline="#4a4a4a", fill="#262626")
        self.lx_center = c.create_line(190, 10, 190, 30, fill="#9e9e9e", width=2)
        self.lx_fill = c.create_rectangle(190, 13, 190, 27, outline="", fill="#67b7ff")

        # RY vertical slider
        c.create_text(24, 72, text="R", fill="#cfd8dc", font=("Segoe UI", 9, "bold"))
        self.ry_track = c.create_rectangle(170, 40, 210, 120, outline="#4a4a4a", fill="#262626")
        self.ry_center = c.create_line(168, 80, 212, 80, fill="#9e9e9e", width=2)
        self.ry_fill = c.create_rectangle(173, 80, 207, 80, outline="", fill="#81f29a")

        # Gas / Brake indicators (mode2 focus)
        c.create_text(58, 130, text="刹车", fill="#ffcdd2", font=("Segoe UI", 9))
        self.brake_box = c.create_rectangle(80, 122, 150, 136, outline="#8a8a8a", fill="#2a2a2a")
        c.create_text(248, 130, text="油门", fill="#c8e6c9", font=("Segoe UI", 9))
        self.gas_box = c.create_rectangle(270, 122, 340, 136, outline="#8a8a8a", fill="#2a2a2a")

    def _draw_lx(self, lx: float) -> None:
        cx = 190
        left = cx + int(150 * min(0.0, lx))
        right = cx + int(150 * max(0.0, lx))
        self.canvas.coords(self.lx_fill, left, 13, right, 27)

    def _draw_ry(self, ry: float) -> None:
        cy = 80
        top = cy + int(38 * min(0.0, ry))
        bottom = cy + int(38 * max(0.0, ry))
        self.canvas.coords(self.ry_fill, 173, top, 207, bottom)

    def _draw_pedals(self, gas: bool, brake: bool) -> None:
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
        self.mode_label.config(text=f"模式{mode}: {mode_names.get(mode, '未知')}  (Shift+V开关 / Alt+Shift+V切模式 / F10重置参考点)")
        self._draw_lx(state.left_x)
        self._draw_ry(state.right_y)
        self._draw_pedals(state.gas_active, state.brake_active)
        self.error_label.config(text=state.last_error)
        if self.debug_mode:
            self.debug_label.config(text=state.debug_text)
        else:
            self.debug_label.config(text="")

    def loop(self, state_getter, mode_getter, stop_event: threading.Event) -> None:
        def tick() -> None:
            if stop_event.is_set():
                self.root.destroy()
                return
            self.update(state_getter(), mode_getter())
            self.root.after(40, tick)

        tick()
        self.root.mainloop()


class MouseToVirtualGamepad:
    def __init__(self) -> None:
        self.config = load_config()
        self.state = MapperState()
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        self.pressed_keys: set = set()
        self.reference_pos: tuple[int, int] | None = None
        self.current_pos: tuple[int, int] | None = None

        self.right_button_down = False
        self.left_button_down = False

        self.mouse_controller = mouse.Controller()

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

    def reset_all(self) -> None:
        self.set_reference_to_current_mouse()
        self.right_button_down = False
        self.left_button_down = False
        self.state.gas_active = False
        self.state.brake_active = False
        self.push_to_gamepad()

    def on_key_press(self, key) -> None:
        self.pressed_keys.add(key)

        if key == RESET_HOTKEY:
            self.reset_all()
            self.state.last_error = "已复位"
            return

        shift_pressed = (
            keyboard.Key.shift in self.pressed_keys
            or keyboard.Key.shift_l in self.pressed_keys
            or keyboard.Key.shift_r in self.pressed_keys
        )
        alt_pressed = (
            keyboard.Key.alt in self.pressed_keys
            or keyboard.Key.alt_l in self.pressed_keys
            or keyboard.Key.alt_r in self.pressed_keys
            or keyboard.Key.alt_gr in self.pressed_keys
        )
        is_v_key = (key == keyboard.KeyCode.from_char('v') or key == keyboard.KeyCode.from_char('V'))

        # Alt+Shift+V: switch control mode (1 -> 2 -> 3 -> 4 -> 1)
        if shift_pressed and alt_pressed and is_v_key:
            self.config.control_mode += 1
            if self.config.control_mode > 4:
                self.config.control_mode = 1
            self.state.last_error = f"已切换到模式{self.config.control_mode}"
            return

        # Shift+V: enable/disable mapper
        if shift_pressed and is_v_key:
            self.state.enabled = not self.state.enabled
            if self.state.enabled:
                self.set_reference_to_current_mouse()
                self.state.last_error = "已开启"
            else:
                self.reset_all()
                self.state.last_error = "已关闭并回中"

    def on_key_release(self, key) -> None:
        self.pressed_keys.discard(key)

    def on_mouse_move(self, x: int, y: int) -> None:
        with self.lock:
            self.current_pos = (x, y)

    def on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        if button == mouse.Button.right:
            self.right_button_down = pressed
        elif button == mouse.Button.left:
            self.left_button_down = pressed

    def compute_state(self) -> None:
        if self.reference_pos is None or self.current_pos is None:
            return

        dx = self.current_pos[0] - self.reference_pos[0]
        dy = self.current_pos[1] - self.reference_pos[1]

        # Steering:
        # mode1/mode2: steering enabled by mouse X
        # mode3/mode4: pedal-only, no steering
        if self.config.control_mode in (1, 2):
            base_lx = clamp(dx / self.config.reference_range_x_px, -1.0, 1.0)
            abs_base_lx = abs(base_lx)
            if abs_base_lx > 0.0:
                abs_lx = self.config.min_output_x + (1.0 - self.config.min_output_x) * abs_base_lx
                lx = (1.0 if base_lx >= 0 else -1.0) * clamp(abs_lx, 0.0, 1.0)
            else:
                lx = 0.0
        else:
            lx = 0.0

        # Pedals:
        # mode1/mode3: linear pedal by mouse Y
        # mode2/mode4: digital pedal by mouse buttons
        if self.config.control_mode in (1, 3):
            ry = clamp(dy / self.config.reference_range_y_px, -1.0, 1.0)
            self.state.gas_active = ry < 0.0
            self.state.brake_active = ry > 0.0
        else:
            if self.right_button_down and not self.left_button_down:
                ry = -1.0
                self.state.gas_active = True
                self.state.brake_active = False
            elif self.left_button_down and not self.right_button_down:
                ry = 1.0
                self.state.gas_active = False
                self.state.brake_active = True
            else:
                ry = 0.0
                self.state.gas_active = False
                self.state.brake_active = False

        self.state.left_x = lx
        self.state.right_y = ry
        self.state.debug_text = f"dx={dx:+d}px dy={dy:+d}px | lx={self.state.left_x:+.3f} ry={self.state.right_y:+.3f}"

    def push_to_gamepad(self) -> None:
        if self.pad is None:
            return

        lx = to_xinput_short(self.state.left_x)
        ry = to_xinput_short(-self.state.right_y)

        self.pad.left_joystick(x_value=lx, y_value=0)
        self.pad.right_joystick(x_value=0, y_value=ry)
        self.pad.update()

    def worker_loop(self) -> None:
        kb_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        ms_listener = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click)
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
            self.reset_all()

    def run(self) -> None:
        indicator = Indicator(debug_mode=self.config.debug_mode)
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
