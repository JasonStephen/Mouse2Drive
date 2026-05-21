let I18N = (typeof window.__I18N__ === "object" && window.__I18N__) ? window.__I18N__ : {};
const OPTIONS = (typeof window.__SETTINGS_OPTIONS__ === "object" && window.__SETTINGS_OPTIONS__) ? window.__SETTINGS_OPTIONS__ : {};
const FALLBACK_DEFAULTS = {
  language: "zh-CN",
  hud_fps: 60,
  fullscreen_mode: false,
  window_scale: 1.0,
  fullscreen_scale: 1.0,
  fullscreen_alpha: 0.5,
  reference_range_x_ratio: 0.63,
  reference_range_y_ratio: 0.52,
  min_output_x: 0.235,
  gear_pulse_ms: 45,
  hide_cursor_on_enable: true,
  control_mode: 1,
  mode_direction_enable: true,
  mode_linear_pedal_enable: true,
  mode_key_pedal_enable: false,
  steering_axis: "left_x",
  toggle_hotkey: "shift+v",
  switch_mode_hotkey: "alt+shift+v",
  toggle_fullscreen_hotkey: "alt+f",
  open_settings_hotkey: "ctrl+shift+o",
  gas_mouse_button: "right",
  brake_mouse_button: "left",
  gear_up_mouse_button: "wheel_up",
  gear_down_mouse_button: "wheel_down",
  gas_output_button: "right_trigger",
  brake_output_button: "left_trigger",
  gas_brake_mapping_mode: "gamepad",
  gas_key: "w",
  brake_key: "s",
  gear_mapping_mode: "gamepad",
  gear_up_button: "none",
  gear_down_button: "none",
  gear_up_key: "e",
  gear_down_key: "q",
};
const DEFAULTS = (typeof window.__SETTINGS_DEFAULTS__ === "object" && window.__SETTINGS_DEFAULTS__) ? window.__SETTINGS_DEFAULTS__ : FALLBACK_DEFAULTS;

function t(key, fallback = "") { return I18N[key] ?? fallback; }
document.title = t("settings.title", "Settings");

const detailEl = document.getElementById("detail");
const tabs = {
  language: document.getElementById("tab-language"),
  mode: document.getElementById("tab-mode"),
  display: document.getElementById("tab-display"),
  sense: document.getElementById("tab-sense"),
  bind: document.getElementById("tab-bind"),
};
const pages = {
  language: document.getElementById("page-language"),
  mode: document.getElementById("page-mode"),
  display: document.getElementById("page-display"),
  sense: document.getElementById("page-sense"),
  bind: document.getElementById("page-bind"),
};
const inputs = {
  language: document.getElementById("language"),
  mode_direction_enable: document.getElementById("mode_direction_enable"),
  mode_linear_pedal_enable: document.getElementById("mode_linear_pedal_enable"),
  mode_key_pedal_enable: document.getElementById("mode_key_pedal_enable"),
  fullscreen_mode: document.getElementById("fullscreen_mode"),
  window_scale: document.getElementById("window_scale"),
  fullscreen_scale: document.getElementById("fullscreen_scale"),
  fullscreen_alpha: document.getElementById("fullscreen_alpha"),
  hud_fps: document.getElementById("hud_fps"),
  reference_range_x_ratio: document.getElementById("reference_range_x_ratio"),
  reference_range_y_ratio: document.getElementById("reference_range_y_ratio"),
  min_output_x: document.getElementById("min_output_x"),
  gear_pulse_ms: document.getElementById("gear_pulse_ms"),
  hide_cursor_on_enable: document.getElementById("hide_cursor_on_enable"),
  steering_axis: document.getElementById("steering_axis"),
  toggle_hotkey: document.getElementById("toggle_hotkey"),
  switch_mode_hotkey: document.getElementById("switch_mode_hotkey"),
  toggle_fullscreen_hotkey: document.getElementById("toggle_fullscreen_hotkey"),
  open_settings_hotkey: document.getElementById("open_settings_hotkey"),
  gas_mouse_button: document.getElementById("gas_mouse_button"),
  brake_mouse_button: document.getElementById("brake_mouse_button"),
  gear_up_mouse_button: document.getElementById("gear_up_mouse_button"),
  gear_down_mouse_button: document.getElementById("gear_down_mouse_button"),
  gas_output_button: document.getElementById("gas_output_button"),
  brake_output_button: document.getElementById("brake_output_button"),
  gas_brake_mapping_mode: document.getElementById("gas_brake_mapping_mode"),
  gas_key: document.getElementById("gas_key"),
  brake_key: document.getElementById("brake_key"),
  gear_mapping_mode: document.getElementById("gear_mapping_mode"),
  gear_up_button: document.getElementById("gear_up_button"),
  gear_down_button: document.getElementById("gear_down_button"),
  gear_up_key: document.getElementById("gear_up_key"),
  gear_down_key: document.getElementById("gear_down_key"),
};

