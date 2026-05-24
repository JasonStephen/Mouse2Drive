# FH Liner Controller 首次操作指引（中文）

FH Liner Controller本身是我为了游玩地平线6逛风景时，能有一个像使用方向盘开车一样的体验而设计的该工具。因为补齐了功能，也希望能分享给您。

但实际上该工具理论可以使用在非常多的游戏中，但仅在极限竞速地平线6中测试过。

本工具可以让您在游戏中使用鼠标去控制车的方向、油门刹车以及换挡的功能，就像你用方向盘开车一样丝滑。

但对于新手首次使用，非常建议您可以查看我们的操作指引，在默认配置下如何使用本工具游玩地平线6。本工具将围绕默认配置进行操作指引，当然后续您也可以通过设置面板修改设置。

!!! 本项目的线性控制基于Xbox虚拟手柄映射 !!!


---

## 一、启动前准备

---

- 1. 本工具需要提前下载并安装 Python 3.11+
- 2. 在根目录找到 run.bat 启动程序
- 3. 第一次启动会自动部署环境以及需要的依赖。
*注意：请确保启动时你的鼠标位于你的游戏对应的屏幕，否则多屏用户可能会出现全屏HUD显示在错误的屏幕上。


---

## 二、默认快捷键（开箱即用）

---

- 1. 鼠标控制启用/关闭：Shift + V
- 2. 全屏/窗口切换：Alt + F
- 3. 你可以随时通过设置按钮打开设置面板修改设置，锁定解锁按钮调整小窗或是全屏HUD的指示器位置。


---

## 三、默认配置

---

- 1. 在使用 Shift + V 启用鼠标控制后，鼠标向上滑为油门（默认右扳机键），向下滑为刹车（默认左扳机键），左划为左转，右划为右转（默认左摇杆的X轴）
- 2. 在 手动档 下，使用鼠标滚轮，上滚和下滚可以实现升档（键盘Q键）和降档（键盘E键）
- 3. 设置中开启 按键油刹 ，可使用鼠标左右键分别控制刹车（默认满右扳机键）和油门（默认满左扳机键）。


---

## 四、可编辑范围

---

- 1. 窗口模式HUD 支持调整窗口的位置
- 2. 全屏模式HUD 支持调整方向、油门、刹车指示滑块的位置
- 3. 支持调整转向和油门刹车灵敏度
- 4. 支持调整油门、刹车控制的鼠标绑键
- 5. 油门刹车和升降档控制均支持手柄映射和键盘映射两种模式


---

## 五、关于游戏内的设置调整

---

在 游戏设置>高级控制 中：
关闭鼠标自由视角，避免右键冲突
转向轴响应起点 设置为 0
转向轴响应终点 设置为 100
转向线性度 建议往高调整，亲测 75 体验较佳。


---

## 六、已知问题

---

- 1. 设置界面基于Web网页开发，启动时间较长，敬请谅解。
- 2. 鼠标无法被隐藏，目前判断是和地平线6冲突导致，暂未找到解决方法。
- 3. 尽管已经尝试修复了，但有小概率出现设置界面无响应问题。
*如果有遇到其他问题，请在B站评论区或者GitHub告诉我。


---

# FH Liner Controller First-Time Guide (English)

FH Liner Controller itself is a tool I designed so that when playing Forza Horizon 6 and cruising for scenery, I could have an experience similar to driving with a steering wheel. Since the features are now more complete, I also hope to share it with you.

In theory, this tool can be used in many games, but in practice it has only been tested in Forza Horizon 6.

This tool lets you use the mouse in-game to control steering, throttle/brake, and gear shifting, with a smooth feel similar to driving with a wheel.

For first-time users, it is highly recommended to follow this guide to use the tool under default settings for Forza Horizon 6. This guide is built around the default configuration. Of course, you can later modify settings through the settings panel.

!!! The linear control in this project is based on Xbox virtual gamepad mapping !!!


---

## 1. Before Launch

---

- 1. Please install Python 3.11+ in advance.
- 2. Find `run.bat` in the project root directory to start the program.
- 3. On first launch, the environment and required dependencies will be deployed automatically.
*Note: Make sure your mouse is on the screen where the game is running when launching. Otherwise, in multi-monitor setups, the fullscreen HUD may appear on the wrong screen.*


---

## 2. Default Hotkeys (Ready Out of the Box)

---

- 1. Enable/Disable mouse control: `Shift + V`
- 2. Fullscreen/Window toggle: `Alt + F`
- 3. You can open the settings panel at any time via the settings button to modify settings, and use the lock/unlock button to adjust indicator positions in windowed HUD or fullscreen HUD.


---

## 3. Default Configuration

---

- 1. After enabling mouse control with `Shift + V`, moving the mouse upward is throttle (default right trigger), downward is brake (default left trigger), left is turn left, and right is turn right (default left stick X-axis).
- 2. In manual transmission mode, using the mouse wheel, scroll up/down can shift up/down (keyboard `Q` and `E`).
- 3. If Key Pedal mode is enabled in settings, you can use the left/right mouse buttons to control brake (default full right trigger) and throttle (default full left trigger).


---

## 4. Editable Scope

---

- 1. Window-mode HUD supports adjusting the window position.
- 2. Fullscreen-mode HUD supports adjusting indicator slider positions for steering, throttle, and brake.
- 3. Supports adjusting steering and throttle/brake sensitivity.
- 4. Supports adjusting mouse bindings for throttle and brake control.
- 5. Throttle/brake and gear shift controls both support two modes: gamepad mapping and keyboard mapping.


---

## 5. In-Game Settings Suggestions

---

In `Game Settings > Advanced Controls`:
Disable mouse free-look to avoid right-click conflicts.
Set Steering Axis Deadzone Inside to `0`.
Set Steering Axis Deadzone Outside to `100`.
For Steering Linearity, a higher value is recommended; in testing, `75` felt better.


---

## 6. Known Issues

---

- 1. The settings UI is web-based, so startup can be relatively slow. Thank you for understanding.
- 2. Mouse cursor hiding may fail; currently this appears to conflict with Forza Horizon 6, and no reliable fix has been found yet.
- 3. Although fixes have been attempted, there is still a small chance that the settings panel becomes unresponsive.
*If you encounter other issues, please let me know in Bilibili comments or on GitHub.*

