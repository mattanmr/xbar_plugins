#!/usr/bin/env python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v2.0.0</xbar.version>
# <xbar.author>Mattan Ram</xbar.author>
# <xbar.author.github>mattanmr</xbar.author.github>
# <xbar.desc>DISCLAIMER: This software is provided "as is" for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Use at your own risk. The authors accept no liability for any consequences of use or misuse.</xbar.desc>
# <xbar.image>https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom_reader.png</xbar.image>
# <xbar.dependencies>gnuplot</xbar.dependencies>

# <xbar.var>boolean(ACKNOWLEDGE_DISCLAIMER=false): BY SETTING THIS VARIABLE TO TRUE, YOU ACKNOWLEDGE THAT YOU HAVE READ AND UNDERSTOOD THE DISCLAIMER PROVIDED IN THE PLUGIN DESCRIPTION.</xbar.var>
# <xbar.var>string(PASSWORD=""): Your dexcom account password </xbar.var>
# <xbar.var>string(USERNAME=""): Your dexcom account username </xbar.var>
# <xbar.var>number(MINUTES=90): amount of history in minutes </xbar.var>
# <xbar.var>number(GRAPH_POINTS=24): amount of points in the graph </xbar.var>
# <xbar.var>number(HIGH_THRESHOLD=130): High glucose threshold </xbar.var>
# <xbar.var>number(LOW_THRESHOLD=75): Low glucose threshold </xbar.var>
# <xbar.var>number(LAST_READINGS=4): number of last readings to show in the dropdown menu </xbar.var>
# <xbar.var>select(REGION="outside USA"): Where your Dexcom server is [in USA, outside USA, Japan]</xbar.var>
# <xbar.var>boolean(VAR_VERBOSE=false): Display attributes data?</xbar.var>

# DISCLAIMER:
# This software is provided "as is" for informational and convenience purposes only.
# It is not intended to replace professional medical advice, diagnosis, or counseling.
# Use at your own risk. The authors accept no liability for any consequences of use or misuse.

import os
import sys
import subprocess
import base64
import traceback
import math
from datetime import datetime
from pathlib import Path
from pydexcom import Dexcom

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

VERSION = "2.0.0"
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

# Color configuration: hex values for different glucose states
COLORS = {
    "low": {"hex": "0x3b82f6", "name": "blue"},      # Blue
    "normal": {"hex": "0x22c55e", "name": "green"},  # Green
    "high": {"hex": "0xef4444", "name": "red"}       # Red
}

COLOR_PALETTE = "1 '#3b82f6', 2 '#22c55e', 3 '#ef4444'"  # Blue, Green, Red

# ============================================================================
# ENVIRONMENT VARIABLES & SETUP
# ============================================================================

# Read environment variables with defaults
username = os.getenv("USERNAME", "")
user_password = os.getenv("PASSWORD", "")
env_region = os.getenv("REGION", "outside USA")
region = REGION_MAP.get(env_region, "ous")
history_minutes = int(os.getenv("MINUTES", "90"))
graph_points = int(os.getenv("GRAPH_POINTS", "24"))
high_threshold = int(os.getenv("HIGH_THRESHOLD", "130"))
low_threshold = int(os.getenv("LOW_THRESHOLD", "75"))
last_readings = int(os.getenv("LAST_READINGS", "4"))
verbose = os.getenv("VAR_VERBOSE", "false").lower() == "true"

# Add Homebrew paths so xbar can find gnuplot
os.environ['PATH'] = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:' + os.environ.get('PATH', '')

# ============================================================================
# GLUCOSE DATA HANDLER CLASS
# ============================================================================

class GlucoseDataHandler:
    """Handles glucose data categorization and formatting."""
    
    def __init__(self, high_threshold: int, low_threshold: int):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
    
    def get_glucose_category(self, value: int) -> str:
        """Categorize glucose value as low, normal, or high."""
        if value < self.low_threshold:
            return "low"
        elif value > self.high_threshold:
            return "high"
        else:
            return "normal"
    
    def get_color_for_category(self, category: str) -> dict:
        """Get color info for glucose category."""
        return COLORS.get(category, COLORS["normal"])
    
    @staticmethod
    def format_time(dt) -> str:
        """Format datetime to readable string."""
        return dt.strftime("%I:%M %p").lstrip("0")

# ============================================================================
# GRAPH GENERATOR CLASS
# ============================================================================