let detailMap = {};
function rebuildDetailMap() {
  detailMap = {
    language: t("settings.detail.language", ""),
    mode: t("settings.detail.control_mode", ""),
    display: t("settings.detail.display", ""),
    sense: t("settings.detail.sense", ""),
    bind: t("settings.detail.bind", ""),
  };
  [
    "mode_direction_enable","mode_linear_pedal_enable","mode_key_pedal_enable","fullscreen_mode","window_scale",
    "fullscreen_scale","fullscreen_alpha","hud_fps","reference_range_x_ratio","reference_range_y_ratio","min_output_x",
    "gear_pulse_ms","hide_cursor_on_enable","steering_axis","toggle_hotkey","switch_mode_hotkey","toggle_fullscreen_hotkey",
    "open_settings_hotkey","gas_mouse_button","brake_mouse_button","gear_up_mouse_button","gear_down_mouse_button",
    "gas_output_button","brake_output_button","gas_brake_mapping_mode","gas_key","brake_key","gear_mapping_mode",
    "gear_up_button","gear_down_button","gear_up_key","gear_down_key"
  ].forEach((k) => { detailMap[k] = t(`settings.detail.${k}`, ""); });
}

let initialValues = null;
let dragState = null;
let hotkeyCaptureTarget = null;
let hotkeyPressed = new Set();
let hotkeyLastCombo = "";

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function applyTextI18n() {
  const textMap = {
    "txt-settings-type-title": t("settings.title.type", "Settings Type"),
    "txt-detail-title": t("settings.title.detail", "Detail"),
    "tab-language": t("settings.page.language", "Language"),
    "tab-mode": t("settings.page.mode", "Control Mode"),
    "tab-display": t("settings.page.display", "Display"),
    "tab-sense": t("settings.page.sense", "Sensitivity"),
    "tab-bind": t("settings.page.bind", "Hotkey & Mapping"),
    "subttl-function-hotkeys": t("settings.section.function_hotkeys", "Function hotkeys"),
    "subttl-mouse-hotkeys": t("settings.section.mouse_hotkeys", "Mouse hotkeys"),
    "subttl-mapping": t("settings.section.mapping", "Mapping"),
    "subttl-pedal-mapping": t("settings.section.pedal_mapping", "Pedal mapping"),
    "subttl-gear-control": t("settings.section.gear_control", "Gear shift control"),
    "lbl-language": t("settings.label.language", "Language"),
    "lbl-mode_direction_enable": t("settings.label.mode_direction_enable", "Steering control"),
    "lbl-mode_linear_pedal_enable": t("settings.label.mode_linear_pedal_enable", "Linear pedal"),
    "lbl-mode_key_pedal_enable": t("settings.label.mode_key_pedal_enable", "Key pedal"),
    "lbl-fullscreen_mode": t("settings.label.fullscreen_mode", "Fullscreen mode"),
    "lbl-window_scale": t("settings.label.window_scale", "Window scale (0.8 - 1.5)"),
    "lbl-fullscreen_scale": t("settings.label.fullscreen_scale", "Fullscreen scale (0.8 - 1.5)"),
    "lbl-fullscreen_alpha": t("settings.label.fullscreen_alpha", "Fullscreen opacity (0 - 1.00)"),
    "lbl-hud_fps": t("settings.label.hud_fps", "HUD FPS"),
    "lbl-reference_range_x_ratio": t("settings.label.reference_range_x_ratio", "Steering sensitivity X ratio (0 - 1)"),
    "lbl-reference_range_y_ratio": t("settings.label.reference_range_y_ratio", "Pedal sensitivity Y ratio (0 - 1)"),
    "lbl-min_output_x": t("settings.label.min_output_x", "Non-zero steering start output (0 - 1)"),
    "lbl-gear_pulse_ms": t("settings.label.gear_pulse_ms", "Shift pulse (ms)"),
    "lbl-hide_cursor_on_enable": t("settings.label.hide_cursor_on_enable", "Hide cursor (experimental)"),
    "lbl-steering_axis": t("settings.label.steering_axis", "Steering mapped axis"),
    "lbl-toggle_hotkey": t("settings.label.toggle_hotkey", "Toggle hotkey"),
    "lbl-switch_mode_hotkey": t("settings.label.switch_mode_hotkey", "Switch mode hotkey"),
    "lbl-toggle_fullscreen_hotkey": t("settings.label.toggle_fullscreen_hotkey", "Fullscreen hotkey"),
    "lbl-open_settings_hotkey": t("settings.label.open_settings_hotkey", "Open settings hotkey"),
    "lbl-gas_mouse_button": t("settings.label.gas_mouse_button", "Throttle control"),
    "lbl-brake_mouse_button": t("settings.label.brake_mouse_button", "Brake control"),
    "lbl-gear_up_mouse_button": t("settings.label.gear_up_mouse_button", "Gear up"),
    "lbl-gear_down_mouse_button": t("settings.label.gear_down_mouse_button", "Gear down"),
    "lbl-gas_brake_mapping_mode": t("settings.label.gas_brake_mapping_mode", "Pedal mapping mode"),
    "lbl-gas_output_button": t("settings.label.gas_output_button", "Throttle mapping"),
    "lbl-brake_output_button": t("settings.label.brake_output_button", "Brake mapping"),
    "lbl-gas_key": t("settings.label.gas_key", "Throttle"),
    "lbl-brake_key": t("settings.label.brake_key", "Brake"),
    "lbl-gear_mapping_mode": t("settings.label.gear_mapping_mode", "Gear shift mapping mode"),
    "lbl-gear_up_button": t("settings.label.gear_up_button", "Gear up"),
    "lbl-gear_down_button": t("settings.label.gear_down_button", "Gear down"),
    "lbl-gear_up_key": t("settings.label.gear_up_key", "Gear up"),
    "lbl-gear_down_key": t("settings.label.gear_down_key", "Gear down"),
    "btn-reset-all": t("settings.button.reset_all", "全部重置"),
    "btn-apply": t("settings.button.apply", "应用"),
    "btn-confirm": t("settings.button.confirm", "确认并应用"),
    "btn-close": t("settings.button.close", "关闭"),
  };
  Object.entries(textMap).forEach(([id, text]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  });

  const zhOpt = inputs.language?.querySelector('option[value="zh-CN"]');
  const enOpt = inputs.language?.querySelector('option[value="en-US"]');
  if (zhOpt) zhOpt.textContent = t("settings.option.language.zh-CN", "简体中文");
  if (enOpt) enOpt.textContent = t("settings.option.language.en-US", "English");

  if (inputs.hide_cursor_on_enable) {
    const onOpt = inputs.hide_cursor_on_enable.querySelector('option[value="true"]');
    const offOpt = inputs.hide_cursor_on_enable.querySelector('option[value="false"]');
    if (onOpt) onOpt.textContent = t("settings.option.boolean.true", "On");
    if (offOpt) offOpt.textContent = t("settings.option.boolean.false", "Off");
  }

  const titleReset = t("settings.icon.reset", "重置");
  const titleClear = t("settings.icon.clear", "取消绑定");
  document.querySelectorAll(".icon-btn").forEach((el) => {
    if (el.classList.contains("danger")) el.title = titleClear;
    else el.title = titleReset;
  });
}

