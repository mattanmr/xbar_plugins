# Dexcom Glucose Reader for macOS menu bar

**Version:** 1.0.0

This plugin displays your Dexcom glucose readings directly in your macOS menu bar using [xbar](https://xbarapp.com/). Features include real-time glucose readings with trend arrows, sparkline graphs, and automatic update notifications.

---

## Disclaimer

This software is provided "as is" and is intended for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Use of this program is at your own risk.

## No Liability

The authors and contributors of this software accept no responsibility or liability for any effects, behaviors, damages, or other issues that may arise from the use or misuse of this software. By using this program, you agree that you do so at your own risk and that you assume full responsibility for any consequences.

---

## Features

- **Real-time glucose readings** with trend arrows
- **Sparkline graph** showing recent glucose history
- **Automatic update checking** (weekly, with user approval required)
- **Automatic rollback** on update failures
- **Multi-region support** for Dexcom servers (USA, outside USA, Japan)
- **Customizable settings** for history window and graph points

---

## Quick Start: One-Line Installation (Recommended)

Copy and paste the following command into your Terminal to download all necessary files and run the installer:

```sh
curl -O https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/install.sh \
     -O https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom.5m.py && \
chmod +x install.sh && \
./install.sh
```

After the script completes, follow the popup instructions to finish configuring your Dexcom plugin.

---

## Configuration

Once installed, you can configure the plugin by clicking the xbar menu icon and selecting "Open Plugin" next to the Dexcom Glucose Reader. Configure the following settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `USERNAME` | (required) | Your Dexcom account username/email |
| `PASSWORD` | (required) | Your Dexcom account password |
| `REGION` | "outside USA" | Dexcom server location: "in USA", "outside USA", or "Japan" |
| `MINUTES` | 90 | Historical data window in minutes |
| `GRAPH_POINTS` | 24 | Number of data points to display in the graph |
| `VAR_VERBOSE` | false | Enable detailed output for debugging |

---

## Auto-Update Feature

The plugin includes an intelligent auto-update system:

- **Weekly checks**: The plugin checks for new releases once per week (respects GitHub API rate limits: 60/hour)
- **User approval required**: Updates are never installed automatically - you must click to approve
- **Automatic backup**: Your current version is backed up before updating (only one backup kept at a time)
- **Automatic rollback**: If the update fails on first run, the plugin automatically restores the previous version
- **Update notifications**: When an update is available, you'll see "🆕 Update available: v1.0.0 → v2.0.0" in the dropdown menu

### How Updates Work

1. Plugin checks GitHub releases API weekly
2. If new version found, notification appears in xbar dropdown
3. Click "Install Update vX.X.X" to approve
4. Current version backed up to `~/.config/dexcom_plugin/backup/`
5. New version downloaded and installed
6. On first run, if errors occur, automatic rollback restores previous version

---

## Dependencies

The installer automatically installs:
- **Python 3** (if not already installed)
- **pip** (Python package manager)
- **pydexcom** - Python library for Dexcom API access
- **sparklines** - For text-based graph visualization

---

## Manual Installation (Advanced)

If you prefer manual setup, see the [install.sh](install.sh) script for required steps.

---

## Troubleshooting

**Error: Invalid credentials or "Dexcom service unavailable"**
- Verify your Dexcom username and password are correct
- Ensure your internet connection is working
- Check that you've selected the correct region for your Dexcom server

**Plugin won't load in xbar**
- Ensure the file is executable: `chmod +x ~/Library/Application\ Support/xbar/plugins/dexcom.5m.py`
- Check xbar's plugin error log for details
- Verify all Python dependencies are installed

**Update failed and rollback didn't work**
- Reinstall from scratch using the one-line installation command above
- Your config directory (`~/.config/dexcom_plugin/`) contains logs that can help diagnose issues

---

## Uninstalling

### Option 1: Via xbar (Quick Uninstall)

1. Open xbar plugin browser
2. Find the Dexcom Glucose Reader plugin
3. Click **Uninstall this plugin**
4. Refresh xbar

**Note:** This removes the plugin but leaves configuration files and dependencies intact.

### Option 2: Complete Manual Cleanup

To completely remove all traces of the plugin:

```bash
# 1. Remove the plugin file
rm ~/Library/Application\ Support/xbar/plugins/dexcom.5m.py

# 2. Remove configuration directory (includes updater module, backups, and logs)
rm -rf ~/.config/dexcom_plugin

# 3. Remove Python dependencies (optional - only if not used by other apps)
python3 -m pip uninstall -y pydexcom sparklines

# 4. Refresh xbar
# Click xbar icon in menu bar > Refresh All
```

**Warning:** Removing `~/.config/dexcom_plugin/` will delete your backups and update history. Only do this if you're completely removing the plugin.

---

## File Locations

- **Plugin:** `~/Library/Application Support/xbar/plugins/dexcom.5m.py`
- **Config:** `~/.config/dexcom_plugin/config.json`
- **Updater Module:** `~/.config/dexcom_plugin/dexcom_updater.py`
- **Backup:** `~/.config/dexcom_plugin/backup/`
- **Logs:** `~/.config/dexcom_plugin/update.log`

---

For questions or help, open an issue on this repository.
