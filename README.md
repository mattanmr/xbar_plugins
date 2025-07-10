# Dexcom Glucose Reader for xbar

This plugin displays your Dexcom glucose readings directly in your macOS menu bar using [xbar](https://xbarapp.com/).

---

## Disclaimer

This software is provided "as is" and is intended for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Use of this program is at your own risk.

## No Liability

The authors and contributors of this software accept no responsibility or liability for any effects, behaviors, damages, or other issues that may arise from the use or misuse of this software. By using this program, you agree that you do so at your own risk and that you assume full responsibility for any consequences.

---

## Step-by-Step Setup Instructions

### 1. Install Python (if you don't have it)
- Open **Terminal** (find it in Applications > Utilities).
- Type `python3 --version` and press Enter.
  - If you see a version (e.g., `Python 3.9.6`), you have Python installed. Skip to the next step.
  - If you see an error, install Python:
    - Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest version for macOS.
    - Open the downloaded file and follow the installation instructions.

### 2. Install xbar
- Go to [xbarapp.com](https://xbarapp.com/) and download xbar for macOS.
- Open the downloaded file and move xbar to your Applications folder.
- Open xbar. It will appear in your menu bar.

### 3. Download the Plugin
- Download the `dexcom.5m.py` file from this repository.
- Place the file in your xbar plugins folder:
  - In xbar, click the menu bar icon > Preferences > Open Plugins Folder.
  - Move `dexcom.5m.py` into this folder.

### 4. Install Required Python Packages
- Open **Terminal**.
- Install the required packages by running:
  ```sh
  python3 -m pip install pydexcom sparklines
  ```

### 5. Configure Your Dexcom Account Details
- In xbar, **left-click** the plugin in the menu bar, then choose **xbar** > **Open Plugin**.
- Enter your Dexcom account ID and password, and set your region (in USA, outside USA, or Japan).
- You can also adjust other settings like history minutes and graph points if desired.

### 6. View Your Glucose Data
- The plugin will update every 5 minutes and show your latest glucose reading and a graph in the menu bar.

---

## Troubleshooting
- If you see an error, make sure your Dexcom credentials are correct and your internet connection is working.
- If you have issues with Python or packages, try restarting your computer after installation.

## Uninstalling
- In xbar, open the plugin browser, find the Dexcom Glucose Reader plugin, and click **Uninstall this plugin**.
- Alternatively, you can delete `dexcom.5m.py` (and any json files contining `dexcom.5m` in the filename) from your xbar plugins folder and restart xbar.

---

For questions or help, open an issue on this repository.
