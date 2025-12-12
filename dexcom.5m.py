#!/usr/bin/env python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v1.0.0</xbar.version>
# <xbar.author>Mattan Ram</xbar.author>
# <xbar.author.github>mattanmr</xbar.author.github>
# <xbar.desc>DISCLAIMER: This software is provided "as is" for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Use at your own risk. The authors accept no liability for any consequences of use or misuse.</xbar.desc>
# <xbar.image>https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom_reader.png</xbar.image>
# <xbar.dependencies>python</xbar.dependencies>

# <xbar.var>string(PASSWORD=""): Your dexcom account password </xbar.var>
# <xbar.var>string(USERNAME=""): Your dexcom account username </xbar.var>
# <xbar.var>number(MINUTES=90): amount of history in minutes </xbar.var>
# <xbar.var>number(GRAPH_POINTS=24): amount of points in the graph </xbar.var>
# <xbar.var>select(REGION="outside USA"): Where your Dexcom server is [in USA, outside USA, Japan]</xbar.var>
# <xbar.var>boolean(VAR_VERBOSE=false): Display attributes data?</xbar.var>

# DISCLAIMER:
# This software is provided "as is" for informational and convenience purposes only.
# It is not intended to replace professional medical advice, diagnosis, or counseling.
# Use at your own risk. The authors accept no liability for any consequences of use or misuse.

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from pydexcom import Dexcom
from sparklines import sparklines

# Import update manager classes from config directory
try:
    config_dir = Path.home() / ".config" / "dexcom_plugin"
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    from dexcom_updater import ConfigManager, UpdateChecker, DependencyManager, UpdateInstaller
except ImportError:
    # If updater module not found, define minimal fallback
    ConfigManager = None

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

VERSION = "1.0.0"
GITHUB_REPO = "mattanmr/xbar_plugins"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CONFIG_DIR = Path.home() / ".config" / "dexcom_plugin"
CONFIG_FILE = CONFIG_DIR / "config.json"
UPDATE_LOG = CONFIG_DIR / "update.log"
BACKUP_DIR = CONFIG_DIR / "backup"
PLUGINS_DIR = Path.home() / "Library" / "Application Support" / "xbar" / "plugins"
PLUGIN_FILE = PLUGINS_DIR / "dexcom.5m.py"

# Update check interval (7 days in seconds)
UPDATE_CHECK_INTERVAL = 7 * 24 * 60 * 60

REGION_MAP = {
    "in USA": "us",
    "outside USA": "ous",
    "Japan": "jp"
}

# ============================================================================
# ENVIRONMENT VARIABLES & SETUP
# ============================================================================

# Get environment variables
user_password: str = os.environ.get("PASSWORD", "")
username: str = os.environ.get("USERNAME", "")
history_minutes: int = int(os.environ.get("MINUTES", 90))
graph_points: int = int(os.environ.get("GRAPH_POINTS", 24))
env_region: str = os.environ.get("REGION", "outside USA")
region: str = REGION_MAP.get(env_region, "ous")
verbose: bool = os.environ.get("VAR_VERBOSE", "false").lower() == "true"

# ============================================================================
# MAIN GLUCOSE READING FUNCTION
# ============================================================================


def fetch_and_display_glucose():
    """Fetch glucose data and display in xbar format."""
    try:
        dexcom = Dexcom(username=username, password=user_password, region=region)
        reading = dexcom.get_current_glucose_reading()
        value = reading.value
        arrow = reading.trend_arrow
        reading_time = reading.datetime
        
        readings = dexcom.get_glucose_readings(minutes=history_minutes)
        values = [r.value for r in reversed(readings[:graph_points])]
        graph = sparklines(values)[0]

        print(f"({reading_time.strftime('%H:%M') if reading_time else 'N/A'}) {value} {arrow}")
        print("---")
        
        if verbose:
            print(f"Last reading: {reading_time.strftime('%H:%M') if reading_time else 'N/A'}")
            print(f"Verbose: {verbose}")
            print(f"Region: {env_region}")
            print("---")
        print(f"Graph: {graph}")

    except Exception as e:
        print("❌ Error")
        print("---")
        print(f"Error fetching glucose data: {str(e)}")


