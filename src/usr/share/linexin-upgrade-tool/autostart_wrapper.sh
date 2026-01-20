#!/bin/bash
# Autostart wrapper for Linexin Upgrade Tool
# Waits for pacman lock to release, then launches the GUI app as the desktop user.

TARGET_USER="$1"
LOG_FILE="/tmp/linexin-autostart.log"

# Redirect all output to log file
exec 1>>"$LOG_FILE" 2>&1

echo "----------------------------------------------------------------"
echo "Starting autostart waiter for user '$TARGET_USER' at $(date)"

if [ -z "$TARGET_USER" ]; then
    echo "Error: Target user not specified."
    exit 1
fi

# Wait for pacman lock to be released
LOCK_FILE="/var/lib/pacman/db.lck"
while [ -f "$LOCK_FILE" ]; do
    echo "Pacman lock found. Waiting..."
    sleep 2
done

echo "Pacman lock released."

# Gather User Details
USER_ID=$(id -u "$TARGET_USER")
USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)

# Setup Environment Variables for GUI Access
export DISPLAY=:0
export XDG_RUNTIME_DIR="/run/user/$USER_ID"

# Set DBus Session Bus Address (Required for systemctl reboot/poweroff commands)
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"

# Attempt to locate XAUTHORITY (for X11/XWayland)
POTENTIAL_AUTHS=(
    "/run/user/$USER_ID/gdm/Xauthority"
    "/run/user/$USER_ID/xauth_*"
    "$USER_HOME/.Xauthority"
)

export XAUTHORITY=""
for auth in "${POTENTIAL_AUTHS[@]}"; do
    # Use glob expansion if wildcards exist
    for f in $auth; do
        if [ -f "$f" ] && [ -r "$f" ]; then
            export XAUTHORITY="$f"
            break 2
        fi
    done
done

# Attempt to locate WAYLAND_DISPLAY (for Wayland)
export WAYLAND_DISPLAY=""
for w in "$XDG_RUNTIME_DIR"/wayland-*; do
    if [ -S "$w" ]; then
        export WAYLAND_DISPLAY=$(basename "$w")
        break
    fi
done

if [ -n "$XAUTHORITY" ]; then
    echo "Using XAUTHORITY=$XAUTHORITY"
else
    echo "Warning: Could not find XAUTHORITY."
fi

if [ -n "$WAYLAND_DISPLAY" ]; then
    echo "Using WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
else
    echo "Warning: No Wayland socket found."
fi

# --- Autorun Logic Check ---
# Only autorun if /version is BEFORE 2026.01.23
VERSION_FILE="/version"
CUTOFF_DATE="20260122"

should_run=true
if [ -f "$VERSION_FILE" ]; then
    # Read version, remove dots to get integer (e.g. 2026.01.23 -> 20260123)
    # Using head -n 1 to ensure we only get the first line
    CURRENT_VERSION=$(cat "$VERSION_FILE" | head -n 1 | tr -d '.')
    
    # Check if conversion resulted in a number
    if [[ "$CURRENT_VERSION" =~ ^[0-9]+$ ]]; then
        if [ "$CURRENT_VERSION" -ge "$CUTOFF_DATE" ]; then
            echo "Version $CURRENT_VERSION is >= $CUTOFF_DATE. Skipping autostart."
            should_run=false
        else
            echo "Version $CURRENT_VERSION is < $CUTOFF_DATE. Proceeding with autostart."
        fi
    else
        echo "Warning: Version file content '$CURRENT_VERSION' is not a valid date format. Proceeding default."
    fi
else
    echo "Warning: $VERSION_FILE not found. Proceeding default."
fi

if [ "$should_run" = false ]; then
    exit 0
fi
# ---------------------------

echo "Launching application..."

# Use exec to replace this shell process with the application.
# Propagate critical environment variables.

exec sudo -u "$TARGET_USER" env \
    DISPLAY="$DISPLAY" \
    XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    XAUTHORITY="$XAUTHORITY" \
    WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
    DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
    /usr/bin/python /usr/share/linexin-upgrade-tool/upgrader

echo "Error: Failed to exec application."
