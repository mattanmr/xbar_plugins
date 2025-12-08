#!/usr/bin/python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v2.0</xbar.version>
# <xbar.author>Mattan Ram</xbar.author>
# <xbar.desc>DISCLAIMER: This software is provided "as is" for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Use at your own risk. The authors accept no liability for any consequences of use or misuse.</xbar.desc>
# <xbar.image>https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom_reader.png</xbar.image>
# <xbar.dependencies>gnuplot</xbar.dependencies>

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
from pydexcom import Dexcom

# ============================================================================
# CONSTANTS
# ============================================================================

REGION_MAP = {
    "in USA": "us",
    "outside USA": "ous",
    "Japan": "jp"
}

COLOR_THRESHOLDS = {
    "low": 1,      # Blue
    "normal": 2,   # Green
    "high": 3      # Red
}

COLOR_PALETTE = "1 '#3b82f6', 2 '#22c55e', 3 '#ef4444'"  # Blue, Green, Red
COLOR_NAMES = {
    "low": "blue",
    "normal": "green",
    "high": "red"
}

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
    """Handles glucose data processing, formatting, and visualization."""
    
    def __init__(self, high_threshold: int, low_threshold: int):

        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
    
    def get_glucose_category(self, value: int) -> str:
        if value >= self.high_threshold:
            return "high"
        elif value <= self.low_threshold:
            return "low"
        else:
            return "normal"
    
    def get_glucose_color(self, category: str) -> str:
        return COLOR_NAMES.get(category, "green")
    
    def get_color_code(self, category: str) -> int:
        return COLOR_THRESHOLDS.get(category, 2)
    
    @staticmethod
    def format_time(dt) -> str:
        return dt.strftime('%H:%M') if dt else 'N/A'
    
    def generate_glucose_data_file(self, values: list) -> str:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.dat') as f:
            for i, v in enumerate(values):
                category = self.get_glucose_category(v)
                color_code = self.get_color_code(category)
                f.write(f"{i} {v} {color_code}\n")
            return f.name
    
    def generate_gnuplot_command(self, data_file: str, output_file: str, values: list) -> str:
        min_val = min(values)
        max_val = max(values)
        
        # Add some padding to the y-range for better visualization
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

        set palette defined ({COLOR_PALETTE});
        unset colorbox;

        plot '{data_file}' using 1:2:3 with lines lw 2.5 palette notitle;
        """
    
    def generate_graph(self, values: list, output_file: str = '/tmp/dexcom_glucose_plot.png') -> str:
        """
        Generate glucose graph using gnuplot and return base64-encoded image.
        
        Args:
            values: List of glucose values
            output_file: Path for temporary output PNG
            
        Returns:
            Base64-encoded PNG image data
            
        Raises:
            RuntimeError: If gnuplot fails to generate the graph
            FileNotFoundError: If gnuplot is not installed
            OSError: If file operations fail
        """
        data_file = None
        try:
            data_file = self.generate_glucose_data_file(values)
            gnuplot_cmd = self.generate_gnuplot_command(data_file, output_file, values)
            
            # Run gnuplot - will raise FileNotFoundError if gnuplot not installed
            result = subprocess.run(['gnuplot', '-e', gnuplot_cmd], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=5)  # Add timeout to prevent hanging
            
            if result.returncode != 0:
                raise RuntimeError(f"gnuplot returned error code {result.returncode}: {result.stderr}")
            
            # Verify output file was created
            if not os.path.exists(output_file):
                raise RuntimeError(f"gnuplot did not create output file: {output_file}")
            
            # Read and encode image
            with open(output_file, 'rb') as f:
                img_data = f.read()
                if not img_data:
                    raise RuntimeError("Generated image file is empty")
                return base64.b64encode(img_data).decode('utf-8')
        except subprocess.TimeoutExpired:
            raise RuntimeError("gnuplot command timed out after 5 seconds")
        finally:
            # Clean up temp files - ensure cleanup even if errors occur
            if data_file and os.path.exists(data_file):
                try:
                    os.unlink(data_file)
                except OSError:
                    pass  # Ignore cleanup errors
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except OSError:
                    pass  # Ignore cleanup errors


# ============================================================================
# MAIN FUNCTION
# ============================================================================


def main():
    """Main function to fetch and display glucose data."""
    try:
        # Initialize handler and Dexcom connection
        handler = GlucoseDataHandler(high_threshold, low_threshold)
        dexcom = Dexcom(username=username, password=user_password, region=region)
        
        # Fetch current reading
        reading = dexcom.get_current_glucose_reading()
        value = reading.value
        arrow = reading.trend_arrow
        reading_time = reading.datetime
        
        # Fetch historical readings
        readings = dexcom.get_glucose_readings(minutes=history_minutes)
        values = [r.value for r in reversed(readings[:graph_points])]
        
        # Determine color for current value
        category = handler.get_glucose_category(value)
        current_color = handler.get_glucose_color(category)
        
        # Attempt to generate graph
        img_base64 = None
        try:
            img_base64 = handler.generate_graph(values)
        except Exception as graph_error:
            # If graph generation fails, we can still show the reading
            # Catches: RuntimeError (gnuplot errors), FileNotFoundError (gnuplot not installed),
            # OSError (file operations), and any other graph-related issues
            if verbose:
                print(f"Warning: Graph generation failed: {str(graph_error)}")
            # Continue without image - graceful degradation
        
        # Output menu bar text
        time_str = handler.format_time(reading_time)
        menu_text = f"({time_str}) {value} {arrow}"
        
        if img_base64:
            # Include image if available
            menu_text += f" | image={img_base64} color={current_color}"
        else:
            # Just use color coding if image unavailable
            menu_text += f" | color={current_color}"
        
        print(menu_text)
        print("---")
        
        # Verbose output
        if verbose:
            print(f"Time: {time_str}")
            print(f"Value: {value}")
            print(f"Trend: {arrow}")
            print(f"Region: {env_region}")
            print(f"Range: {low_threshold}-{high_threshold}")
            if img_base64:
                print("Graph: Generated successfully")
            else:
                print("Graph: Failed to generate (gnuplot unavailable or error)")
            print("---")
        
        # Show recent readings in dropdown
        print("Recent Readings:")
        for r in readings[:last_readings]:
            r_time = handler.format_time(r.datetime)
            r_value = r.value
            r_arrow = r.trend_arrow
            r_category = handler.get_glucose_category(r_value)
            r_color = handler.get_glucose_color(r_category)
            
            print(f"{r_time}: {r_value} {r_arrow} | color={r_color} size=11")
    
    except Exception as e:
        # Handle other errors (API, network, credentials, etc.)
        print("❌ Error")
        print("---")
        error_msg = str(e)
        print(f"Error fetching glucose data: {error_msg}")
        if verbose:
            print("---")
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