class GraphGenerator:
    """Generate glucose graph using gnuplot."""
    
    def __init__(self, handler: GlucoseDataHandler):
        self.handler = handler
    
    def generate_data_file(self, values: list) -> str:
        """Create temporary data file for gnuplot."""
        import tempfile
        data_content = "\n".join(f"{i} {val}" for i, val in enumerate(values))
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.dat')
        temp_file.write(data_content)
        temp_file.close()
        return temp_file.name
    
    def generate_gnuplot_command(self, data_file: str, output_file: str, values: list) -> str:
        """Generate gnuplot command string."""
        y_min = min(values) - 20 if values else 40
        y_max = max(values) + 20 if values else 180
        
        return f"""
        set term png size 400,150;
        set output '{output_file}';
        set datafile separator " ";
        unset key;
        unset xtics;
        unset ytics;
        set border 0;
        set lmargin 0;
        set rmargin 0.5;
        set tmargin 0.5;
        set bmargin 0.5;
        set yrange [{y_min}:{y_max}];

        plot '{data_file}' using 1:2 with lines lw 2.5 linecolor rgb "#22c55e" notitle;
        """
    
    def generate(self, values: list, output_file: str = '/tmp/dexcom_glucose_plot.png') -> str:
        """
        Generate glucose graph and return base64-encoded image.
        
        Raises:
            RuntimeError: If gnuplot fails
            FileNotFoundError: If gnuplot not installed
        """
        data_file = None
        try:
            data_file = self.generate_data_file(values)
            gnuplot_cmd = self.generate_gnuplot_command(data_file, output_file, values)
            
            result = subprocess.run(['gnuplot', '-e', gnuplot_cmd], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=5)
            
            if result.returncode != 0:
                raise RuntimeError(f"gnuplot error: {result.stderr}")
            
            if not os.path.exists(output_file):
                raise RuntimeError(f"gnuplot did not create output file")
            
            with open(output_file, 'rb') as f:
                img_data = f.read()
                if not img_data:
                    raise RuntimeError("Generated image is empty")
                return base64.b64encode(img_data).decode('utf-8')
        except subprocess.TimeoutExpired:
            raise RuntimeError("gnuplot command timed out")
        finally:
            # Cleanup temp files
            if data_file and os.path.exists(data_file):
                try:
                    os.unlink(data_file)
                except OSError:
                    pass
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except OSError:
                    pass

# ============================================================================
# OUTPUT FORMATTER CLASS
# ============================================================================

class OutputFormatter:
    """Formats xbar menu output for glucose data."""
    
    def __init__(self, handler: GlucoseDataHandler, verbose: bool = False):
        self.handler = handler
        self.verbose = verbose
    
    def format_menu_bar(self, value: int, arrow: str, time_str: str, 
                       img_base64: str = None, category: str = None) -> str:
        """Format the main menu bar text with optional image and color."""
        if category is None:
            category = self.handler.get_glucose_category(value)
        
        color_info = self.handler.get_color_for_category(category)
        menu_text = f"({time_str}) {value} {arrow}"
        
        if img_base64:
            menu_text += f" | image={img_base64} color={color_info['name']}"
        else:
            menu_text += f" | color={color_info['name']}"
        
        return menu_text
    
    def format_verbose_info(self, time_str: str, value: int, arrow: str, 
                           env_region: str, low_threshold: int, high_threshold: int,
                           has_graph: bool) -> str:
        """Format verbose output information."""
        lines = [
            f"Time: {time_str}",
            f"Value: {value}",
            f"Trend: {arrow}",
            f"Region: {env_region}",
            f"Range: {low_threshold}-{high_threshold}",
            f"Graph: {'Generated successfully' if has_graph else 'Failed to generate (gnuplot unavailable or error)'}",
            "---"
        ]
        return "\n".join(lines)
    
    def format_recent_readings(self, readings: list, last_readings_count: int) -> str:
        """Format recent glucose readings."""
        lines = ["Recent Readings:"]
        for r in readings[:last_readings_count]:
            r_time = self.handler.format_time(r.datetime)
            r_value = r.value
            r_arrow = r.trend_arrow
            r_category = self.handler.get_glucose_category(r_value)
            color_info = self.handler.get_color_for_category(r_category)
            lines.append(f"{r_time}: {r_value} {r_arrow} | color={color_info['name']} size=11")
        return "\n".join(lines)
    
    def format_error_message(self, error_msg: str, full_traceback: str = None) -> str:
        """Format error output."""
        lines = ["❌ Error", "---", f"Error fetching glucose data: {error_msg}"]
        if self.verbose and full_traceback:
            lines.extend(["---", full_traceback])
        return "\n".join(lines)

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def fetch_glucose_data(dexcom, handler: GlucoseDataHandler, history_minutes: int, 
                      graph_points: int) -> tuple:
    """
    Fetch current and historical glucose data.
    
    Returns:
        Tuple of (current_reading, readings_list, values_list)
    """
    reading = dexcom.get_current_glucose_reading()
    readings = dexcom.get_glucose_readings(minutes=history_minutes)
    values = [r.value for r in reversed(readings[:graph_points])]
    return reading, readings, values

def attempt_graph_generation(graph_gen: GraphGenerator, values: list, verbose: bool) -> tuple:
    """
    Attempt to generate glucose graph.
    
    Returns:
        Tuple of (img_base64, error_message)
    """
    try:
        img_base64 = graph_gen.generate(values)
        return img_base64, None
    except Exception as e:
        if verbose:
            return None, f"Graph generation failed: {str(e)}"
        return None, None

