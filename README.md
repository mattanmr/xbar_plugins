# Dexcom Glucose Reader for macOS menu bar

This plugin displays your Dexcom glucose readings directly in your macOS menu bar using [xbar](https://xbarapp.com/).

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
