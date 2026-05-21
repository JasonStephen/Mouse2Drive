const detailEl = document.getElementById("detail");
const tabs = {
  mode: document.getElementById("tab-mode"),
  display: document.getElementById("tab-display"),
  sense: document.getElementById("tab-sense"),
  bind: document.getElementById("tab-bind"),
};
const pages = {
  mode: document.getElementById("page-mode"),
  display: document.getElementById("page-display"),
  sense: document.getElementById("page-sense"),
  bind: document.getElementById("page-bind"),
};

const inputs = {
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

const detailMap = {
  mode: "控制模式设置提示。",
  display: "图像显示设置提示。",
  sense: "灵敏度设置提示。",
  bind: "快捷键与映射设置提示。",
  mode_direction_enable: "是否启用方向控制。",
  mode_linear_pedal_enable: "是否启用线性油刹（鼠标位移控制油刹）。",
  mode_key_pedal_enable: "是否启用按键油刹（按键/映射触发油刹）。",
  fullscreen_mode: "切换 HUD 全屏或窗口模式。",
  window_scale: "小窗显示缩放比例。",
  fullscreen_scale: "全屏显示缩放比例。",
  fullscreen_alpha: "全屏下三滑块与锁定/设置按钮的透明度。",
  hud_fps: "HUD 刷新帧率档位。",
  reference_range_x_ratio: "转向灵敏度X比例。公式：1 - reference_range_x_px / (屏幕宽度/2)。",
  reference_range_y_ratio: "油刹灵敏度Y比例。公式：1 - reference_range_y_px / (屏幕高度/2)。",
  min_output_x: "非零方向起始输出，值越大起步越敏感。",
  gear_pulse_ms: "换挡脉冲持续时长（毫秒）。",
  hide_cursor_on_enable: "实验功能：开启映射时尝试隐藏光标。",
  steering_axis: "转向映射到哪个摇杆轴。",
  toggle_hotkey: "点击输入框后按组合键完成映射。",
  switch_mode_hotkey: "点击输入框后按组合键完成映射。",
  toggle_fullscreen_hotkey: "点击输入框后按组合键完成映射。",
  open_settings_hotkey: "点击输入框后按组合键完成映射。",
  gas_mouse_button: "油门触发按键。",
  brake_mouse_button: "刹车触发按键。",
  gear_up_mouse_button: "鼠标触发升档。",
  gear_down_mouse_button: "鼠标触发降档。",
  gas_output_button: "油门映射到手柄按键。",
  brake_output_button: "刹车映射到手柄按键。",
  gas_brake_mapping_mode: "油刹输出到手柄或键盘。",
  gas_key: "油门键盘按键映射。",
  brake_key: "刹车键盘按键映射。",
  gear_mapping_mode: "升降档输出到手柄或键盘。",
  gear_up_button: "升档对应的手柄按键。",
  gear_down_button: "降档对应的手柄按键。",
  gear_up_key: "升档键盘按键映射。",
  gear_down_key: "降档键盘按键映射。",
};

const FALLBACK_DEFAULTS = {
  hud_fps: 60,
  fullscreen_mode: false,
  window_scale: 1.0,
  fullscreen_scale: 1.0,
  fullscreen_alpha: 0.5,
  reference_range_x_ratio: 0.625,
  reference_range_y_ratio: 0.5185,
  min_output_x: 0.235,
  gear_pulse_ms: 45,
  hide_cursor_on_enable: true,
  control_mode: 1,
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
  gear_up_button: "right_thumb",
  gear_down_button: "left_thumb",
  gear_up_key: "e",
  gear_down_key: "q",
};
const DEFAULTS = (typeof window.__SETTINGS_DEFAULTS__ === "object" && window.__SETTINGS_DEFAULTS__) ? window.__SETTINGS_DEFAULTS__ : FALLBACK_DEFAULTS;
const OPTIONS = (typeof window.__SETTINGS_OPTIONS__ === "object" && window.__SETTINGS_OPTIONS__) ? window.__SETTINGS_OPTIONS__ : {};

let initialValues = null;
let dragState = null;
let hotkeyCaptureTarget = null;
let hotkeyPressed = new Set();
let hotkeyLastCombo = "";

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function applyGearModeVisibility() {
  const mode = inputs.gear_mapping_mode.value;
  const isKeyboard = mode === "keyboard";
  const isGamepad = mode === "gamepad";
  document.getElementById("gear-gamepad-group").classList.toggle("hidden", !isGamepad);
  document.getElementById("gear-keyboard-group").classList.toggle("hidden", !isKeyboard);
}

function applyPedalModeVisibility() {
  const mode = inputs.gas_brake_mapping_mode.value;
  const isKeyboard = mode === "keyboard";
  const isGamepad = mode === "gamepad";
  document.getElementById("pedal-gamepad-group").classList.toggle("hidden", !isGamepad);
  document.getElementById("pedal-keyboard-group").classList.toggle("hidden", !isKeyboard);
}

function showPage(kind) {
  tabs.mode.classList.toggle("active", kind === "mode");
  tabs.display.classList.toggle("active", kind === "display");
  tabs.sense.classList.toggle("active", kind === "sense");
  tabs.bind.classList.toggle("active", kind === "bind");
  pages.mode.classList.toggle("hidden", kind !== "mode");
  pages.display.classList.toggle("hidden", kind !== "display");
  pages.sense.classList.toggle("hidden", kind !== "sense");
  pages.bind.classList.toggle("hidden", kind !== "bind");
  detailEl.textContent = detailMap[kind] || "";
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
  fillSelect(inputs.hud_fps, (OPTIONS.hud_fps || [15, 30, 60, 90, 120]).map((x) => String(x)));
  fillSelect(inputs.hide_cursor_on_enable, OPTIONS.boolean_switch || ["true", "false"]);
  fillSelect(inputs.gas_mouse_button, OPTIONS.mouse_buttons || ["right", "left", "middle", "x1", "x2", "wheel_up", "wheel_down", "none"]);
  fillSelect(inputs.brake_mouse_button, OPTIONS.mouse_buttons || ["right", "left", "middle", "x1", "x2", "wheel_up", "wheel_down", "none"]);
  fillSelect(inputs.gear_up_mouse_button, OPTIONS.mouse_buttons || ["right", "left", "middle", "x1", "x2", "wheel_up", "wheel_down", "none"]);
  fillSelect(inputs.gear_down_mouse_button, OPTIONS.mouse_buttons || ["right", "left", "middle", "x1", "x2", "wheel_up", "wheel_down", "none"]);
  fillSelect(inputs.steering_axis, OPTIONS.steering_axes || ["left_x", "left_y", "right_x", "right_y", "left_trigger", "right_trigger", "none"]);
  const modeValues = OPTIONS.mapping_modes || ["gamepad", "keyboard"];
  fillSelectWithLabels(inputs.gas_brake_mapping_mode, modeValues.map((v) => ({ value: v, label: v === "gamepad" ? "手柄映射" : "键盘映射" })));
  fillSelectWithLabels(inputs.gear_mapping_mode, modeValues.map((v) => ({ value: v, label: v === "gamepad" ? "手柄映射" : "键盘映射" })));
  fillSelect(inputs.gas_output_button, OPTIONS.gamepad_bindings || []);
  fillSelect(inputs.brake_output_button, OPTIONS.gamepad_bindings || []);
  fillSelect(inputs.gear_up_button, OPTIONS.gamepad_bindings || []);
  fillSelect(inputs.gear_down_button, OPTIONS.gamepad_bindings || []);
}

function parseValues() {
  return {
    hud_fps: parseInt(inputs.hud_fps.value || String(DEFAULTS.hud_fps), 10),
    fullscreen_mode: !!inputs.fullscreen_mode.checked,
    mode_direction_enable: !!inputs.mode_direction_enable.checked,
    mode_linear_pedal_enable: !!inputs.mode_linear_pedal_enable.checked,
    mode_key_pedal_enable: !!inputs.mode_key_pedal_enable.checked,
    window_scale: clamp(parseFloat(inputs.window_scale.value || String(DEFAULTS.window_scale)), 0.8, 1.5),
    fullscreen_scale: clamp(parseFloat(inputs.fullscreen_scale.value || String(DEFAULTS.fullscreen_scale)), 0.8, 1.5),
    fullscreen_alpha: clamp(parseFloat(inputs.fullscreen_alpha.value || String(DEFAULTS.fullscreen_alpha)), 0.0, 1.0),
    reference_range_x_ratio: clamp(parseFloat(inputs.reference_range_x_ratio.value || String(DEFAULTS.reference_range_x_ratio)), 0.0, 1.0),
    reference_range_y_ratio: clamp(parseFloat(inputs.reference_range_y_ratio.value || String(DEFAULTS.reference_range_y_ratio)), 0.0, 1.0),
    min_output_x: clamp(parseFloat(inputs.min_output_x.value || String(DEFAULTS.min_output_x)), 0.0, 1.0),
    gear_pulse_ms: Math.round(clamp(parseFloat(inputs.gear_pulse_ms.value || String(DEFAULTS.gear_pulse_ms)), 10, 300)),
    hide_cursor_on_enable: inputs.hide_cursor_on_enable.value === "true",
    control_mode: flagsToControlMode(
      inputs.mode_direction_enable.checked,
      inputs.mode_linear_pedal_enable.checked,
      inputs.mode_key_pedal_enable.checked
    ),
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
  inputs.hud_fps.value = String(v.hud_fps ?? DEFAULTS.hud_fps);
  inputs.fullscreen_mode.checked = !!(v.fullscreen_mode ?? DEFAULTS.fullscreen_mode);
  inputs.window_scale.value = Number(v.window_scale ?? DEFAULTS.window_scale).toFixed(2);
  inputs.fullscreen_scale.value = Number(v.fullscreen_scale ?? DEFAULTS.fullscreen_scale).toFixed(2);
  inputs.fullscreen_alpha.value = Number(v.fullscreen_alpha ?? DEFAULTS.fullscreen_alpha).toFixed(2);
  inputs.reference_range_x_ratio.value = Number(v.reference_range_x_ratio ?? DEFAULTS.reference_range_x_ratio).toFixed(2);
  inputs.reference_range_y_ratio.value = Number(v.reference_range_y_ratio ?? DEFAULTS.reference_range_y_ratio).toFixed(2);
  inputs.min_output_x.value = Number(v.min_output_x ?? DEFAULTS.min_output_x).toFixed(3);
  inputs.gear_pulse_ms.value = String(v.gear_pulse_ms ?? DEFAULTS.gear_pulse_ms);
  inputs.hide_cursor_on_enable.value = (v.hide_cursor_on_enable ? "true" : "false");
  const flags = controlModeToFlags(v.control_mode ?? DEFAULTS.control_mode);
  inputs.mode_direction_enable.checked = !!(v.mode_direction_enable ?? flags.direction);
  inputs.mode_linear_pedal_enable.checked = !!(v.mode_linear_pedal_enable ?? flags.linear);
  inputs.mode_key_pedal_enable.checked = !!(v.mode_key_pedal_enable ?? flags.key);
  inputs.steering_axis.value = String(v.steering_axis ?? DEFAULTS.steering_axis);
  inputs.toggle_hotkey.value = String(v.toggle_hotkey ?? DEFAULTS.toggle_hotkey);
  inputs.switch_mode_hotkey.value = String(v.switch_mode_hotkey ?? DEFAULTS.switch_mode_hotkey);
  inputs.toggle_fullscreen_hotkey.value = String(v.toggle_fullscreen_hotkey ?? DEFAULTS.toggle_fullscreen_hotkey);
  inputs.open_settings_hotkey.value = String(v.open_settings_hotkey ?? DEFAULTS.open_settings_hotkey);
  inputs.gas_mouse_button.value = String(v.gas_mouse_button ?? DEFAULTS.gas_mouse_button);
  inputs.brake_mouse_button.value = String(v.brake_mouse_button ?? DEFAULTS.brake_mouse_button);
  inputs.gear_up_mouse_button.value = String(v.gear_up_mouse_button ?? DEFAULTS.gear_up_mouse_button);
  inputs.gear_down_mouse_button.value = String(v.gear_down_mouse_button ?? DEFAULTS.gear_down_mouse_button);
  inputs.gas_output_button.value = String(v.gas_output_button ?? DEFAULTS.gas_output_button);
  inputs.brake_output_button.value = String(v.brake_output_button ?? DEFAULTS.brake_output_button);
  inputs.gas_brake_mapping_mode.value = String(v.gas_brake_mapping_mode ?? DEFAULTS.gas_brake_mapping_mode);
  inputs.gas_key.value = String(v.gas_key ?? DEFAULTS.gas_key);
  inputs.brake_key.value = String(v.brake_key ?? DEFAULTS.brake_key);
  inputs.gear_mapping_mode.value = String(v.gear_mapping_mode ?? DEFAULTS.gear_mapping_mode);
  inputs.gear_up_button.value = String(v.gear_up_button ?? DEFAULTS.gear_up_button);
  inputs.gear_down_button.value = String(v.gear_down_button ?? DEFAULTS.gear_down_button);
  inputs.gear_up_key.value = String(v.gear_up_key ?? DEFAULTS.gear_up_key);
  inputs.gear_down_key.value = String(v.gear_down_key ?? DEFAULTS.gear_down_key);
  applyGearModeVisibility();
  applyPedalModeVisibility();
}

function hasChanges() {
  if (!initialValues) return false;
  const now = parseValues();
  const keys = Object.keys(now);
  for (const k of keys) {
    if (JSON.stringify(now[k]) !== JSON.stringify(initialValues[k])) {
      return true;
    }
  }
  return false;
}

function getEffectiveHotkeyFields() {
  const fields = [
    "toggle_hotkey",
    "switch_mode_hotkey",
    "toggle_fullscreen_hotkey",
    "open_settings_hotkey",
  ];
  if (inputs.gas_brake_mapping_mode.value === "keyboard") {
    fields.push("gas_key", "brake_key");
  }
  if (inputs.gear_mapping_mode.value === "keyboard") {
    fields.push("gear_up_key", "gear_down_key");
  }
  return fields;
}

function normalizeHotkeyValue(v) {
  return String(v || "").trim().toLowerCase();
}

function validateHotkeyConflicts(showAlert = false) {
  const allHotkeyInputs = document.querySelectorAll(".hotkey");
  allHotkeyInputs.forEach((el) => el.classList.remove("conflict"));

  const fields = getEffectiveHotkeyFields();
  const map = new Map();
  for (const f of fields) {
    const el = inputs[f];
    if (!el) continue;
    const val = normalizeHotkeyValue(el.value);
    if (!val || val === "none") continue;
    if (!map.has(val)) map.set(val, []);
    map.get(val).push(el);
  }

  let hasConflict = false;
  for (const [, list] of map.entries()) {
    if (list.length > 1) {
      hasConflict = true;
      list.forEach((el) => el.classList.add("conflict"));
    }
  }

  if (hasConflict && showAlert) {
    alert("有重复热键，请修改后再确认。");
  }
  return !hasConflict;
}

async function apply(closeAfter) {
  if (!validateHotkeyConflicts(true)) return;
  const v = parseValues();
  setValues(v);
  await Promise.race([
    window.pywebview.api.apply(v, closeAfter),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1500)),
  ]);
  initialValues = parseValues();
}

