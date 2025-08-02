#!/usr/bin/python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Mattan Ram</xbar.author>
# <xbar.desc>DISCLAIMER: This software is provided "as is" for informational and convenience purposes only. It is not intended to replace professional medical advice, diagnosis, or counseling. Use at your own risk. The authors accept no liability for any consequences of use or misuse.</xbar.desc>
# <xbar.image>https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom_reader.png</xbar.image>
# <xbar.plugin_version>1.0.0</xbar.plugin_version>
# <xbar.version_file>VERSION</xbar.version_file>

# <xbar.var>string(PASSWORD=""): Your dexcom account password </xbar.var>
# <xbar.var>string(ID=""): Your dexcom account id </xbar.var>
# <xbar.var>number(MINUTES=90): amount of history in minutes </xbar.var>
# <xbar.var>number(GRAPH_POINTS=24): amount of points in the graph </xbar.var>
# <xbar.var>select(REGION="outside USA"): Where your Dexcom server is [in USA, outside USA, Japan]</xbar.var>
# <xbar.var>boolean(VAR_VERBOSE=false): Display attributes data?</xbar.var>

# DISCLAIMER:
# This software is provided "as is" for informational and convenience purposes only.
# It is not intended to replace professional medical advice, diagnosis, or counseling.
# Use at your own risk. The authors accept no liability for any consequences of use or misuse.

import os
from pydexcom import Dexcom
from sparklines import sparklines
import urllib.request
import subprocess

region_dict = {
    "in USA": "us",
    "outside USA": "ous",
    "Japan": "jp"
    }

# Get environment variables
user_password: str = os.environ.get("PASSWORD")
account_id: str = os.environ.get("ID")
history_minutes: int = int(os.environ.get("MINUTES"))
graph_points: int = int(os.environ.get("GRAPH_POINTS"))
env_region: str = os.environ.get("REGION")
region: str = region_dict.get(env_region)
verbose: bool = True if os.environ.get("VAR_VERBOSE") == "true" else False

dexcom = Dexcom(account_id=account_id, password=user_password, region=region)

PLUGIN_VERSION = "1.0.0"
VERSION_FILE = os.path.join(os.path.dirname(__file__), "VERSION")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/VERSION"
UPDATE_SCRIPT = os.path.join(os.path.dirname(__file__), "update.sh")

# Check for updates
try:
    with open(VERSION_FILE) as f:
        local_version = f.read().strip()
except Exception:
    local_version = PLUGIN_VERSION

try:
    remote_version = urllib.request.urlopen(REMOTE_VERSION_URL).read().decode("utf-8").strip()
except Exception:
    remote_version = local_version

if remote_version != local_version:
    print(f"Update Available: {remote_version}")
    print(f"--Update Plugin | bash='{UPDATE_SCRIPT}' terminal=false refresh=true")
    print("---")

try:
    reading = dexcom.get_current_glucose_reading()
    value = reading.value
    arrow = reading.trend_arrow
    reading_time = reading.datetime
    
    readings = dexcom.get_glucose_readings(minutes=history_minutes)
    values = [r.value for r in reversed(readings[:graph_points])] # limit to points
    graph = sparklines(values)[0]

    print(f"({reading_time.strftime('%H:%M') if reading_time else 'N/A'}) {value} {arrow}")
    print("---")
    
    if verbose:
        print(f"Last reading: {reading_time.strftime('%H:%M') if reading_time else 'N/A'}")
        print(f"Verbose: {verbose}")
        print(f"Region: {env_region}")
    print(graph)

except Exception as e:
    print("❌ Error")
    print("---")
    print(str(e))
