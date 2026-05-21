const detailEl = document.getElementById("detail");
const tabs = {
  display: document.getElementById("tab-display"),
  sense: document.getElementById("tab-sense"),
  bind: document.getElementById("tab-bind"),
};
const pages = {
  display: document.getElementById("page-display"),
  sense: document.getElementById("page-sense"),
  bind: document.getElementById("page-bind"),
};

const inputs = {
  fullscreen_mode: document.getElementById("fullscreen_mode"),
  window_scale: document.getElementById("window_scale"),
  fullscreen_scale: document.getElementById("fullscreen_scale"),
  hud_fps: document.getElementById("hud_fps"),
  min_output_x: document.getElementById("min_output_x"),
  gear_pulse_ms: document.getElementById("gear_pulse_ms"),
  hide_cursor_on_enable: document.getElementById("hide_cursor_on_enable"),
  control_mode: document.getElementById("control_mode"),
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
  display: "图像显示设置提示。",
  sense: "灵敏度设置提示。",
  bind: "快捷键与映射设置提示。",
  fullscreen_mode: "切换 HUD 全屏或窗口模式。",
  window_scale: "小窗显示缩放比例。",
  fullscreen_scale: "全屏显示缩放比例。",
  hud_fps: "HUD 刷新帧率档位。",
  min_output_x: "非零方向起始输出，值越大起步越敏感。",
  gear_pulse_ms: "换挡脉冲持续时长（毫秒）。",
  hide_cursor_on_enable: "实验功能：开启映射时尝试隐藏光标。",
  control_mode: "方向控制模式。",
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

const DEFAULTS = {
  hud_fps: 60,
  fullscreen_mode: false,
  window_scale: 1.0,
  fullscreen_scale: 1.0,
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

let initialValues = null;
let dragState = null;
let hotkeyCaptureTarget = null;
let hotkeyPressed = new Set();
let hotkeyLastCombo = "";
const GAMEPAD_BINDINGS = [
  "right_shoulder", "left_shoulder", "left_thumb", "right_thumb",
  "back", "start", "guide", "a", "b", "x", "y",
  "dpad_up", "dpad_down", "dpad_left", "dpad_right",
  "left_stick_left", "left_stick_right", "left_stick_up", "left_stick_down",
  "right_stick_left", "right_stick_right", "right_stick_up", "right_stick_down",
  "left_trigger", "right_trigger", "none",
];

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
  tabs.display.classList.toggle("active", kind === "display");
  tabs.sense.classList.toggle("active", kind === "sense");
  tabs.bind.classList.toggle("active", kind === "bind");
  pages.display.classList.toggle("hidden", kind !== "display");
  pages.sense.classList.toggle("hidden", kind !== "sense");
  pages.bind.classList.toggle("hidden", kind !== "bind");
  detailEl.textContent = detailMap[kind] || "";
}

function fillSelect(selectEl, values) {
  if (!selectEl) return;
  const prev = selectEl.value;
  selectEl.innerHTML = values.map((v) => `<option value="${v}">${v}</option>`).join("");
  if (values.includes(prev)) selectEl.value = prev;
}

function parseValues() {
  return {
    hud_fps: parseInt(inputs.hud_fps.value || "60", 10),
    fullscreen_mode: !!inputs.fullscreen_mode.checked,
    window_scale: clamp(parseFloat(inputs.window_scale.value || "1"), 0.8, 1.5),
    fullscreen_scale: clamp(parseFloat(inputs.fullscreen_scale.value || "1"), 0.8, 1.5),
    min_output_x: clamp(parseFloat(inputs.min_output_x.value || "0.235"), 0.0, 1.0),
    gear_pulse_ms: Math.round(clamp(parseFloat(inputs.gear_pulse_ms.value || "45"), 10, 300)),
    hide_cursor_on_enable: inputs.hide_cursor_on_enable.value === "true",
    control_mode: parseInt(inputs.control_mode.value || "1", 10),
    steering_axis: (inputs.steering_axis.value || "left_x").trim(),
    toggle_hotkey: (inputs.toggle_hotkey.value || "").trim(),
    switch_mode_hotkey: (inputs.switch_mode_hotkey.value || "").trim(),
    toggle_fullscreen_hotkey: (inputs.toggle_fullscreen_hotkey.value || "").trim(),
    open_settings_hotkey: (inputs.open_settings_hotkey.value || "").trim(),
    gas_mouse_button: (inputs.gas_mouse_button.value || "right").trim(),
    brake_mouse_button: (inputs.brake_mouse_button.value || "left").trim(),
    gear_up_mouse_button: (inputs.gear_up_mouse_button.value || "wheel_up").trim(),
    gear_down_mouse_button: (inputs.gear_down_mouse_button.value || "wheel_down").trim(),
    gas_output_button: (inputs.gas_output_button.value || "right_trigger").trim(),
    brake_output_button: (inputs.brake_output_button.value || "left_trigger").trim(),
    gas_brake_mapping_mode: (inputs.gas_brake_mapping_mode.value || "gamepad").trim(),
    gas_key: (inputs.gas_key.value || "w").trim(),
    brake_key: (inputs.brake_key.value || "s").trim(),
    gear_mapping_mode: (inputs.gear_mapping_mode.value || "gamepad").trim(),
    gear_up_button: (inputs.gear_up_button.value || "right_thumb").trim(),
    gear_down_button: (inputs.gear_down_button.value || "left_thumb").trim(),
    gear_up_key: (inputs.gear_up_key.value || "e").trim(),
    gear_down_key: (inputs.gear_down_key.value || "q").trim(),
  };
}

function setValues(v) {
  inputs.hud_fps.value = String(v.hud_fps ?? 60);
  inputs.fullscreen_mode.checked = !!(v.fullscreen_mode ?? false);
  inputs.window_scale.value = Number(v.window_scale).toFixed(2);
  inputs.fullscreen_scale.value = Number(v.fullscreen_scale).toFixed(2);
  inputs.min_output_x.value = Number(v.min_output_x).toFixed(3);
  inputs.gear_pulse_ms.value = String(v.gear_pulse_ms ?? 45);
  inputs.hide_cursor_on_enable.value = (v.hide_cursor_on_enable ? "true" : "false");
  inputs.control_mode.value = String(v.control_mode ?? 1);
  inputs.steering_axis.value = String(v.steering_axis ?? "left_x");
  inputs.toggle_hotkey.value = String(v.toggle_hotkey ?? "shift+v");
  inputs.switch_mode_hotkey.value = String(v.switch_mode_hotkey ?? "alt+shift+v");
  inputs.toggle_fullscreen_hotkey.value = String(v.toggle_fullscreen_hotkey ?? "alt+f");
  inputs.open_settings_hotkey.value = String(v.open_settings_hotkey ?? "ctrl+shift+o");
  inputs.gas_mouse_button.value = String(v.gas_mouse_button ?? "right");
  inputs.brake_mouse_button.value = String(v.brake_mouse_button ?? "left");
  inputs.gear_up_mouse_button.value = String(v.gear_up_mouse_button ?? "wheel_up");
  inputs.gear_down_mouse_button.value = String(v.gear_down_mouse_button ?? "wheel_down");
  inputs.gas_output_button.value = String(v.gas_output_button ?? "right_trigger");
  inputs.brake_output_button.value = String(v.brake_output_button ?? "left_trigger");
  inputs.gas_brake_mapping_mode.value = String(v.gas_brake_mapping_mode ?? "gamepad");
  inputs.gas_key.value = String(v.gas_key ?? "w");
  inputs.brake_key.value = String(v.brake_key ?? "s");
  inputs.gear_mapping_mode.value = String(v.gear_mapping_mode ?? "gamepad");
  inputs.gear_up_button.value = String(v.gear_up_button ?? "right_thumb");
  inputs.gear_down_button.value = String(v.gear_down_button ?? "left_thumb");
  inputs.gear_up_key.value = String(v.gear_up_key ?? "e");
  inputs.gear_down_key.value = String(v.gear_down_key ?? "q");
  applyGearModeVisibility();
  applyPedalModeVisibility();
}

function hasChanges() {
  return JSON.stringify(parseValues()) !== JSON.stringify(initialValues);
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
  initialValues = v;
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
    if (tabs.display.classList.contains("active")) detailEl.textContent = detailMap.display;
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
  document.getElementById("btn-reset-min-output").addEventListener("click", () => setField("min_output_x", "0.235"));
  document.getElementById("btn-reset-gear-pulse").addEventListener("click", () => setField("gear_pulse_ms", "45"));
  document.getElementById("btn-reset-hide-cursor").addEventListener("click", () => setField("hide_cursor_on_enable", "true"));

  ["toggle_hotkey", "switch_mode_hotkey", "toggle_fullscreen_hotkey", "open_settings_hotkey", "steering_axis", "gas_mouse_button", "brake_mouse_button", "gear_up_mouse_button", "gear_down_mouse_button", "gas_output_button", "brake_output_button", "gas_brake_mapping_mode", "gas_key", "brake_key", "gear_mapping_mode", "gear_up_button", "gear_down_button", "gear_up_key", "gear_down_key"].forEach((k) => {
    const r = document.getElementById(`reset-${k}`);
    if (r) r.addEventListener("click", () => setField(k, String(DEFAULTS[k])));
    const c = document.getElementById(`clear-${k}`);
    if (c) c.addEventListener("click", () => setField(k, "none"));
  });
}

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
["fullscreen_mode", "window_scale", "fullscreen_scale", "hud_fps", "min_output_x", "gear_pulse_ms", "hide_cursor_on_enable", "control_mode", "steering_axis", "toggle_hotkey", "switch_mode_hotkey", "toggle_fullscreen_hotkey", "open_settings_hotkey", "gas_mouse_button", "brake_mouse_button", "gear_up_mouse_button", "gear_down_mouse_button", "gas_output_button", "brake_output_button", "gas_brake_mapping_mode", "gas_key", "brake_key", "gear_mapping_mode", "gear_up_button", "gear_down_button", "gear_up_key", "gear_down_key"].forEach((k) => {
  const lbl = document.getElementById(`lbl-${k}`);
  if (lbl) bindHoverDetail(lbl, k);
});

bindDragAdjust(document.getElementById("lbl-window_scale"), "window_scale", 0.8, 1.5, 0.01);
bindDragAdjust(inputs.window_scale, "window_scale", 0.8, 1.5, 0.01);
bindDragAdjust(document.getElementById("lbl-fullscreen_scale"), "fullscreen_scale", 0.8, 1.5, 0.01);
bindDragAdjust(inputs.fullscreen_scale, "fullscreen_scale", 0.8, 1.5, 0.01);
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

window.addEventListener("pywebviewready", async () => {
  fillSelect(inputs.gas_output_button, GAMEPAD_BINDINGS);
  fillSelect(inputs.brake_output_button, GAMEPAD_BINDINGS);
  fillSelect(inputs.gear_up_button, GAMEPAD_BINDINGS);
  fillSelect(inputs.gear_down_button, GAMEPAD_BINDINGS);
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
  initialValues = init;
  setValues(init);
  validateHotkeyConflicts(false);
  showPage("display");
});
