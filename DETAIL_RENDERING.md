# Detail Panel Rendering Guide

This document defines the rendering syntax for the right-side "Detail" panel.

## Supported Syntax

1. Line break  
Use `/n` for a new line.

2. Bold  
Use `[b]...[/b]`.

3. Color tags (auto-bold)
- Severe warning (red): `[swarn]...[/swarn]`
- Normal warning (yellow): `[warn]...[/warn]`
- Success/down (green): `[success]...[/success]`
- Information (blue): `[info]...[/info]`

All 4 color tags are automatically bold.

## Example

```text
[b]Control Mode Notes[/b]/n
[info]Info: Direction, pedal, and gear can be toggled independently.[/info]/n
[warn]Warning: Duplicate hotkeys may cause conflicts.[/warn]/n
[swarn]Severe: Virtual gamepad is not available.[/swarn]/n
[success]Down: Current settings have been applied successfully.[/success]
```

## Notes

1. Plain text still works without tags.
2. Tags must be properly closed, for example `[warn]...[/warn]`.
3. Input text is HTML-escaped before rendering.
