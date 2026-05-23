# Mouse2Pad 绑定与配置说明

本文档与当前代码实现保持一致（`gamepad_mouse_mapper.py` + `settings_defaults.cfg`）。

## 模式对照（`control_mode`）

| 模式 | 名称 | 行为 |
|---|---|---|
| 1 | 方向 + 线性 RT/LT | 鼠标 X -> 转向；鼠标 Y 上/下 -> RT/LT 线性 |
| 2 | 方向 + 按键 RT/LT | 鼠标 X -> 转向；油门键/刹车键 -> RT/LT=1.00 |
| 3 | 仅线性 RT/LT | 不控制方向；鼠标 Y 上/下 -> RT/LT 线性 |
| 4 | 仅按键 RT/LT | 不控制方向；油门键/刹车键 -> RT/LT=1.00 |

## 功能热键（`config.cfg`）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `toggle_hotkey` | `shift+v` | 开关映射 |
| `toggle_fullscreen_hotkey` | `alt+f` | HUD 全屏切换 |

热键格式示例：`shift+v`、`alt+f`、`f10`、`ctrl+alt+r`

## 鼠标绑定（`config.cfg`）

| 配置项 | 默认值 | 可选值（由 `settings_options.cfg` 提供） |
|---|---|---|
| `gas_mouse_button` | `right` | `left` / `right` / `middle` / `x1` / `x2` / `wheel_up` / `wheel_down` / `none` |
| `brake_mouse_button` | `left` | 同上 |
| `gear_up_mouse_button` | `wheel_up` | 同上 |
| `gear_down_mouse_button` | `wheel_down` | 同上 |

## 踏板/换挡映射（`config.cfg`）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `gas_brake_mapping_mode` | `gamepad` | 踏板映射模式：`gamepad` / `keyboard` / `none` |
| `gear_mapping_mode` | `gamepad` | 换挡映射模式：`gamepad` / `keyboard` / `none` |
| `gas_output_button` | `right_trigger` | 油门输出映射（手柄信号名） |
| `brake_output_button` | `left_trigger` | 刹车输出映射（手柄信号名） |
| `gear_up_button` | `right_thumb` | 升档输出映射（手柄信号名） |
| `gear_down_button` | `left_thumb` | 降档输出映射（手柄信号名） |
| `gas_key` | `w` | 踏板键盘油门（`keyboard` 模式下生效） |
| `brake_key` | `s` | 踏板键盘刹车（`keyboard` 模式下生效） |
| `gear_up_key` | `e` | 键盘升档（`keyboard` 模式下生效） |
| `gear_down_key` | `q` | 键盘降档（`keyboard` 模式下生效） |
| `gear_pulse_ms` | `45` | 换挡脉冲时长，范围会被限制在 `10~300` ms |

## HUD 与显示

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `hud_fps` | `60` | HUD 刷新帧率；可选值来自 `settings_options.cfg`（默认 `15/30/60/90/120`） |
| `debug_mode` | `false` | 调试文本开关 |
| `fullscreen_mode` | `false` | HUD 是否全屏显示 |
| `windows_scale` | `1.00` | 窗口缩放，限制 `0.8~1.5` |
| `fullscreen_scale` | `1.00` | 全屏缩放，限制 `0.8~1.5` |
| `fullscreen_alpha` | `0.50` | 全屏透明度，限制 `0~1` |
| `hide_cursor_on_enable` | `true` | 启用映射时隐藏鼠标 |

## 灵敏度与转向

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `reference_range_x_ratio` | `0.63` | X 向灵敏度比例（`0~1`） |
| `reference_range_y_ratio` | `0.52` | Y 向灵敏度比例（`0~1`） |
| `min_output_x` | `0.235` | 非零转向最小输出（`0~1`） |
| `steering_axis` | `left_x` | 转向映射轴（`left_x`/`left_y`/`right_x`/`right_y`/`left_trigger`/`right_trigger`/`none`） |

说明：代码内部仍保留 `reference_range_x_px` / `reference_range_y_px` 以兼容旧配置，但新语义优先使用 ratio 字段。