function fillSelect(selectEl, values) {
  if (!selectEl) return;
  const prev = selectEl.value;
  selectEl.innerHTML = values.map((v) => `<option value="${v}">${v}</option>`).join("");
  if (values.includes(prev)) selectEl.value = prev;
}

function fillSelectWithLabels(selectEl, pairs) {
  if (!selectEl) return;
  const prev = selectEl.value;
  selectEl.innerHTML = pairs.map((p) => `<option value="${p.value}">${p.label}</option>`).join("");
  if (pairs.some((p) => p.value === prev)) selectEl.value = prev;
}

function applyOptionsFromConfig() {
  fillSelect(inputs.hud_fps, (OPTIONS.hud_fps || [15, 30, 60, 90, 120]).map(String));
  fillSelect(inputs.hide_cursor_on_enable, OPTIONS.boolean_switch || ["true", "false"]);
  const mouseButtons = OPTIONS.mouse_buttons || ["right", "left", "middle", "x1", "x2", "wheel_up", "wheel_down", "none"];
  fillSelect(inputs.gas_mouse_button, mouseButtons);
  fillSelect(inputs.brake_mouse_button, mouseButtons);
  fillSelect(inputs.gear_up_mouse_button, mouseButtons);
  fillSelect(inputs.gear_down_mouse_button, mouseButtons);

  fillSelect(inputs.steering_axis, OPTIONS.steering_axes || ["left_x", "left_y", "right_x", "right_y", "left_trigger", "right_trigger", "none"]);
  const modeValues = OPTIONS.mapping_modes || ["gamepad", "keyboard"];
  fillSelectWithLabels(inputs.gas_brake_mapping_mode, modeValues.map((v) => ({ value: v, label: v === "gamepad" ? t("settings.option.map.gamepad", "手柄映射") : t("settings.option.map.keyboard", "键盘映射") })));
  fillSelectWithLabels(inputs.gear_mapping_mode, modeValues.map((v) => ({ value: v, label: v === "gamepad" ? t("settings.option.map.gamepad", "手柄映射") : t("settings.option.map.keyboard", "键盘映射") })));

  const pad = OPTIONS.gamepad_bindings || [];
  fillSelect(inputs.gas_output_button, pad);
  fillSelect(inputs.brake_output_button, pad);
  fillSelect(inputs.gear_up_button, pad);
  fillSelect(inputs.gear_down_button, pad);
}

