# Mouse2Pad 绑定对照表

## 🎛 模式对照
| 模式 | 名称 | 行为 |
|---|---|---|
| 1 | 方向 + 线性RT/LT | 鼠标X -> 左摇杆X；鼠标Y上/下 -> RT/LT线性 |
| 2 | 方向 + 按键RT/LT | 鼠标X -> 左摇杆X；油门键/刹车键 -> RT/LT=1.00 |
| 3 | 仅线性RT/LT | 不控制方向；鼠标Y上/下 -> RT/LT线性 |
| 4 | 仅按键RT/LT | 不控制方向；油门键/刹车键 -> RT/LT=1.00 |

## ⌨️ 热键绑定（config.cfg）
| 配置项 | 默认值 | 说明 |
|---|---|---|
| `reset_hotkey` | `f10` | 复位（参考点回中） |
| `toggle_hotkey` | `shift+v` | 开关映射 |
| `switch_mode_hotkey` | `alt+shift+v` | 模式切换（1→2→3→4） |

热键格式：`shift+v`、`alt+shift+v`、`f10`、`ctrl+alt+r`

## 🖱 鼠标绑定（config.cfg）
| 配置项 | 默认值 | 可选值 |
|---|---|---|
| `gas_mouse_button` | `right` | `left` / `right` / `middle` |
| `brake_mouse_button` | `left` | `left` / `right` / `middle` |

## 🎮 虚拟手柄换挡绑定（config.cfg）
| 配置项 | 默认值 | 可选值 |
|---|---|---|
| `gear_up_button` | `right_shoulder` | `right_shoulder`, `left_shoulder`, `a`, `b`, `x`, `y`, `dpad_up`, `dpad_down`, `dpad_left`, `dpad_right` |
| `gear_down_button` | `left_shoulder` | 同上 |
| `gear_pulse_ms` | `45` | 按键脉冲时长（ms） |

## 📺 HUD
| 配置项 | 默认值 | 说明 |
|---|---|---|
| `hud_fps` | `25` | HUD刷新帧率（5~240） |
| `debug_mode` | `1` | 调试文本开关（on/off, true/false, 1/0） |

## 🧭 转向显示说明
`L` 滑块使用分段可视化区间：
- `[-1.00, -min_output_x)`
- `0`
- `(min_output_x, 1.00]`

这样可避免最小输出在视觉上“贴近中心但仍有值”的误判。
