#!/bin/bash

# Configuration
REPO_URL="https://github.com/mattanmr/xbar_plugins.git"
LOCAL_DIR="$(dirname "$0")"
BRANCH="main"
XBAR_APP_NAME="xbar"

# Function to show a notification (macOS example using terminal-notifier)
notify() {
  local message="$1"
  if command -v terminal-notifier &>/dev/null; then
    terminal-notifier -title "xbar Update" -message "$message"
  else
    osascript -e "display notification \"$message\" with title \"xbar Update\""
  fi
}

# Function to submit error as GitHub issue
submit_issue() {
  local error_log="$1"
  local url="https://github.com/mattanmr/xbar_plugins/issues/new?title=Update%20Error&body=$(python3 -c \"import urllib.parse; print(urllib.parse.quote('Update error:\n\n' + '''$error_log'''))\")"
  open "$url"
}

# Update process
cd "$LOCAL_DIR" || exit 1
git fetch origin "$BRANCH" 2>error.log
if ! git pull origin "$BRANCH" >>error.log 2>&1; then
  ERROR_MSG=$(cat error.log)
  notify "Update failed! Click OK to submit an issue."
  read -p "Submit the error log as a GitHub issue? (y/N): " RESP
  if [[ "$RESP" =~ ^[Yy]$ ]]; then
    submit_issue "$ERROR_MSG"
  fi
  exit 1
fi

# Restart xbar
osascript -e "quit app \"$XBAR_APP_NAME\""
sleep 2
open -a "$XBAR_APP_NAME"

notify "xbar updated and restarted successfully!"

exit 0