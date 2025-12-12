# Dexcom Glucose Reader for macOS menu bar

**Version:** 2.0.0

This plugin displays your Dexcom glucose readings directly in your macOS menu bar using [xbar](https://xbarapp.com/). Features include real-time glucose readings with trend arrows, embedded glucose graphs, automatic update checking, and recent reading history.

---

## Disclaimer

This software is provided "as is" and is intended for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Use of this program is at your own risk.

## No Liability

The authors and contributors of this software accept no responsibility or liability for any effects, behaviors, damages, or other issues that may arise from the use or misuse of this software. By using this program, you agree that you do so at your own risk and that you assume full responsibility for any consequences.

---

## Features

- **Real-time glucose readings** in your menu bar with trend arrows
- **Color-coded values**: Red (high), Green (normal), Blue (low)
- **Embedded glucose graph** showing recent readings with color-coded visualization
- **Recent readings history** in dropdown menu with configurable count
- **Customizable thresholds** for high/low glucose alerts
- **Multi-region support** for Dexcom servers (USA, outside USA, Japan)
- **Automatic update checking** (weekly, with user approval required)
- **Automatic rollback** on update failures
- **Single backup retention** of previous plugin version
- **Dependency management** with optional auto-cleanup

---

## Quick Start: One-Line Installation (Recommended)

Copy and paste the following command into your Terminal to download all necessary files and run the installer:

```sh
curl -O https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/install.sh && chmod +x install.sh && ./install.sh
```

The installer will:
1. Install system dependencies (Xcode tools, Python, pip)
2. Install Python dependencies (pydexcom, gnuplot)
3. Create configuration directory (`~/.config/dexcom_plugin/`)
4. Deploy the plugin to xbar
5. Launch xbar and open the plugin settings

---

## Manual Installation

If you prefer manual installation:

1. **Download the files:**
   ```sh
   # Create config directory
   mkdir -p ~/.config/dexcom_plugin
   
   # Download plugin
   curl -O ~/Library/Application\ Support/xbar/plugins/dexcom.5m.py \
     https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom.5m.py
   
   # Download updater module
   curl -O ~/.config/dexcom_plugin/dexcom_updater.py \
     https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom_updater.py
   ```

2. **Install dependencies:**
   ```sh
   # Install Python dependencies
   pip3 install pydexcom
   
   # Install gnuplot (using Homebrew)
   brew install gnuplot
   ```

3. **Make plugin executable:**
   ```sh
   chmod +x ~/Library/Application\ Support/xbar/plugins/dexcom.5m.py
   ```

4. **Configure in xbar:**
   - Open xbar's Plugin Browser
   - Find "Dexcom Glucose Reader"
   - Click the gear icon to set variables
   - Acknowledge the disclaimer by setting `ACKNOWLEDGE_DISCLAIMER` to true
   - Enter your Dexcom username and password
   - Select your region

---

## Configuration

### Required Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ACKNOWLEDGE_DISCLAIMER` | boolean | false | **REQUIRED**: Set to true to confirm you've read the disclaimer |
| `USERNAME` | string | (empty) | Your Dexcom account username/email |
| `PASSWORD` | string | (empty) | Your Dexcom account password |
| `REGION` | select | outside USA | Your Dexcom server region |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MINUTES` | number | 90 | Minutes of history to display in graph |
| `GRAPH_POINTS` | number | 24 | Number of data points in glucose graph |
| `HIGH_THRESHOLD` | number | 130 | High glucose threshold (mg/dL) |
| `LOW_THRESHOLD` | number | 75 | Low glucose threshold (mg/dL) |
| `LAST_READINGS` | number | 4 | Number of recent readings to show |
| `VAR_VERBOSE` | boolean | false | Enable verbose logging and error details |

---

## Auto-Update System

### How It Works

The plugin includes an automatic update checker that:

1. **Checks weekly** for new releases on GitHub
2. **Notifies you** when an update is available
3. **Requires approval** before updating (manual click required)
4. **Creates backup** of your current version before updating
5. **Auto-rollback** if the new version fails
6. **Tracks dependencies** and alerts on changes

### Update Check Configuration

- Updates are checked **once per week**
- You'll see an orange "Update available" notification in the menu bar
- Click the notification to view release details
- Updates require **explicit approval** - no automatic installation
- Your current version is **backed up** before any update
- If the updated version fails, it **automatically restores** your backup

### Manual Update Check

To trigger an update check immediately:
1. Reset the last check timestamp in config.json
2. The plugin will check for updates on its next run

---

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| `dexcom.5m.py` | `~/Library/Application Support/xbar/plugins/` | Main plugin (executed by xbar) |
| `dexcom_updater.py` | `~/.config/dexcom_plugin/` | Update management module |
| `config.json` | `~/.config/dexcom_plugin/` | Version tracking, update status, settings |
| `backup/` | `~/.config/dexcom_plugin/backup/` | Stores single backup of previous version |
| `update.log` | `~/.config/dexcom_plugin/` | Update operation logs |

---

## Troubleshooting

### "Graph unavailable" message

**Cause:** gnuplot is not installed or not in PATH

**Solution:**
```sh
brew install gnuplot
# Verify installation
which gnuplot  # Should output /opt/homebrew/bin/gnuplot or similar
```

### "Error fetching glucose data"

**Causes:**
- Incorrect username/password
- Network connectivity issue
- Dexcom server is down
- Region setting is incorrect

**Solutions:**
1. Verify your Dexcom username (email) and password in xbar settings
2. Test your internet connection
3. Confirm your region setting matches your Dexcom account location
4. Check status at https://status.dexcomcloud.com/
5. Enable `VAR_VERBOSE` for detailed error messages

### "Update system not available"

**Cause:** dexcom_updater.py is missing from `~/.config/dexcom_plugin/`

**Solution:**
```sh
# Re-run the installer
curl -O install.sh https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/install.sh
chmod +x install.sh
./install.sh
```

### Dependency issues after update

The plugin tracks dependency changes between versions. If asked to remove old dependencies:

```sh
# Automatic removal (if prompted)
pip3 uninstall sparklines  # v1.0.0 dependency, not needed in v2.0.0

# Manual removal (if needed)
pip3 uninstall -y sparklines
```

---

## Uninstallation

### Method 1: Via xbar GUI (Recommended)

1. Open xbar
2. Open Plugin Browser
3. Find "Dexcom Glucose Reader"
4. Click the "X" button to uninstall

### Method 2: Manual Uninstallation

```sh
# Remove plugin from xbar
rm ~/Library/Application\ Support/xbar/plugins/dexcom.5m.py

# Remove configuration directory and all related files
rm -rf ~/.config/dexcom_plugin/

# Optional: Remove Python dependencies
pip3 uninstall pydexcom  # Keeps pydexcom if you use it for other projects
```

---

## Support & Contributing

- **Issues:** Please report bugs on [GitHub Issues](https://github.com/mattanmr/xbar_plugins/issues)
- **Suggestions:** Feature requests welcome via GitHub Issues
- **Contributing:** Pull requests are welcome for bug fixes and enhancements

---

## License

This project is provided as-is for personal use. See the disclaimer above.

## Acknowledgments

- [xbar](https://xbarapp.com/) - Menu bar app framework
- [pydexcom](https://github.com/statik/pydexcom) - Dexcom API wrapper
- [gnuplot](http://www.gnuplot.info/) - Graph visualization