# ============================================================================
# UPDATE MANAGEMENT FUNCTIONS
# ============================================================================

def check_and_display_updates():
    """Check for available updates and display notification if update exists."""
    if ConfigManager is None:
        return
    
    try:
        config_mgr = ConfigManager(CONFIG_FILE, UPDATE_LOG)
        cfg = config_mgr.load()
        checker = UpdateChecker(cfg.get("version_url", ""), UPDATE_LOG)
        
        if checker.should_check_for_update(cfg.get("last_check_ts", 0), UPDATE_CHECK_INTERVAL):
            # mark check
            cfg["last_check_ts"] = int(datetime.now().timestamp())
            config_mgr.save(cfg)
            available, remote_version = checker.check_for_update(cfg.get("current_version", VERSION))
            if available:
                print(f"Update available: {cfg.get('current_version', VERSION)} → {remote_version} | color=orange")
                print(f"Update now | bash='{sys.executable} {PLUGIN_FILE} update' terminal=false refresh=true")
            else:
                print(f"No updates available | color=gray size=10")
    except Exception as e:
        if verbose:
            print(f"Warning: Update check failed: {str(e)} | color=yellow size=10")

def handle_update_command():
    """Handle update installation when triggered."""
    if ConfigManager is None:
        print("Update system not available")
        return
    
    try:
        config_mgr = ConfigManager(CONFIG_FILE, UPDATE_LOG)
        cfg = config_mgr.load()
        installer = UpdateInstaller(CONFIG_DIR, PLUGINS_DIR, BACKUP_DIR, UPDATE_LOG)
        dep_mgr = DependencyManager(UPDATE_LOG)
        dep_mgr.ensure_dependencies(cfg.get("dependencies", {}))
        print("Installing update from manifest...")
        installer.install_from_manifest(cfg.get("repo", "mattanmr/xbar_plugins"), cfg.get("source_ref", "update_process"), cfg.get("manifest_url", ""))
        cfg["backup_version"] = cfg.get("current_version")
        cfg["current_version"] = VERSION
        cfg["first_run_after_update"] = True
        config_mgr.save(cfg)
        print("Update complete. Refresh xbar to apply.")
    except Exception as e:
        print(f"Update failed: {str(e)}")

def handle_first_run_after_update():
    """Handle first run after successful update."""
    if ConfigManager is None:
        return
    
    try:
        config_mgr = ConfigManager(CONFIG_FILE, UPDATE_LOG)
        if config_mgr.is_first_run_after_update():
            print("Update completed successfully!")
            config_mgr.mark_update_complete()
    except Exception as e:
        if verbose:
            print(f"Warning: Post-update check failed: {str(e)} | color=yellow size=10")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to fetch and display glucose data."""
    try:
        # Initialize components
        handler = GlucoseDataHandler(high_threshold, low_threshold)
        graph_gen = GraphGenerator(handler)
        formatter = OutputFormatter(handler, verbose)
        dexcom = Dexcom(username=username, password=user_password, region=region)
        
        # Fetch data
        reading, readings, values = fetch_glucose_data(dexcom, handler, history_minutes, graph_points)
        value = reading.value
        arrow = reading.trend_arrow
        reading_time = reading.datetime
        
        # Generate graph
        img_base64, graph_warning = attempt_graph_generation(graph_gen, values, verbose)
        if graph_warning and verbose:
            print(f"Warning: {graph_warning}")
        
        # Output menu bar
        time_str = handler.format_time(reading_time)
        category = handler.get_glucose_category(value)
        menu_text = formatter.format_menu_bar(value, arrow, time_str, img_base64, category)
        print(menu_text)
        print("---")
        
        # Verbose output
        if verbose:
            verbose_info = formatter.format_verbose_info(
                time_str, value, arrow, env_region, low_threshold, high_threshold, bool(img_base64)
            )
            print(verbose_info)
        
        # Recent readings
        recent_text = formatter.format_recent_readings(readings, last_readings)
        print(recent_text)
        
        # Graph unavailable notice
        if not img_base64:
            print("---")
            print("Note: Graph unavailable. Ensure gnuplot is installed. | color=purple")
        
        # Update check
        print("---")
        check_and_display_updates()
    
    except Exception as e:
        formatter = OutputFormatter(GlucoseDataHandler(high_threshold, low_threshold), verbose)
        error_output = formatter.format_error_message(
            str(e),
            traceback.format_exc() if verbose else None
        )
        print(error_output)

if __name__ == "__main__":
    # Handle update commands passed as arguments
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "update":
            handle_update_command()
        elif cmd == "first_run_after_update":
            handle_first_run_after_update()
    elif os.getenv("ACKNOWLEDGE_DISCLAIMER", "false").lower() == "true":
        main()
    else:
        print("Please acknowledge the disclaimer by setting ACKNOWLEDGE_DISCLAIMER to true.")
