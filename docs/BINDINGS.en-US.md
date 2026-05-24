# Mouse2Pad Bindings and Config Reference

This document is aligned with the current implementation (`gamepad_mouse_mapper.py` + `config/settings_defaults.cfg`).

## Mode Mapping (`control_mode`)

| Mode | Name | Behavior |
|---|---|---|
| 1 | Steering + Linear RT/LT | Mouse X -> steering; Mouse Y up/down -> linear RT/LT |
| 2 | Steering + Key RT/LT | Mouse X -> steering; throttle/brake keys -> RT/LT=1.00 |
| 3 | Linear RT/LT Only | No steering; Mouse Y up/down -> linear RT/LT |
| 4 | Key RT/LT Only | No steering; throttle/brake keys -> RT/LT=1.00 |

## Function Hotkeys (`config/config.cfg`)

| Key | Default | Description |
|---|---|---|
| `toggle_hotkey` | `shift+v` | Toggle mapping on/off |
| `toggle_fullscreen_hotkey` | `alt+f` | Toggle HUD fullscreen |

Hotkey format examples: `shift+v`, `alt+f`, `f10`, `ctrl+alt+r`

## Mouse Bindings (`config/config.cfg`)

| Key | Default | Options (from `config/settings_options.cfg`) |
|---|---|---|
| `gas_mouse_button` | `right` | `left` / `right` / `middle` / `x1` / `x2` / `wheel_up` / `wheel_down` / `none` |
| `brake_mouse_button` | `left` | same as above |
| `gear_up_mouse_button` | `wheel_up` | same as above |
| `gear_down_mouse_button` | `wheel_down` | same as above |

## Pedal/Gear Mapping (`config/config.cfg`)

| Key | Default | Description |
|---|---|---|
| `gas_brake_mapping_mode` | `gamepad` | Pedal mapping mode: `gamepad` / `keyboard` / `none` |
| `gear_mapping_mode` | `gamepad` | Gear mapping mode: `gamepad` / `keyboard` / `none` |
| `gas_output_button` | `right_trigger` | Throttle output binding (gamepad signal name) |
| `brake_output_button` | `left_trigger` | Brake output binding (gamepad signal name) |
| `gear_up_button` | `right_thumb` | Gear-up output binding (gamepad signal name) |
| `gear_down_button` | `left_thumb` | Gear-down output binding (gamepad signal name) |
| `gas_key` | `w` | Keyboard throttle (`keyboard` mode only) |
| `brake_key` | `s` | Keyboard brake (`keyboard` mode only) |
| `gear_up_key` | `e` | Keyboard gear up (`keyboard` mode only) |
| `gear_down_key` | `q` | Keyboard gear down (`keyboard` mode only) |
| `gear_pulse_ms` | `45` | Shift pulse length, clamped to `10~300` ms |

## HUD and Display

| Key | Default | Description |
|---|---|---|
| `hud_fps` | `60` | HUD refresh FPS; options come from `config/settings_options.cfg` (default `15/30/60/90/120`) |
| `debug_mode` | `false` | Debug text switch |
| `fullscreen_mode` | `false` | HUD fullscreen mode |
| `windows_scale` | `1.00` | Window scale, clamped to `0.8~1.5` |
| `fullscreen_scale` | `1.00` | Fullscreen scale, clamped to `0.8~1.5` |
| `fullscreen_alpha` | `0.50` | Fullscreen opacity, clamped to `0~1` |
| `hide_cursor_on_enable` | `true` | Hide cursor while mapping is enabled |

## Sensitivity and Steering

| Key | Default | Description |
|---|---|---|
| `reference_range_x_ratio` | `0.63` | X sensitivity ratio (`0~1`) |
| `reference_range_y_ratio` | `0.52` | Y sensitivity ratio (`0~1`) |
| `min_output_x` | `0.235` | Minimum non-zero steering output (`0~1`) |
| `steering_axis` | `left_x` | Steering target axis (`left_x`/`left_y`/`right_x`/`right_y`/`left_trigger`/`right_trigger`/`none`) |

Note: the code still keeps `reference_range_x_px` / `reference_range_y_px` for backward compatibility, but ratio fields are the preferred semantics.

