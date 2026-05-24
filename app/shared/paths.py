import sys
from pathlib import Path


APP_BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]

CONFIG_DIR = APP_BASE_DIR / "config"
LOCALE_DIR = APP_BASE_DIR / "locale"
WEB_SETTINGS_UI_DIR = APP_BASE_DIR / "web_settings_ui"
WEB_SETTINGS_UI_INTERNAL_DIR = APP_BASE_DIR / "_internal" / "web_settings_ui"

CONFIG_PATH = CONFIG_DIR / "config.cfg"
SETTINGS_DEFAULTS_PATH = CONFIG_DIR / "settings_defaults.cfg"
SETTINGS_OPTIONS_PATH = CONFIG_DIR / "settings_options.cfg"
I18N_ZH_PATH = LOCALE_DIR / "i18n_zh-CN.cfg"
I18N_EN_PATH = LOCALE_DIR / "i18n_en-US.cfg"
