import argparse
import json
import time
import threading
from pathlib import Path

import webview
from gamepad_mouse_mapper import load_settings_defaults, load_settings_options


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
        if close_after:
            self._close_deferred()
        return True

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
    bootstrap_text = (
        "window.__BOOTSTRAP_STATE__ = " + json.dumps(state, ensure_ascii=False) + ";\n"
        "window.__SETTINGS_DEFAULTS__ = " + json.dumps(defaults, ensure_ascii=False) + ";\n"
        "window.__SETTINGS_OPTIONS__ = " + json.dumps(options, ensure_ascii=False) + ";\n"
    )
    bootstrap_path.write_text(bootstrap_text, encoding="utf-8")
    window = webview.create_window("设置", ui_path.as_uri(), js_api=api, width=760, height=420, min_size=(720, 420), resizable=True)
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    main()

