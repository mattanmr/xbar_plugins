#!/bin/bash
# Dexcom Glucose Reader for xbar - Automated Installer
# This script helps new users set up the plugin on macOS.

set -e

# 1. Check for Python 3
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Attempting to install via Homebrew..."
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is not installed. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$($(brew --prefix)/bin/brew shellenv)"
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
  XBAR_URL="https://github.com/matryer/xbar/releases/latest/download/xbar.zip"
  TMP_DIR=$(mktemp -d)
  curl -L "$XBAR_URL" -o "$TMP_DIR/xbar.zip"
  unzip -q "$TMP_DIR/xbar.zip" -d "$TMP_DIR"
  echo "Moving xbar to /Applications (may require your password)..."
  mv "$TMP_DIR/xbar.app" /Applications/
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
PLUGINS_DIR=$(osascript -e 'tell application "xbar" to POSIX path of (get plugins folder)')
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
