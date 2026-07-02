#!/bin/bash

# --- Cron Job Environment Setup ---
# Cron runs with a minimal environment. Set necessary variables explicitly.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export HOME="/home/addy"
# Add paths for tools like gcloud. Find the correct path with 'which gcloud' and adjust if needed.
export PATH="/home/addy/google-cloud-sdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PYTHONPATH="$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/cron_$(date +%Y-%m-%d).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Delete log files older than 7 days
find "$LOG_DIR" -name "cron_*.log" -mtime +7 -delete 2>/dev/null || true

echo "----------------------------------------" >> "$LOG_FILE"
echo "[$(date)] Starting YouTube Shorts Automation..." >> "$LOG_FILE"

cd "$SCRIPT_DIR" >> "$LOG_FILE" 2>&1 || { echo "[$(date)] Failed to change directory to $SCRIPT_DIR." >> "$LOG_FILE"; exit 1; }
echo "[$(date)] Changed directory to $(pwd)" >> "$LOG_FILE"

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# No need to source the venv; calling the python executable directly is more reliable in cron.
echo "[$(date)] Using Python from: $VENV_PYTHON" >> "$LOG_FILE"

# The following git commands are for record-keeping.
# Ensure your git user.name and user.email are configured globally.
/usr/bin/git add . >> "$LOG_FILE" 2>&1
echo "[$(date)] Staged changes" >> "$LOG_FILE"
/usr/bin/git commit --allow-empty -m "Automated commit before running script" >> "$LOG_FILE" 2>&1
echo "[$(date)] Committed changes" >> "$LOG_FILE"
/usr/bin/git checkout master >> "$LOG_FILE" 2>&1
echo "[$(date)] Checked out master branch" >> "$LOG_FILE"

"$VENV_PYTHON" "$SCRIPT_DIR/main.py" >> "$LOG_FILE" 2>&1
echo "[$(date)] Ran Python script" >> "$LOG_FILE"

echo "[$(date)] Script execution completed." >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
