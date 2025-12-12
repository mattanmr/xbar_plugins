#!/bin/bash
# Dexcom Glucose Reader for xbar - Automated Installer
# This script helps new users set up the plugin on macOS.

set -e
set -x  # Enable debug output

# -----------------------------
# 0. Check for Xcode Command Line Tools
# -----------------------------
if ! xcode-select -p 1>/dev/null 2>&1; then
  tmp_file="/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"
  touch "$tmp_file"
  label=$(softwareupdate -l | grep -B 1 -E 'Command Line Tools' | awk -F'*' '/^ *\\*/ {print $2}' | sed -e 's/^ *Label: //' -e 's/^ *//' | sort -V | tail -n1)
  if [ -n "$label" ]; then
    softwareupdate -i "$label"
  fi
  rm -f "$tmp_file"
fi

# -----------------------------
# 1. Check for Python 3
# -----------------------------
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

# -----------------------------
# 2. Install pip if missing
# -----------------------------
if ! python3 -m pip --version >/dev/null 2>&1; then
  echo "pip not found. Installing pip..."
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python3 get-pip.py
  rm get-pip.py
fi

# -----------------------------
# 3. Install required Python packages
# -----------------------------
python3 -m pip install --user --upgrade pydexcom

# -----------------------------
# 3b. Install gnuplot
# -----------------------------
if ! command -v gnuplot >/dev/null 2>&1; then
  echo "gnuplot is not installed. Installing via Homebrew..."
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is not installed. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$($(brew --prefix)/bin/brew shellenv)"
    echo "Adding Homebrew to PATH"
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
  brew install gnuplot
else
  echo "gnuplot is already installed"
fi

# -----------------------------
# 3b. Create config directory for plugin
# -----------------------------
CONFIG_DIR="$HOME/.config/dexcom_plugin"
echo "Creating plugin config directory: $CONFIG_DIR"
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    echo "Created config directory at $CONFIG_DIR"
else
    echo "Config directory already exists at $CONFIG_DIR"
fi

# Copy updater module to config directory (will be imported by plugin)
cp dexcom_updater.py "$CONFIG_DIR/"
echo "Update manager module copied to config directory."
chmod +x "$CONFIG_DIR/dexcom_updater.py"

# Initialize config.json if it doesn't exist (preserve existing config on updates)
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating initial config.json..."
    cat > "$CONFIG_FILE" << 'EOF'
{
  "current_version": "2.0.0",
  "last_check_ts": 0,
  "first_run_after_update": false,
  "backup_version": null,
  "repo": "mattanmr/xbar_plugins",
  "source_ref": "update_process",
  "manifest_url": "https://raw.githubusercontent.com/mattanmr/xbar_plugins/update_process/update_manifest.json",
  "version_url": "https://raw.githubusercontent.com/mattanmr/xbar_plugins/update_process/VERSION",
  "dependencies": {
    "pip": ["pydexcom"],
    "homebrew": ["gnuplot"]
  }
}
EOF
    echo "Created config.json"
else
    echo "Config file already exists - preserving existing configuration"
fi

# -----------------------------
# 4. Prompt for Accessibility Permissions
# -----------------------------
result=$(osascript -e 'display alert "Please allow xbar to control system events" message "If popup appears, please choose '"'Allow'"' xbar to control system events" buttons {"OK", "Cancel"} default button "OK" cancel button "Cancel"')
if [[ "$result" == "button returned:OK" ]]; then
    echo "User chose OK"
else
    echo "User cancelled or closed the dialog."
fi

# -----------------------------
# 5. Check for xbar and install if missing
# -----------------------------
XBAR_APP_PATH="/Applications/xbar.app"
if [ ! -d "$XBAR_APP_PATH" ]; then
  echo "xbar is not installed. Downloading and installing xbar..."
  XBAR_URL="https://github.com/matryer/xbar/releases/download/v2.1.7-beta/xbar.v2.1.7-beta.dmg"
  TMP_DIR=$(mktemp -d)
  curl -L "$XBAR_URL" -o "$TMP_DIR/xbar.dmg"
  hdiutil attach "$TMP_DIR/xbar.dmg"
  cp -r "/Volumes/Install xbar/xbar.app" /Applications/
  hdiutil detach "/Volumes/Install xbar"
  rm -rf "$TMP_DIR"
  echo "xbar installed."
else
  echo "xbar is already installed at $XBAR_APP_PATH"
fi

# -----------------------------
# 6. Start xbar if not running
# -----------------------------
if ! pgrep -x "xbar" >/dev/null; then
  echo "Starting xbar..."
  open -a /Applications/xbar.app
  sleep 2
fi

# -----------------------------
# 7. Ensure xbar plugins directory exists
# -----------------------------
PLUGINS_DIR="$HOME/Library/Application Support/xbar/plugins"
echo "Checking for plugins directory: $PLUGINS_DIR"
if [ ! -d "$PLUGINS_DIR" ]; then
    mkdir -p "$PLUGINS_DIR"
    echo "Created xbar plugins folder at $PLUGINS_DIR"
else
    echo "Found xbar plugins folder at $PLUGINS_DIR"
fi
if [ ! -d "$PLUGINS_DIR" ]; then
    echo "Could not find or create xbar plugins folder. Please open xbar, then try again."
    exit 1
fi

# -----------------------------
# 8. Copy plugin file
# -----------------------------
cp dexcom.5m.py "$PLUGINS_DIR/"
echo "Plugin copied to xbar plugins folder."
chmod +x "$PLUGINS_DIR/dexcom.5m.py"

# -----------------------------
# 9. Open plugins folder for user
# -----------------------------
open "$PLUGINS_DIR"

# -----------------------------
# 10. Open xbar app
# -----------------------------
open -a /Applications/xbar.app

# -----------------------------
# 11. Final instructions (popup)
# -----------------------------
osascript <<EOD
  display dialog "Setup complete!\n\nPlease refresh xbar by clicking the xbar icon in the menu bar or using the 'Refresh All' option.\n\n- Please left-click the Dexcom plugin in your menu bar, choose 'xbar' > 'Open Plugin', enter your Dexcom credentials and acknowledge the disclaimer.\n- If you have any issues, see the README for troubleshooting." with title "Dexcom xbar Plugin Installer" buttons {"OK"} default button "OK"
EOD
