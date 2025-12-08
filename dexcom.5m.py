#!/usr/bin/python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v1.1</xbar.version>
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
from pydexcom import Dexcom

region_dict = {
    "in USA": "us",
    "outside USA": "ous",
    "Japan": "jp"
}

# Add Homebrew paths so xbar can find gnuplot
os.environ['PATH'] = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:' + os.environ.get('PATH', '')

# Get environment variables
user_password: str = os.environ.get("PASSWORD")
username: str = os.environ.get("USERNAME")
history_minutes: int = int(os.environ.get("MINUTES"))
graph_points: int = int(os.environ.get("GRAPH_POINTS"))
high_threshold: int = int(os.environ.get("HIGH_THRESHOLD"))
low_threshold: int = int(os.environ.get("LOW_THRESHOLD"))
last_readings: int = int(os.environ.get("LAST_READINGS"))
env_region: str = os.environ.get("REGION")
region: str = region_dict.get(env_region)
verbose: bool = True if os.environ.get("VAR_VERBOSE") == "true" else False

dexcom = Dexcom(username=username, password=user_password, region=region)

try:
    reading = dexcom.get_current_glucose_reading()
    value = reading.value
    arrow = reading.trend_arrow
    reading_time = reading.datetime
    
    readings = dexcom.get_glucose_readings(minutes=history_minutes)
    values = [r.value for r in reversed(readings[:graph_points])]  # limit to points
    
    # Determine current value color
    if value >= high_threshold:
        current_color = "red"
    elif value <= low_threshold:
        current_color = "blue"
    else:
        current_color = "green"

    # Write data with color codes
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.dat') as f:
        for i, v in enumerate(values):
            if v <= low_threshold:
                color_code = 1  # Blue
            elif v >= high_threshold:
                color_code = 3  # Red
            else:
                color_code = 2  # Green
            f.write(f"{i} {v} {color_code}\n")
        data_file = f.name
    
    # Generate plot with gnuplot
    output_file = '/tmp/dexcom_glucose_plot.png'

    min_val = min(values)
    max_val = max(values)
    
    # Add some padding to the y-range
    y_padding = (max_val - min_val) * 0.1
    y_min = max(0, min_val - y_padding)
    y_max = max_val + y_padding
    
    gnuplot_cmd = f"""
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

    set palette defined (1 '#3b82f6', 2 '#22c55e', 3 '#ef4444');
    unset colorbox;

    plot '{data_file}' using 1:2:3 with lines lw 2.5 palette notitle;
    """
    
    # Run gnuplot
    result = subprocess.run(['gnuplot', '-e', gnuplot_cmd], 
                          capture_output=True, 
                          text=True)
    
    if result.returncode != 0:
        raise Exception(f"gnuplot error: {result.stderr}")
    
    # Read and encode image
    with open(output_file, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Clean up temp files
    os.unlink(data_file)
    os.unlink(output_file)
    
    # Output with embedded image
    print(f"({reading_time.strftime('%H:%M') if reading_time else 'N/A'}) {value} {arrow} | image={img_base64} color={current_color}")
    print("---")
    
    if verbose:
        print(f"Last reading: {reading_time.strftime('%H:%M') if reading_time else 'N/A'}")
        print(f"Time: {reading_time.strftime('%H:%M') if reading_time else 'N/A'}")
        print(f"Value: {value}")
        print(f"Trend: {arrow}")
        print(f"Region: {env_region}")
        print(f"Range: {low_threshold}-{high_threshold}")
        print("---")
    
    # Show recent readings in dropdown
    print("Recent Readings:")
    for r in readings[:last_readings]:
        r_time = r.datetime.strftime('%H:%M') if r.datetime else 'N/A'
        r_value = r.value
        r_arrow = r.trend_arrow
        
        if r_value >= high_threshold:
            r_color = "red"
        elif r_value <= low_threshold:
            r_color = "blue"
        else:
            r_color = "green"
        
        print(f"{r_time}: {r_value} {r_arrow} | color={r_color} size=11")

except Exception as e:
    print("❌ Error")
    print("---")
    print(str(e))
