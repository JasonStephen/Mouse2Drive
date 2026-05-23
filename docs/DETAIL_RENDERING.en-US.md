# Detail Panel Rendering Syntax

This document describes the rendering rules for the right-side Detail panel text (implemented in `web_settings_ui/app.js`).

## Supported Syntax

1. Line break  
Use `/n` for a new line.

2. Bold  
Use `[b]...[/b]`.

3. Color tags (visual boldness is controlled by CSS)
- Severe warning (red): `[swarn]...[/swarn]`
- Warning (yellow): `[warn]...[/warn]`
- Success/done (green): `[success]...[/success]`
- Info (blue): `[info]...[/info]`

## Example

```text
[b]Control Mode Notes[/b]/n
[info]Info: Steering, pedal, and gear can be toggled independently.[/info]/n
[warn]Warning: Duplicate hotkeys may cause conflicts.[/warn]/n
[swarn]Severe: Virtual gamepad is not available.[/swarn]/n
[success]Done: Current settings were applied successfully.[/success]
```

## Notes

1. Plain text works without any tags.  
2. Tags must be properly closed, for example `[warn]...[/warn]`.  
3. Input text is HTML-escaped first, then tag replacement is applied.  
