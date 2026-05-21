import argparse
import json
import time
import threading
from pathlib import Path

import webview


class Api:
    def __init__(self, ipc_path: str, state: dict):
        self.ipc_path = ipc_path
        self.state = state
        self.window = None

    def set_window(self, window):
        self.window = window

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
        if self.window is None:
            return
        # Avoid destroying window directly inside sync API callback to reduce deadlock risk.
        threading.Timer(0.05, self.window.destroy).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipc", required=True)
    parser.add_argument("--state-file", required=True)
    args = parser.parse_args()
    with open(args.state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
    api = Api(args.ipc, state)
    ui_path = (Path(__file__).parent / "web_settings_ui" / "index.html").resolve()
    window = webview.create_window("设置", ui_path.as_uri(), js_api=api, width=760, height=420, min_size=(720, 420), resizable=True)
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    main()

