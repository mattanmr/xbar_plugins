#!/bin/bash
# Dexcom Glucose Reader for xbar - Automated Installer
# This script helps new users set up the plugin on macOS.

set -e

# 0. check for xcode
if ! xcode-select -p 1>/dev/null 2>&1; then
  tmp_file=/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
  touch "$tmp_file"
  label=$(softwareupdate -l | grep -B 1 -E 'Command Line Tools' | awk -F'*' '/^ *\\*/ {print $2}' | sed -e 's/^ *Label: //' -e 's/^ *//' | sort -V | tail -n1)
  # $label is like 'Command Line Tools for Xcode-16.0'
  if [ -n "$label" ]; then
    softwareupdate -i "$label"
  fi
  rm -f "$tmp_file"
fi

# 1. Check for Python 3
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Attempting to install via Homebrew..."
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is not installed. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$($(brew --prefix)/bin/brew shellenv)"
    echo "Adding Homebrew to PATH"
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
  brew install python
fi

# 2. Install pip if missing
if ! python3 -m pip --version >/dev/null 2>&1; then
  echo "pip not found. Installing pip..."
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python3 get-pip.py
  rm get-pip.py
fi

# 3. Install required Python packages
python3 -m pip install --user --upgrade pydexcom sparklines

# 4. Check for xbar and install if missing
if ! ls /Applications | grep -i xbar >/dev/null 2>&1; then
  echo "xbar is not installed. Downloading and installing xbar..."
  XBAR_URL="https://github.com/matryer/xbar/releases/download/v2.1.7-beta/xbar.v2.1.7-beta.dmg"
  TMP_DIR=$(mktemp -d)
  curl -L "$XBAR_URL" -o "$TMP_DIR/xbar.dmg"
  hdiutil attach "$TMP_DIR/xbar.dmg"
  cp -r "/Volumes/Install xbar/xbar.app" /Applications/
  #sudo installer -package /Volumes/xbar/xbar.pkg -target /Applications
  hdiutil detach "/Volumes/Install xbar"
  rm -rf "$TMP_DIR"
  echo "xbar installed."
fi

# 5. Start xbar if not running
if ! pgrep -x "xbar" >/dev/null; then
  echo "Starting xbar..."
  open -a xbar
  sleep 2
fi

# 6. Find xbar plugins folder
#PLUGINS_DIR=$(osascript -e 'tell application "xbar" to POSIX path of (get plugins folder)')
PLUGINS_DIR="$HOME/Library/Application Support/xbar/plugins"
if [ ! -d "$PLUGINS_DIR" ]; then
  echo "Could not find xbar plugins folder. Please open xbar, then try again."
  exit 1
fi

# 7. Copy plugin file
cp dexcom.5m.py "$PLUGINS_DIR/"
echo "Plugin copied to xbar plugins folder."

# 8. Open plugins folder for user
open "$PLUGINS_DIR"

# 9. Try to open plugin configuration (if possible)
# Note: xbar does not have a public AppleScript API for opening plugin config, so we provide clear instructions

echo "\nSetup complete!"
echo "- Please left-click the Dexcom plugin in your menu bar, choose 'xbar' > 'Open Plugin', and enter your Dexcom credentials."
echo "- If you have any issues, see the README for troubleshooting."
