import argparse
import json
import threading
import time
from pathlib import Path

import webview
from app.shared.i18n import load_i18n
from app.shared.paths import WEB_SETTINGS_UI_DIR, WEB_SETTINGS_UI_INTERNAL_DIR
from app.shared.settings_files import load_settings_defaults, load_settings_options


def _resolve_existing_path(candidates: list[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


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
        WEB_SETTINGS_UI_DIR.resolve(),
        WEB_SETTINGS_UI_INTERNAL_DIR.resolve(),
    ])
    ui_path = _resolve_existing_path([
        (ui_dir / "index.html").resolve(),
        (WEB_SETTINGS_UI_DIR / "index.html").resolve(),
        (WEB_SETTINGS_UI_INTERNAL_DIR / "index.html").resolve(),
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
