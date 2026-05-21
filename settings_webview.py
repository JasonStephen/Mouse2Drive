import argparse
import json
import time
import threading
from pathlib import Path

import webview
from gamepad_mouse_mapper import load_i18n, load_settings_defaults, load_settings_options


class Api:
    def __init__(self, ipc_path: str, state: dict):
        self.ipc_path = ipc_path
        self.state = state
        # Do not expose native window object as a public js_api attribute,
        # otherwise pywebview may recurse deeply while introspecting js_api.
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
        # Avoid destroying window directly inside sync API callback to reduce deadlock risk.
        threading.Timer(0.05, self._window.destroy).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipc", required=True)
    parser.add_argument("--state-file", required=True)
    args = parser.parse_args()
    with open(args.state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
    api = Api(args.ipc, state)
    ui_dir = (Path(__file__).parent / "web_settings_ui").resolve()
    ui_path = (ui_dir / "index.html").resolve()
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
    bootstrap_path.write_text(bootstrap_text, encoding="utf-8")
    window_title = i18n.get("settings.title", "Settings")
    window = webview.create_window(window_title, ui_path.as_uri(), js_api=api, width=980, height=460, min_size=(900, 420), resizable=True)
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    main()