async function closePanel() {
  if (hasChanges()) {
    if (confirm("检测到修改，是否保存并应用？")) {
      try {
        await apply(true);
      } catch (e) {
        alert("应用设置失败，请重试。");
      }
      return;
    }
  }
  try {
    await Promise.race([
      window.pywebview.api.close_window(),
      new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1200)),
    ]);
  } catch (e) {
    alert("关闭设置窗口失败，请重试。");
  }
}

function bindHoverDetail(el, key) {
  el.addEventListener("mouseenter", () => { detailEl.textContent = detailMap[key] || ""; });
  el.addEventListener("mouseleave", () => {
    if (tabs.mode.classList.contains("active")) detailEl.textContent = detailMap.mode;
    else if (tabs.display.classList.contains("active")) detailEl.textContent = detailMap.display;
    else if (tabs.sense.classList.contains("active")) detailEl.textContent = detailMap.sense;
    else detailEl.textContent = detailMap.bind;
  });
}

function bindDragAdjust(el, inputKey, lo, hi, step) {
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
  const t = tokenFromEvent(e);
  if (!t) return;
  e.preventDefault();
  hotkeyPressed.add(t);
  const combo = formatCombo(hotkeyPressed);
  if (combo) {
    hotkeyCaptureTarget.value = combo;
    hotkeyLastCombo = combo;
  }
});

