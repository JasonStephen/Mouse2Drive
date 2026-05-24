import configparser

from app.shared.paths import SETTINGS_DEFAULTS_PATH, SETTINGS_OPTIONS_PATH


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