def check_and_display_updates():
    """Check for updates and display notification if available."""
    if ConfigManager is None:
        return  # Silently skip if update module not available
        
    config_mgr = ConfigManager(CONFIG_FILE)
    config = config_mgr.load()
    
    # Check if enough time has passed since last check
    last_check = config.get('last_check', 0)
    current_time = datetime.now().timestamp()
    
    if current_time - last_check > UPDATE_CHECK_INTERVAL:
        checker = UpdateChecker(VERSION, GITHUB_API_URL)
        update_available, new_version, download_url = checker.check_for_updates()
        
        # Update last check time
        config['last_check'] = current_time
        config_mgr.save(config)
        
        if update_available and new_version:
            print(f"🆕 Update available: v{VERSION} → v{new_version}")
            print(f"--Install Update v{new_version} | bash='{sys.executable}' param1='{PLUGIN_FILE}' param2='--install-update' param3='{download_url}' param4='{new_version}' terminal=false refresh=true")
            print("---")


def handle_update_command():
    """Handle update installation from command line."""
    if ConfigManager is None:
        print("❌ Update module not available")
        sys.exit(1)
        
    if len(sys.argv) >= 5 and sys.argv[2] == '--install-update':
        download_url = sys.argv[3]
        new_version = sys.argv[4]
        
        config_mgr = ConfigManager(CONFIG_FILE)
        dep_mgr = DependencyManager(config_mgr)
        installer = UpdateInstaller(config_mgr, dep_mgr, PLUGIN_FILE, BACKUP_DIR)
        
        # Create backup
        if not installer.create_backup():
            print("❌ Failed to create backup. Update cancelled.")
            sys.exit(1)
        
        # Install update
        if installer.install_update(download_url, new_version):
            print(f"✅ Successfully updated to v{new_version}")
            print("Please refresh xbar to see changes.")
        else:
            print("❌ Update failed. Rolling back...")
            installer.rollback()
        
        sys.exit(0)


def handle_first_run_after_update():
    """Handle first run after update - check for errors and rollback if needed."""
    if ConfigManager is None:
        return  # Skip if update module not available
        
    config_mgr = ConfigManager(CONFIG_FILE)
    config = config_mgr.load()
    
    if config.get('first_run_after_update', False):
        # Clear the flag
        config['first_run_after_update'] = False
        config_mgr.save(config)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main execution function."""
    # Handle update command if present
    if len(sys.argv) > 2 and sys.argv[2] == '--install-update':
        handle_update_command()
        return
    
    # Initialize config on first run
    config_mgr = ConfigManager(CONFIG_FILE)
    config = config_mgr.load()
    
    # Handle first run after update
    handle_first_run_after_update()
    
    try:
        # Check for updates (weekly)
        check_and_display_updates()
        
        # Display glucose data
        fetch_and_display_glucose()
        
    except Exception as e:
        # If this is first run after update and error occurs, rollback
        if ConfigManager is not None:
            config = config_mgr.load()
            if config.get('first_run_after_update', False):
                dep_mgr = DependencyManager(config_mgr)
                installer = UpdateInstaller(config_mgr, dep_mgr, PLUGIN_FILE, BACKUP_DIR)
                
                print("❌ Error after update")
                print("---")
                print("Rolling back to previous version...")
                
                if installer.rollback():
                    backup_version = config.get('backup_version', 'previous')
                    print(f"✅ Rollback successful - restored v{backup_version}")
                    print("Please refresh xbar and report this issue on GitHub.")
                else:
                    print("❌ Rollback failed")
                    print("Please reinstall manually from GitHub.")
                return
        
        # Normal error handling
        print("❌ Error")
        print("---")
        print(f"Error: {str(e)}")
        if verbose:
            print("---")
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