function showPage(kind) {
  Object.keys(tabs).forEach((k) => tabs[k].classList.toggle("active", k === kind));
  Object.keys(pages).forEach((k) => pages[k].classList.toggle("hidden", k !== kind));
  detailEl.textContent = detailMap[kind] || "";
}

function getCurrentPageKind() {
  if (tabs.language.classList.contains("active")) return "language";
  if (tabs.mode.classList.contains("active")) return "mode";
  if (tabs.display.classList.contains("active")) return "display";
  if (tabs.sense.classList.contains("active")) return "sense";
  return "bind";
}

function applyGearModeVisibility() {
  const mode = inputs.gear_mapping_mode.value;
  document.getElementById("gear-gamepad-group").classList.toggle("hidden", mode !== "gamepad");
  document.getElementById("gear-keyboard-group").classList.toggle("hidden", mode !== "keyboard");
}

function applyPedalModeVisibility() {
  const mode = inputs.gas_brake_mapping_mode.value;
  document.getElementById("pedal-gamepad-group").classList.toggle("hidden", mode !== "gamepad");
  document.getElementById("pedal-keyboard-group").classList.toggle("hidden", mode !== "keyboard");
}

function controlModeToFlags(mode) {
  const m = parseInt(mode || "1", 10);
  if (m === 2) return { direction: true, linear: false, key: true };
  if (m === 3) return { direction: false, linear: true, key: false };
  if (m === 4) return { direction: false, linear: false, key: true };
  return { direction: true, linear: true, key: false };
}

function flagsToControlMode(direction, linear, key) {
  const d = !!direction;
  const l = !!linear;
  const k = !!key;
  if (d && l) return 1;
  if (d && k) return 2;
  if (!d && l) return 3;
  if (!d && k) return 4;
  return 1;
}

function parseValues() {
  return {
    language: (inputs.language.value || "zh-CN").trim(),
    hud_fps: parseInt(inputs.hud_fps.value || String(DEFAULTS.hud_fps), 10),
    fullscreen_mode: !!inputs.fullscreen_mode.checked,
    mode_direction_enable: !!inputs.mode_direction_enable.checked,
    mode_linear_pedal_enable: !!inputs.mode_linear_pedal_enable.checked,
    mode_key_pedal_enable: !!inputs.mode_key_pedal_enable.checked,
    window_scale: clamp(parseFloat(inputs.window_scale.value || String(DEFAULTS.window_scale)), 0.8, 1.5),
    fullscreen_scale: clamp(parseFloat(inputs.fullscreen_scale.value || String(DEFAULTS.fullscreen_scale)), 0.8, 1.5),
    fullscreen_alpha: clamp(parseFloat(inputs.fullscreen_alpha.value || String(DEFAULTS.fullscreen_alpha)), 0, 1),
    reference_range_x_ratio: clamp(parseFloat(inputs.reference_range_x_ratio.value || String(DEFAULTS.reference_range_x_ratio)), 0, 1),
    reference_range_y_ratio: clamp(parseFloat(inputs.reference_range_y_ratio.value || String(DEFAULTS.reference_range_y_ratio)), 0, 1),
    min_output_x: clamp(parseFloat(inputs.min_output_x.value || String(DEFAULTS.min_output_x)), 0, 1),
    gear_pulse_ms: Math.round(clamp(parseFloat(inputs.gear_pulse_ms.value || String(DEFAULTS.gear_pulse_ms)), 10, 300)),
    hide_cursor_on_enable: inputs.hide_cursor_on_enable.value === "true",
    control_mode: flagsToControlMode(inputs.mode_direction_enable.checked, inputs.mode_linear_pedal_enable.checked, inputs.mode_key_pedal_enable.checked),
    steering_axis: (inputs.steering_axis.value || String(DEFAULTS.steering_axis)).trim(),
    toggle_hotkey: (inputs.toggle_hotkey.value || "").trim(),
    switch_mode_hotkey: (inputs.switch_mode_hotkey.value || "").trim(),
    toggle_fullscreen_hotkey: (inputs.toggle_fullscreen_hotkey.value || "").trim(),
    open_settings_hotkey: (inputs.open_settings_hotkey.value || "").trim(),
    gas_mouse_button: (inputs.gas_mouse_button.value || String(DEFAULTS.gas_mouse_button)).trim(),
    brake_mouse_button: (inputs.brake_mouse_button.value || String(DEFAULTS.brake_mouse_button)).trim(),
    gear_up_mouse_button: (inputs.gear_up_mouse_button.value || String(DEFAULTS.gear_up_mouse_button)).trim(),
    gear_down_mouse_button: (inputs.gear_down_mouse_button.value || String(DEFAULTS.gear_down_mouse_button)).trim(),
    gas_output_button: (inputs.gas_output_button.value || String(DEFAULTS.gas_output_button)).trim(),
    brake_output_button: (inputs.brake_output_button.value || String(DEFAULTS.brake_output_button)).trim(),
    gas_brake_mapping_mode: (inputs.gas_brake_mapping_mode.value || String(DEFAULTS.gas_brake_mapping_mode)).trim(),
    gas_key: (inputs.gas_key.value || String(DEFAULTS.gas_key)).trim(),
    brake_key: (inputs.brake_key.value || String(DEFAULTS.brake_key)).trim(),
    gear_mapping_mode: (inputs.gear_mapping_mode.value || String(DEFAULTS.gear_mapping_mode)).trim(),
    gear_up_button: (inputs.gear_up_button.value || String(DEFAULTS.gear_up_button)).trim(),
    gear_down_button: (inputs.gear_down_button.value || String(DEFAULTS.gear_down_button)).trim(),
    gear_up_key: (inputs.gear_up_key.value || String(DEFAULTS.gear_up_key)).trim(),
    gear_down_key: (inputs.gear_down_key.value || String(DEFAULTS.gear_down_key)).trim(),
  };
}

