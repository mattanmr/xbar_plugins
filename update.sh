#!/bin/bash
# Dexcom xbar Plugin Updater
# This script updates the plugin by pulling the latest changes from the main branch and running install.sh if present.

set -e
set -x

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "Checking for updates from main branch..."
git fetch origin main
git reset --hard origin/main

echo "Update complete. Running install.sh if present..."
if [ -f install.sh ]; then
    bash install.sh
else
    echo "install.sh not found. Update finished."
fi
