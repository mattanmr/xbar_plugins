#!/usr/bin/env /usr/local/bin/python3
#
# <xbar.title>Dexcom Glucose Reader</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Mattan Ram</xbar.author>
# <xbar.image>https://raw.githubusercontent.com/mattanmr/xbar_plugins/main/dexcom_reader.png</xbar.image>

# <xbar.var>string(PASSWORD=""): Your dexcom account password </xbar.var>
# <xbar.var>string(ID=""): Your dexcom account id </xbar.var>
# <xbar.var>number(MINUTES=90): amount of history in minutes </xbar.var>
# <xbar.var>number(GRAPH_POINTS=24): amount of points in the graph </xbar.var>
# <xbar.var>select(REGION="outside USA"): Where your Dexcom server is [in USA, outside USA, Japan]</xbar.var>
# <xbar.var>boolean(VAR_VERBOSE=false): Display attributes data?</xbar.var>

import os
from pydexcom import Dexcom
from sparklines import sparklines

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
