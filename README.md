# Dexcom Glucose Reader for macOS menu bar

This plugin displays your Dexcom glucose readings directly in your macOS menu bar using [xbar](https://xbarapp.com/).

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
     -O https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom.5m.py \
     -O https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/update.sh && \
chmod +x install.sh update.sh && \
./install.sh
```

After the script completes, follow the popup instructions to finish configuring your Dexcom plugin.

---

## Update Feature
- The plugin will automatically check for updates from the main branch.
- If a new version is available, you will see an "Update Available" option in the xbar menu.
- Click "Update Plugin" to update your local files using the included `update.sh` script.

---

## Manual Installation (Advanced)

If you prefer manual setup, see the [install.sh](install.sh) script for required steps.

---

## Troubleshooting
- If you see an error, make sure your Dexcom credentials are correct and your internet connection is working.
- If you have issues with Python or packages, try restarting your computer after installation.

## Uninstalling
- In xbar, open the plugin browser, find the Dexcom Glucose Reader plugin, and click **Uninstall this plugin**.
- Alternatively, you can delete `dexcom.5m.py` (and any json files containing `dexcom.5m` in the filename) from your xbar plugins folder and restart xbar.

---

For questions or help, open an issue on this repository.
