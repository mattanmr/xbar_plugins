# Dexcom Glucose Reader for macOS menu bar

This plugin displays your Dexcom glucose readings directly in your macOS menu bar using [xbar](https://xbarapp.com/). Features include color-coded glucose values, a real-time graph visualization, and recent reading history.

---

## Features

- **Real-time glucose readings** in your menu bar with trend arrows
- **Color-coded values**: Red (high), Green (normal), Blue (low)
- **Embedded glucose graph** showing the last readings with color-coded visualization
- **Recent readings history** in dropdown menu with configurable count
- **Customizable thresholds** for high/low glucose alerts
- **Multi-region support** for Dexcom servers (USA, outside USA, Japan)

---

## Disclaimer

This software is provided "as is" and is intended for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Use of this program is at your own risk.

## No Liability

The authors and contributors of this software accept no responsibility or liability for any effects, behaviors, damages, or other issues that may arise from the use or misuse of this software. By using this program, you agree that you do so at your own risk and that you assume full responsibility for any consequences.

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
| `HIGH_THRESHOLD` | 130 | Blood glucose level (mg/dL) considered "high" (triggers red color) |
| `LOW_THRESHOLD` | 75 | Blood glucose level (mg/dL) considered "low" (triggers blue color) |
| `LAST_READINGS` | 4 | Number of recent readings to show in the dropdown menu |
| `VAR_VERBOSE` | false | Enable detailed output for debugging |

---

## Dependencies

The installer automatically installs the following:
- **Python 3** (if not already installed)
- **pydexcom** - Python library for Dexcom API access
- **gnuplot** - For graph visualization (installed via Homebrew)

---

## Manual Installation (Advanced)

If you prefer manual setup, see the [install.sh](install.sh) script for required steps.

---

## Troubleshooting

**Error: "gnuplot error"**
- Ensure gnuplot is installed: `brew install gnuplot`
- If using a non-standard Python installation, update the shebang in `dexcom.5m.py` to match your Python path
- Add Homebrew to your PATH if needed: `export PATH="/opt/homebrew/bin:$PATH"`

**Error: Invalid credentials or "Dexcom service unavailable"**
- Verify your Dexcom username and password are correct
- Ensure your internet connection is working
- Check that you've selected the correct region for your Dexcom server

**Graph not appearing**
- Make sure gnuplot is installed: `which gnuplot`
- Try running the script manually in Terminal to see any error messages
- Check that `/tmp/` is writable on your system

**Plugin won't load in xbar**
- Ensure the file is executable: `chmod +x ~/Library/Application\ Support/xbar/plugins/dexcom.5m.py`
- Check xbar's plugin error log for details
- Verify all Python dependencies are installed

## Uninstalling

- In xbar, open the plugin browser, find the Dexcom Glucose Reader plugin, and click **Uninstall this plugin**.
- Alternatively, you can delete `dexcom.5m.py` (and any json files containing `dexcom.5m` in the filename) from your xbar plugins folder and restart xbar.
- Optionally uninstall gnuplot if you don't need it elsewhere: `brew uninstall gnuplot`

---

For questions or help, open an issue on this repository.