function setValues(v) {
  inputs.language.value = String(v.language ?? DEFAULTS.language ?? "zh-CN");
  inputs.hud_fps.value = String(v.hud_fps ?? DEFAULTS.hud_fps);
  inputs.fullscreen_mode.checked = !!(v.fullscreen_mode ?? DEFAULTS.fullscreen_mode);
  inputs.window_scale.value = Number(v.window_scale ?? DEFAULTS.window_scale).toFixed(2);
  inputs.fullscreen_scale.value = Number(v.fullscreen_scale ?? DEFAULTS.fullscreen_scale).toFixed(2);
  inputs.fullscreen_alpha.value = Number(v.fullscreen_alpha ?? DEFAULTS.fullscreen_alpha).toFixed(2);
  inputs.reference_range_x_ratio.value = Number(v.reference_range_x_ratio ?? DEFAULTS.reference_range_x_ratio).toFixed(2);
  inputs.reference_range_y_ratio.value = Number(v.reference_range_y_ratio ?? DEFAULTS.reference_range_y_ratio).toFixed(2);
  inputs.min_output_x.value = Number(v.min_output_x ?? DEFAULTS.min_output_x).toFixed(3);
  inputs.gear_pulse_ms.value = String(v.gear_pulse_ms ?? DEFAULTS.gear_pulse_ms);
  inputs.hide_cursor_on_enable.value = v.hide_cursor_on_enable ? "true" : "false";
  const flags = controlModeToFlags(v.control_mode ?? DEFAULTS.control_mode);
  inputs.mode_direction_enable.checked = !!(v.mode_direction_enable ?? flags.direction);
  inputs.mode_linear_pedal_enable.checked = !!(v.mode_linear_pedal_enable ?? flags.linear);
  inputs.mode_key_pedal_enable.checked = !!(v.mode_key_pedal_enable ?? flags.key);

  ["steering_axis","toggle_hotkey","switch_mode_hotkey","toggle_fullscreen_hotkey","open_settings_hotkey","gas_mouse_button","brake_mouse_button","gear_up_mouse_button","gear_down_mouse_button","gas_output_button","brake_output_button","gas_brake_mapping_mode","gas_key","brake_key","gear_mapping_mode","gear_up_button","gear_down_button","gear_up_key","gear_down_key"].forEach((k) => {
    if (inputs[k]) inputs[k].value = String(v[k] ?? DEFAULTS[k]);
  });
  applyGearModeVisibility();
  applyPedalModeVisibility();
}

function hasChanges() {
  if (!initialValues) return false;
  const now = parseValues();
  return Object.keys(now).some((k) => JSON.stringify(now[k]) !== JSON.stringify(initialValues[k]));
}