document.addEventListener("keyup", (e) => {
  if (!hotkeyCaptureTarget) return;
  const t = tokenFromEvent(e);
  if (!t) return;
  e.preventDefault();
  const isModifier = t === "ctrl" || t === "alt" || t === "shift";
  if (!isModifier && hotkeyLastCombo) {
    hotkeyCaptureTarget.value = hotkeyLastCombo;
    hotkeyCaptureTarget.blur();
    return;
  }
  hotkeyPressed.delete(t);
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
  document.getElementById("btn-reset-fullscreen-alpha").addEventListener("click", () => setField("fullscreen_alpha", String(DEFAULTS.fullscreen_alpha)));
  document.getElementById("btn-reset-ref-x-ratio").addEventListener("click", () => setField("reference_range_x_ratio", String(DEFAULTS.reference_range_x_ratio)));
  document.getElementById("btn-reset-ref-y-ratio").addEventListener("click", () => setField("reference_range_y_ratio", String(DEFAULTS.reference_range_y_ratio)));
  document.getElementById("btn-reset-min-output").addEventListener("click", () => setField("min_output_x", String(DEFAULTS.min_output_x)));
  document.getElementById("btn-reset-gear-pulse").addEventListener("click", () => setField("gear_pulse_ms", String(DEFAULTS.gear_pulse_ms)));
  document.getElementById("btn-reset-hide-cursor").addEventListener("click", () => setField("hide_cursor_on_enable", String(DEFAULTS.hide_cursor_on_enable)));

  ["toggle_hotkey", "switch_mode_hotkey", "toggle_fullscreen_hotkey", "open_settings_hotkey", "steering_axis", "gas_mouse_button", "brake_mouse_button", "gear_up_mouse_button", "gear_down_mouse_button", "gas_output_button", "brake_output_button", "gas_brake_mapping_mode", "gas_key", "brake_key", "gear_mapping_mode", "gear_up_button", "gear_down_button", "gear_up_key", "gear_down_key"].forEach((k) => {
    const r = document.getElementById(`reset-${k}`);
    if (r) r.addEventListener("click", () => setField(k, String(DEFAULTS[k])));
    const c = document.getElementById(`clear-${k}`);
    if (c) c.addEventListener("click", () => setField(k, "none"));
  });
}

tabs.mode.addEventListener("click", () => showPage("mode"));
tabs.display.addEventListener("click", () => showPage("display"));
tabs.sense.addEventListener("click", () => showPage("sense"));
tabs.bind.addEventListener("click", () => showPage("bind"));
inputs.gear_mapping_mode.addEventListener("change", applyGearModeVisibility);
inputs.gas_brake_mapping_mode.addEventListener("change", applyPedalModeVisibility);
inputs.gear_mapping_mode.addEventListener("change", () => validateHotkeyConflicts(false));
inputs.gas_brake_mapping_mode.addEventListener("change", () => validateHotkeyConflicts(false));
document.getElementById("btn-apply").addEventListener("click", async () => {
  try {
    await apply(false);
  } catch (e) {
    alert("应用设置失败，请重试。");
  }
});
document.getElementById("btn-confirm").addEventListener("click", async () => {
  try {
    await apply(true);
  } catch (e) {
    alert("确认并应用失败，请重试。");
  }
});
document.getElementById("btn-close").addEventListener("click", () => closePanel());
document.getElementById("btn-reset-all").addEventListener("click", () => {
  if (!confirm("是否确认重置全部设置？")) return;
  setValues(DEFAULTS);
});

for (const key of Object.keys(inputs)) {
  if (inputs[key]) bindHoverDetail(inputs[key], key);
}
["mode_direction_enable", "mode_linear_pedal_enable", "mode_key_pedal_enable", "fullscreen_mode", "window_scale", "fullscreen_scale", "fullscreen_alpha", "hud_fps", "reference_range_x_ratio", "reference_range_y_ratio", "min_output_x", "gear_pulse_ms", "hide_cursor_on_enable", "steering_axis", "toggle_hotkey", "switch_mode_hotkey", "toggle_fullscreen_hotkey", "open_settings_hotkey", "gas_mouse_button", "brake_mouse_button", "gear_up_mouse_button", "gear_down_mouse_button", "gas_output_button", "brake_output_button", "gas_brake_mapping_mode", "gas_key", "brake_key", "gear_mapping_mode", "gear_up_button", "gear_down_button", "gear_up_key", "gear_down_key"].forEach((k) => {
  const lbl = document.getElementById(`lbl-${k}`);
  if (lbl) bindHoverDetail(lbl, k);
});

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

bindHotkeyCapture(inputs.toggle_hotkey);
bindHotkeyCapture(inputs.switch_mode_hotkey);
bindHotkeyCapture(inputs.toggle_fullscreen_hotkey);
bindHotkeyCapture(inputs.open_settings_hotkey);
bindHotkeyCapture(inputs.gas_key);
bindHotkeyCapture(inputs.brake_key);
bindHotkeyCapture(inputs.gear_up_key);
bindHotkeyCapture(inputs.gear_down_key);
[
  inputs.toggle_hotkey,
  inputs.switch_mode_hotkey,
  inputs.toggle_fullscreen_hotkey,
  inputs.open_settings_hotkey,
  inputs.gas_key,
  inputs.brake_key,
  inputs.gear_up_key,
  inputs.gear_down_key,
].forEach((el) => {
  if (!el) return;
  el.addEventListener("input", () => validateHotkeyConflicts(false));
  el.addEventListener("blur", () => validateHotkeyConflicts(false));
});

wireIconActions();

function tryReadBootstrapStateFromWindow() {
  try {
    if (typeof window.__BOOTSTRAP_STATE__ === "object" && window.__BOOTSTRAP_STATE__ !== null) {
      return window.__BOOTSTRAP_STATE__;
    }
    return null;
  } catch (e) {
    return null;
  }
}

let __initStarted = false;
async function initSettingsUI() {
  if (__initStarted) return;
  __initStarted = true;
  applyOptionsFromConfig();
  let init = tryReadBootstrapStateFromWindow();
  if (!init) {
    try {
      const p = window.pywebview.api.get_initial();
      init = await Promise.race([
        p,
        new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 1200)),
      ]);
    } catch (e) {
      init = { ...DEFAULTS };
      alert("设置初始化读取超时，已使用默认值。可关闭后重开设置面板。");
    }
  }
  setValues(init);
  initialValues = parseValues();
  validateHotkeyConflicts(false);
  showPage("mode");
}

window.addEventListener("pywebviewready", () => {
  initSettingsUI();
});
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    initSettingsUI();
  }, 50);
});
