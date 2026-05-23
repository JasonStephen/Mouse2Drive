param(
    [string]$Version = "0.5.0"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$DistDir = Join-Path $ProjectRoot ("dist\\Mouse_Controller_v" + $Version)
$BuildDir = Join-Path $ProjectRoot "build\\pyinstaller"
$VersionFile = Join-Path $ProjectRoot "build\\version_info_0_5_0.txt"

$IconIco = Join-Path $ProjectRoot "icon\\icon.ico"
$IconPng = Join-Path $ProjectRoot "icon\\icon.png"
$IconArg = @()
if (Test-Path $IconIco) {
    $IconArg = @("--icon", $IconIco)
} elseif (Test-Path $IconPng) {
    Write-Host "Warning: only icon.png found. For reliable Windows EXE icon, please provide icon\\icon.ico."
}

if (!(Test-Path $VersionFile)) {
    throw "Version file not found: $VersionFile"
}

python -m pip install -U pip
python -m pip install pyinstaller pywebview pynput vgamepad

if (Test-Path $DistDir) {
    Remove-Item -LiteralPath $DistDir -Recurse -Force
}

$common = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--version-file", $VersionFile
)

# Build settings window executable
pyinstaller @common @IconArg `
    "--name" "settings_webview" `
    "--add-data" "web_settings_ui;web_settings_ui" `
    "--add-data" "settings_defaults.cfg;." `
    "--add-data" "settings_options.cfg;." `
    "--add-data" "i18n_zh-CN.cfg;." `
    "--add-data" "i18n_en-US.cfg;." `
    "settings_webview.py"

# Build main executable
pyinstaller @common @IconArg `
    "--name" "Mouse_Controller" `
    "--add-data" "settings_defaults.cfg;." `
    "--add-data" "settings_options.cfg;." `
    "--add-data" "i18n_zh-CN.cfg;." `
    "--add-data" "i18n_en-US.cfg;." `
    "gamepad_mouse_mapper.py"

# Keep editable runtime config in output root
Copy-Item -LiteralPath "config.cfg" -Destination (Join-Path $DistDir "config.cfg") -Force

Write-Host "Build completed: $DistDir"