function getEffectiveHotkeyFields() {
  const fields = ["toggle_hotkey", "switch_mode_hotkey", "toggle_fullscreen_hotkey", "open_settings_hotkey"];
  if (inputs.gas_brake_mapping_mode.value === "keyboard") fields.push("gas_key", "brake_key");
  if (inputs.gear_mapping_mode.value === "keyboard") fields.push("gear_up_key", "gear_down_key");
  return fields;
}

function normalizeHotkeyValue(v) { return String(v || "").trim().toLowerCase(); }

function validateHotkeyConflicts(showAlert = false) {
  document.querySelectorAll(".hotkey").forEach((el) => el.classList.remove("conflict"));
  const map = new Map();
  for (const f of getEffectiveHotkeyFields()) {
    const el = inputs[f];
    if (!el) continue;
    const val = normalizeHotkeyValue(el.value);
    if (!val || val === "none") continue;
    if (!map.has(val)) map.set(val, []);
    map.get(val).push(el);
  }
  let hasConflict = false;
  for (const list of map.values()) {
    if (list.length > 1) {
      hasConflict = true;
      list.forEach((el) => el.classList.add("conflict"));
    }
  }
  if (hasConflict && showAlert) alert(t("settings.alert.conflict", "Duplicate hotkeys detected."));
  return !hasConflict;
}

async function apply(closeAfter) {
  if (!validateHotkeyConflicts(true)) return;
  const langBefore = String((initialValues && initialValues.language) ? initialValues.language : (inputs.language.value || "zh-CN"));
  const v = parseValues();
  setValues(v);
  await Promise.race([
    window.pywebview.api.apply(v, closeAfter),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1500)),
  ]);
  if (!closeAfter && String(v.language || "zh-CN") !== langBefore) {
    try {
      const newI18n = await Promise.race([
        window.pywebview.api.get_i18n(v.language),
        new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1200)),
      ]);
      if (newI18n && typeof newI18n === "object") {
        I18N = newI18n;
        document.title = t("settings.title", "Settings");
        const snapshot = parseValues();
        rebuildDetailMap();
        applyTextI18n();
        applyOptionsFromConfig();
        setValues(snapshot);
        showPage(getCurrentPageKind());
      }
    } catch (_) {
      // no-op
    }
  }
  initialValues = parseValues();
}

async function closePanel() {
  if (hasChanges() && confirm(t("settings.confirm.save_changes", "Unsaved changes detected. Save and apply?"))) {
    try {
      await apply(true);
    } catch (e) {
      alert(t("settings.alert.apply_failed", "Failed to apply settings. Please retry."));
    }
    return;
  }
  try {
    await Promise.race([
      window.pywebview.api.close_window(),
      new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1200)),
    ]);
  } catch (e) {
    alert(t("settings.alert.close_failed", "Failed to close settings window. Please retry."));
  }
}

function bindHoverDetail(el, key) {
  if (!el) return;
  el.addEventListener("mouseenter", () => { detailEl.textContent = detailMap[key] || ""; });
  el.addEventListener("mouseleave", () => {
    if (tabs.language.classList.contains("active")) detailEl.textContent = detailMap.language;
    else if (tabs.mode.classList.contains("active")) detailEl.textContent = detailMap.mode;
    else if (tabs.display.classList.contains("active")) detailEl.textContent = detailMap.display;
    else if (tabs.sense.classList.contains("active")) detailEl.textContent = detailMap.sense;
    else detailEl.textContent = detailMap.bind;
  });
}

function bindDragAdjust(el, inputKey, lo, hi, step) {
  if (!el) return;
  el.addEventListener("mousedown", (e) => {
    dragState = { x: e.clientX, key: inputKey, start: clamp(parseFloat(inputs[inputKey].value || "0"), lo, hi), lo, hi, step };
  });
}

function tokenFromEvent(e) {
  const k = (e.key || "").toLowerCase();
  if (k === "shift") return "shift";
  if (k === "control" || k === "ctrl") return "ctrl";
  if (k === "alt") return "alt";
  if (/^[a-z0-9]$/.test(k)) return k;
  if (k === " ") return "space";
  if (k === "arrowup") return "up";
  if (k === "arrowdown") return "down";
  if (k === "arrowleft") return "left";
  if (k === "arrowright") return "right";
  if (k === "pageup") return "page_up";
  if (k === "pagedown") return "page_down";
  return null;
}

function formatCombo(tokens) {
  const order = ["ctrl", "alt", "shift"];
  const mods = order.filter((x) => tokens.has(x));
  const rest = [...tokens].filter((x) => !order.includes(x)).sort();
  return [...mods, ...rest].join("+");
}

