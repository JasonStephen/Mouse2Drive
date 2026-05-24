import argparse
import configparser
import json
import sys
import threading
import time
from pathlib import Path

import webview

APP_BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
I18N_ZH_PATH = APP_BASE_DIR / "i18n_zh-CN.cfg"
I18N_EN_PATH = APP_BASE_DIR / "i18n_en-US.cfg"
SETTINGS_DEFAULTS_PATH = APP_BASE_DIR / "settings_defaults.cfg"
SETTINGS_OPTIONS_PATH = APP_BASE_DIR / "settings_options.cfg"


def _resolve_existing_path(candidates: list[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def _parse_i18n_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            key = k.strip()
            if key:
                result[key] = v.strip()
    except Exception:
        pass
    return result


def load_i18n(language: str) -> dict[str, str]:
    lang = str(language or "zh-CN").strip()
    base = _parse_i18n_file(I18N_EN_PATH)
    zh = _parse_i18n_file(I18N_ZH_PATH)
    if lang == "zh-CN":
        merged = dict(base)
        merged.update(zh)
        return merged
    return base


def _split_pipe_list(text: str) -> list[str]:
    return [x.strip() for x in str(text).split("|") if x.strip()]


def _to_bool(v: str, fallback: bool) -> bool:
    t = str(v).strip().lower()
    if t in {"1", "true", "yes", "on"}:
        return True
    if t in {"0", "false", "no", "off"}:
        return False
    return fallback


def load_settings_options() -> dict:
    parser = configparser.ConfigParser()
    defaults = {
        "hud_fps": [15, 30, 60, 90, 120],
        "boolean_switch": ["true", "false"],
        "mouse_buttons": ["right", "left", "middle", "x1", "x2", "wheel_up", "wheel_down", "none"],
        "gamepad_bindings": [
            "a", "b", "x", "y", "start", "back", "guide",
            "left_shoulder", "right_shoulder",
            "left_thumb", "right_thumb",
            "dpad_up", "dpad_down", "dpad_left", "dpad_right",
            "left_trigger", "right_trigger",
            "left_x", "left_y", "right_x", "right_y",
            "none",
        ],
        "mapping_modes": ["gamepad", "keyboard", "none"],
        "control_modes": ["1", "2", "3", "4"],
        "steering_axes": ["left_x", "left_y", "right_x", "right_y", "left_trigger", "right_trigger", "none"],
    }
    try:
        if SETTINGS_OPTIONS_PATH.exists():
            parser.read(SETTINGS_OPTIONS_PATH, encoding="utf-8-sig")
            sec = "options"
            if parser.has_section(sec):
                raw_hud = _split_pipe_list(parser.get(sec, "hud_fps", fallback=""))
                if raw_hud:
                    defaults["hud_fps"] = [int(x) for x in raw_hud if x.isdigit()]
                for key in ("boolean_switch", "mouse_buttons", "gamepad_bindings", "mapping_modes", "control_modes", "steering_axes"):
                    raw = _split_pipe_list(parser.get(sec, key, fallback=""))
                    if raw:
                        defaults[key] = raw
    except Exception:
        pass
    return defaults


def load_settings_defaults() -> dict:
    parser = configparser.ConfigParser()
    result = {
        "hud_fps": 60,
        "language": "zh-CN",
        "fullscreen_mode": False,
        "window_scale": 1.0,
        "fullscreen_scale": 1.0,
        "fullscreen_alpha": 0.5,
        "reference_range_x_ratio": 0.6250,
        "reference_range_y_ratio": 0.5185,
        "min_output_x": 0.235,
        "gear_pulse_ms": 45,
        "hide_cursor_on_enable": True,
        "control_mode": 1,
        "mode_direction_enable": True,
        "mode_linear_pedal_enable": True,
        "mode_key_pedal_enable": False,
        "mode_gear_enable": True,
        "steering_axis": "left_x",
        "toggle_hotkey": "shift+v",
        "toggle_fullscreen_hotkey": "alt+f",
        "gas_mouse_button": "right",
        "brake_mouse_button": "left",
        "gear_up_mouse_button": "wheel_up",
        "gear_down_mouse_button": "wheel_down",
        "gas_output_button": "right_trigger",
        "brake_output_button": "left_trigger",
        "gas_brake_mapping_mode": "gamepad",
        "gas_key": "w",
        "brake_key": "s",
        "gear_mapping_mode": "gamepad",
        "gear_up_button": "right_thumb",
        "gear_down_button": "left_thumb",
        "gear_up_key": "e",
        "gear_down_key": "q",
        "debug_mode": False,
    }
    try:
        if SETTINGS_DEFAULTS_PATH.exists():
            parser.read(SETTINGS_DEFAULTS_PATH, encoding="utf-8-sig")
            sec = "defaults"
            if parser.has_section(sec):
                for k in (
                    "language", "toggle_hotkey", "toggle_fullscreen_hotkey", "steering_axis",
                    "gas_mouse_button", "brake_mouse_button", "gear_up_mouse_button", "gear_down_mouse_button",
                    "gas_output_button", "brake_output_button", "gas_brake_mapping_mode", "gas_key", "brake_key",
                    "gear_mapping_mode", "gear_up_button", "gear_down_button", "gear_up_key", "gear_down_key",
                ):
                    result[k] = parser.get(sec, k, fallback=str(result[k]))
                for k in ("hud_fps", "gear_pulse_ms", "control_mode"):
                    result[k] = parser.getint(sec, k, fallback=int(result[k]))
                for k in ("mode_direction_enable", "mode_linear_pedal_enable", "mode_key_pedal_enable", "mode_gear_enable"):
                    result[k] = _to_bool(parser.get(sec, k, fallback=str(result[k])), bool(result[k]))
                for k in ("window_scale", "fullscreen_scale", "fullscreen_alpha", "min_output_x", "reference_range_x_ratio", "reference_range_y_ratio"):
                    result[k] = parser.getfloat(sec, k, fallback=float(result[k]))
                result["fullscreen_mode"] = _to_bool(parser.get(sec, "fullscreen_mode", fallback=str(result["fullscreen_mode"])), bool(result["fullscreen_mode"]))
                result["hide_cursor_on_enable"] = _to_bool(parser.get(sec, "hide_cursor_on_enable", fallback=str(result["hide_cursor_on_enable"])), bool(result["hide_cursor_on_enable"]))
                result["debug_mode"] = _to_bool(parser.get(sec, "debug_mode", fallback=str(result["debug_mode"])), bool(result["debug_mode"]))
    except Exception:
        pass
    return result


class Api:
    def __init__(self, ipc_path: str, state: dict):
        self.ipc_path = ipc_path
        self.state = state
        self._window = None

    def set_window(self, window):
        self._window = window

    def get_initial(self):
        return self.state

    def apply(self, values, close_after=False):
        payload = {"ts": time.time(), "values": values, "close": bool(close_after)}
        with open(self.ipc_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        self.state = values
        lang = str(values.get("language", "zh-CN"))
        i18n = load_i18n(lang)
        if self._window is not None:
            try:
                self._window.title = i18n.get("settings.title", "Settings")
            except Exception:
                pass
        if close_after:
            self._close_deferred()
        return True

    def get_i18n(self, language=None):
        lang = str(language or self.state.get("language", "zh-CN"))
        return load_i18n(lang)

    def close_window(self):
        self._close_deferred()
        return True

    def _close_deferred(self):
        if self._window is None:
            return
        threading.Timer(0.05, self._window.destroy).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipc", required=True)
    parser.add_argument("--state-file", required=True)
    args = parser.parse_args()
    with open(args.state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
    api = Api(args.ipc, state)
    ui_dir = _resolve_existing_path([
        (APP_BASE_DIR / "web_settings_ui").resolve(),
        (APP_BASE_DIR / "_internal" / "web_settings_ui").resolve(),
    ])
    ui_path = _resolve_existing_path([
        (ui_dir / "index.html").resolve(),
        (APP_BASE_DIR / "web_settings_ui" / "index.html").resolve(),
        (APP_BASE_DIR / "_internal" / "web_settings_ui" / "index.html").resolve(),
    ])
    bootstrap_path = ui_dir / "bootstrap_state.js"
    defaults = load_settings_defaults()
    options = load_settings_options()
    language = str(state.get("language", defaults.get("language", "zh-CN")))
    i18n = load_i18n(language)
    bootstrap_text = (
        "window.__BOOTSTRAP_STATE__ = " + json.dumps(state, ensure_ascii=False) + ";\n"
        "window.__SETTINGS_DEFAULTS__ = " + json.dumps(defaults, ensure_ascii=False) + ";\n"
        "window.__SETTINGS_OPTIONS__ = " + json.dumps(options, ensure_ascii=False) + ";\n"
        "window.__I18N__ = " + json.dumps(i18n, ensure_ascii=False) + ";\n"
    )
    bootstrap_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_path.write_text(bootstrap_text, encoding="utf-8")
    window_title = i18n.get("settings.title", "Settings")
    window = webview.create_window(window_title, ui_path.as_uri(), js_api=api, width=980, height=460, min_size=(900, 420), resizable=True)
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    main()
