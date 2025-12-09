#!/usr/bin/python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v2.0</xbar.version>
# <xbar.author>Mattan Ram</xbar.author>
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
import subprocess
import tempfile
import base64
import traceback
import math
from pydexcom import Dexcom

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

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
# UTILITY FUNCTIONS
# ============================================================================

def generate_test_glucose_values(points: int = 24):
    """Generate test glucose values using a sine wave pattern."""
    for i in range(points):
        angle = (i / points) * 2 * math.pi
        value = int(100 + 50 * math.sin(angle))
        yield value

# Add Homebrew paths so xbar can find gnuplot
os.environ['PATH'] = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:' + os.environ.get('PATH', '')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get environment variables
user_password: str = os.environ.get("PASSWORD", "")
username: str = os.environ.get("USERNAME", "")
history_minutes: int = int(os.environ.get("MINUTES", 90))
graph_points: int = int(os.environ.get("GRAPH_POINTS", 24))
high_threshold: int = int(os.environ.get("HIGH_THRESHOLD", 130))
low_threshold: int = int(os.environ.get("LOW_THRESHOLD", 75))
last_readings: int = int(os.environ.get("LAST_READINGS", 4))
env_region: str = os.environ.get("REGION", "outside USA")
region: str = REGION_MAP.get(env_region, "ous")
verbose: bool = os.environ.get("VAR_VERBOSE", "false").lower() == "true"

# ============================================================================
# GLUCOSE DATA HANDLER CLASS
# ============================================================================


class GlucoseDataHandler:
    """Handles glucose data processing and categorization."""
    
    def __init__(self, high_threshold: int, low_threshold: int):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
    
    def get_glucose_category(self, value: int) -> str:
        """Categorize glucose value as low, normal, or high."""
        if value >= self.high_threshold:
            return "high"
        elif value <= self.low_threshold:
            return "low"
        else:
            return "normal"
    
    def get_color_for_category(self, category: str) -> dict:
        """Get color info (hex and name) for a glucose category."""
        return COLORS.get(category, COLORS["normal"])
    
    @staticmethod
    def format_time(dt) -> str:
        """Format datetime to HH:MM string."""
        return dt.strftime('%H:%M') if dt else 'N/A'


# ============================================================================
# GRAPH GENERATION CLASS
# ============================================================================


class GraphGenerator:
    """Handles glucose graph generation using gnuplot."""
    
    def __init__(self, handler: GlucoseDataHandler):
        self.handler = handler
    
    def generate_data_file(self, values: list) -> str:
        """Create temporary data file with glucose values and colors."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.dat') as f:
            for i, v in enumerate(values):
                category = self.handler.get_glucose_category(v)
                color_hex = self.handler.get_color_for_category(category)["hex"]
                f.write(f"{i} {v} {color_hex}\n")
            return f.name
    
    def generate_gnuplot_command(self, data_file: str, output_file: str, values: list) -> str:
        """Generate gnuplot script for glucose graph."""
        min_val = min(values)
        max_val = max(values)
        
        # Add padding for better visualization
        y_padding = (max_val - min_val) * 0.1 if max_val > min_val else 10
        y_min = max(0, min_val - y_padding)
        y_max = max_val + y_padding
        
        return f"""
        set terminal pngcairo size 80,40 transparent;
        set output '{output_file}';
        unset title;
        unset xlabel;
        unset ylabel;
        unset key;
        unset xtics;
        unset ytics;
        set border 0;
        set lmargin 0;
        set rmargin 0.5;
        set tmargin 0.5;
        set bmargin 0.5;
        set yrange [{y_min}:{y_max}];

        plot '{data_file}' using 1:2:3 with lines lw 2.5 linecolor rgb variable notitle;
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
        Tuple of (current_reading, values_list)
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
    
    except Exception as e:
        formatter = OutputFormatter(GlucoseDataHandler(high_threshold, low_threshold), verbose)
        error_output = formatter.format_error_message(
            str(e),
            traceback.format_exc() if verbose else None
        )
        print(error_output)


if __name__ == "__main__":
    
    if os.getenv("ACKNOWLEDGE_DISCLAIMER", "false").lower() == "true":
        main()
    else:
        print("Please acknowledge the disclaimer by setting ACKNOWLEDGE_DISCLAIMER to true.")