function bindHotkeyCapture(inputEl) {
  if (!inputEl) return;
  inputEl.addEventListener("focus", () => {
    hotkeyCaptureTarget = inputEl;
    hotkeyPressed = new Set();
    hotkeyLastCombo = inputEl.value || "";
    inputEl.classList.add("capturing");
  });
  inputEl.addEventListener("blur", () => {
    inputEl.classList.remove("capturing");
    if (hotkeyCaptureTarget === inputEl) {
      hotkeyCaptureTarget = null;
      hotkeyPressed = new Set();
    }
  });
}

document.addEventListener("keydown", (e) => {
  if (!hotkeyCaptureTarget) return;
  const tk = tokenFromEvent(e);
  if (!tk) return;
  e.preventDefault();
  hotkeyPressed.add(tk);
  const combo = formatCombo(hotkeyPressed);
  if (combo) {
    hotkeyCaptureTarget.value = combo;
    hotkeyLastCombo = combo;
  }
});

document.addEventListener("keyup", (e) => {
  if (!hotkeyCaptureTarget) return;
  const tk = tokenFromEvent(e);
  if (!tk) return;
  e.preventDefault();
  const isModifier = tk === "ctrl" || tk === "alt" || tk === "shift";
  if (!isModifier && hotkeyLastCombo) {
    hotkeyCaptureTarget.value = hotkeyLastCombo;
    hotkeyCaptureTarget.blur();
    return;
  }
  hotkeyPressed.delete(tk);
});

document.addEventListener("mousemove", (e) => {
  if (!dragState) return;
  const dx = e.clientX - dragState.x;
  const raw = clamp(dragState.start + dx * dragState.step, dragState.lo, dragState.hi);
  if (dragState.key === "min_output_x") inputs[dragState.key].value = raw.toFixed(3);
  else if (dragState.key === "reference_range_x_ratio" || dragState.key === "reference_range_y_ratio") inputs[dragState.key].value = raw.toFixed(2);
  else if (dragState.key === "gear_pulse_ms") inputs[dragState.key].value = String(Math.round(raw));
  else inputs[dragState.key].value = raw.toFixed(2);
});
document.addEventListener("mouseup", () => { dragState = null; });

function setField(field, value) {
  if (!inputs[field]) return;
  inputs[field].value = value;
  if (field === "gear_mapping_mode") applyGearModeVisibility();
  if (field === "gas_brake_mapping_mode") applyPedalModeVisibility();
}

function wireIconActions() {
  const singleReset = {
    "btn-reset-fullscreen-alpha": "fullscreen_alpha",
    "btn-reset-ref-x-ratio": "reference_range_x_ratio",
    "btn-reset-ref-y-ratio": "reference_range_y_ratio",
    "btn-reset-min-output": "min_output_x",
    "btn-reset-gear-pulse": "gear_pulse_ms",
    "btn-reset-hide-cursor": "hide_cursor_on_enable",
  };
  Object.entries(singleReset).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", () => setField(key, String(DEFAULTS[key])));
  });

  ["toggle_hotkey","switch_mode_hotkey","toggle_fullscreen_hotkey","open_settings_hotkey","steering_axis","gas_mouse_button","brake_mouse_button","gear_up_mouse_button","gear_down_mouse_button","gas_output_button","brake_output_button","gas_brake_mapping_mode","gas_key","brake_key","gear_mapping_mode","gear_up_button","gear_down_button","gear_up_key","gear_down_key"].forEach((k) => {
    const r = document.getElementById(`reset-${k}`);
    if (r) r.addEventListener("click", () => setField(k, String(DEFAULTS[k])));
    const c = document.getElementById(`clear-${k}`);
    if (c) c.addEventListener("click", () => setField(k, "none"));
  });
}

Object.keys(inputs).forEach((key) => bindHoverDetail(inputs[key], key === "language" ? "language" : key));
[
  "mode_direction_enable","mode_linear_pedal_enable","mode_key_pedal_enable","fullscreen_mode","window_scale","fullscreen_scale",
  "fullscreen_alpha","hud_fps","reference_range_x_ratio","reference_range_y_ratio","min_output_x","gear_pulse_ms",
  "hide_cursor_on_enable","steering_axis","toggle_hotkey","switch_mode_hotkey","toggle_fullscreen_hotkey","open_settings_hotkey",
  "gas_mouse_button","brake_mouse_button","gear_up_mouse_button","gear_down_mouse_button","gas_output_button","brake_output_button",
  "gas_brake_mapping_mode","gas_key","brake_key","gear_mapping_mode","gear_up_button","gear_down_button","gear_up_key","gear_down_key"
].forEach((k) => bindHoverDetail(document.getElementById(`lbl-${k}`), k));

