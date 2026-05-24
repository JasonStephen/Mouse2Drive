from pathlib import Path

from app.shared.paths import I18N_EN_PATH, I18N_ZH_PATH


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
