#!/bin/bash

# --- Cron Job Environment Setup ---
# Cron runs with a minimal environment. Set necessary variables explicitly.
export HOME="/home/addy"
# Add paths for tools like gcloud. Find the correct path with 'which gcloud' and adjust if needed.
export PATH="/home/addy/google-cloud-sdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PYTHONPATH="/home/addy/projects/youtube-shorts-automation"

LOG_DIR="/home/addy/projects/youtube-shorts-automation/logs"
LOG_FILE="$LOG_DIR/cron_$(date +%Y-%m-%d).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Delete log files older than 7 days
find "$LOG_DIR" -name "cron_*.log" -mtime +7 -delete

echo "----------------------------------------" >> "$LOG_FILE"
echo "[$(date)] Starting YouTube Shorts Automation..." >> "$LOG_FILE"

PROJECT_DIR="/home/addy/projects/youtube-shorts-automation"

cd "$PROJECT_DIR" >> "$LOG_FILE" 2>&1 || { echo "[$(date)] Failed to change directory to $PROJECT_DIR." >> "$LOG_FILE"; exit 1; }
echo "[$(date)] Changed directory to $(pwd)" >> "$LOG_FILE"

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

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

# The Python script seems to handle authentication via GOOGLE_APPLICATION_CREDENTIALS.
# This gcloud command may be unnecessary and could fail in a non-interactive session.
# I recommend commenting it out.
# gcloud config set account adhbutg@gmail.com >> "$LOG_FILE" 2>&1
# echo "[$(date)] Set gcloud account" >> "$LOG_FILE"

"$VENV_PYTHON" "$PROJECT_DIR/main.py" >> "$LOG_FILE" 2>&1
echo "[$(date)] Ran Python script" >> "$LOG_FILE"

echo "[$(date)] Script execution completed." >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