bindDragAdjust(document.getElementById("lbl-window_scale"), "window_scale", 0.8, 1.5, 0.01);
bindDragAdjust(inputs.window_scale, "window_scale", 0.8, 1.5, 0.01);
bindDragAdjust(document.getElementById("lbl-fullscreen_scale"), "fullscreen_scale", 0.8, 1.5, 0.01);
bindDragAdjust(inputs.fullscreen_scale, "fullscreen_scale", 0.8, 1.5, 0.01);
bindDragAdjust(document.getElementById("lbl-fullscreen_alpha"), "fullscreen_alpha", 0, 1, 0.01);
bindDragAdjust(inputs.fullscreen_alpha, "fullscreen_alpha", 0, 1, 0.01);
bindDragAdjust(document.getElementById("lbl-reference_range_x_ratio"), "reference_range_x_ratio", 0, 1, 0.01);
bindDragAdjust(inputs.reference_range_x_ratio, "reference_range_x_ratio", 0, 1, 0.01);
bindDragAdjust(document.getElementById("lbl-reference_range_y_ratio"), "reference_range_y_ratio", 0, 1, 0.01);
bindDragAdjust(inputs.reference_range_y_ratio, "reference_range_y_ratio", 0, 1, 0.01);
bindDragAdjust(document.getElementById("lbl-min_output_x"), "min_output_x", 0, 1, 0.01);
bindDragAdjust(inputs.min_output_x, "min_output_x", 0, 1, 0.01);
bindDragAdjust(document.getElementById("lbl-gear_pulse_ms"), "gear_pulse_ms", 10, 300, 1);
bindDragAdjust(inputs.gear_pulse_ms, "gear_pulse_ms", 10, 300, 1);

[inputs.toggle_hotkey, inputs.switch_mode_hotkey, inputs.toggle_fullscreen_hotkey, inputs.open_settings_hotkey, inputs.gas_key, inputs.brake_key, inputs.gear_up_key, inputs.gear_down_key].forEach(bindHotkeyCapture);
[inputs.toggle_hotkey, inputs.switch_mode_hotkey, inputs.toggle_fullscreen_hotkey, inputs.open_settings_hotkey, inputs.gas_key, inputs.brake_key, inputs.gear_up_key, inputs.gear_down_key].forEach((el) => {
  if (!el) return;
  el.addEventListener("input", () => validateHotkeyConflicts(false));
  el.addEventListener("blur", () => validateHotkeyConflicts(false));
});

Object.entries(tabs).forEach(([k, el]) => el.addEventListener("click", () => showPage(k)));
inputs.gear_mapping_mode.addEventListener("change", () => { applyGearModeVisibility(); validateHotkeyConflicts(false); });
inputs.gas_brake_mapping_mode.addEventListener("change", () => { applyPedalModeVisibility(); validateHotkeyConflicts(false); });

document.getElementById("btn-apply").addEventListener("click", async () => {
  try { await apply(false); }
  catch { alert(t("settings.alert.apply_failed", "Failed to apply settings. Please retry.")); }
});
document.getElementById("btn-confirm").addEventListener("click", async () => {
  try { await apply(true); }
  catch { alert(t("settings.alert.confirm_apply_failed", "Failed to confirm and apply. Please retry.")); }
});
document.getElementById("btn-close").addEventListener("click", () => closePanel());
document.getElementById("btn-reset-all").addEventListener("click", () => {
  if (!confirm(t("settings.confirm.reset_all", "Confirm reset all settings?"))) return;
  setValues(DEFAULTS);
});

wireIconActions();

function tryReadBootstrapStateFromWindow() {
  try {
    if (typeof window.__BOOTSTRAP_STATE__ === "object" && window.__BOOTSTRAP_STATE__ !== null) return window.__BOOTSTRAP_STATE__;
  } catch {}
  return null;
}

let __initStarted = false;
async function initSettingsUI() {
  if (__initStarted) return;
  __initStarted = true;
  rebuildDetailMap();
  applyTextI18n();
  applyOptionsFromConfig();

  let init = tryReadBootstrapStateFromWindow();
  if (!init) {
    try {
      init = await Promise.race([
        window.pywebview.api.get_initial(),
        new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1200)),
      ]);
    } catch {
      init = { ...DEFAULTS };
      alert(t("settings.alert.init_timeout", "Settings init timeout. Defaults loaded."));
    }
  }

  setValues(init);
  initialValues = parseValues();
  validateHotkeyConflicts(false);
  showPage("language");
}

window.addEventListener("pywebviewready", () => initSettingsUI());
document.addEventListener("DOMContentLoaded", () => setTimeout(() => initSettingsUI(), 50));
