#!/bin/bash
# ==============================================================================
# PortMaster Launch Script for Mustache Protocol
# ==============================================================================

# 1. Environment & PortMaster Setup
XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
elif [ -d "/mnt/sdcard/roms/ports/PortMaster" ]; then
  controlfolder="/mnt/sdcard/roms/ports/PortMaster"
elif [ -d "/mnt/mmc/ports/PortMaster" ]; then
  controlfolder="/mnt/mmc/ports/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

if [ -f "$controlfolder/control.txt" ]; then
  source "$controlfolder/control.txt"
  [ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
  get_controls
fi

# 2. Locate Game Directory
GAMEDIR=""
for dir in \
  "$directory/ports/mustacheprotocol" \
  "/mnt/mmc/ports/mustacheprotocol" \
  "/mnt/sdcard/ports/mustacheprotocol" \
  "/roms/ports/mustacheprotocol" \
  "/userdata/roms/ports/mustacheprotocol" \
  "$(dirname "$0")/mustacheprotocol" \
  "$(cd "$(dirname "$0")/../../ports/mustacheprotocol" 2>/dev/null && pwd)"; do
  if [ -d "$dir" ] && [ -f "$dir/www/index.html" ]; then
    GAMEDIR="$dir"
    break
  fi
done

if [ -z "$GAMEDIR" ]; then
  echo "Error: Mustache Protocol game directory not found!" > "/tmp/mustache_error.log"
  exit 1
fi

cd "$GAMEDIR"

# 3. Locate or Install retsurf Runtime
RUNNER=""
for r in \
  "$GAMEDIR/retsurf" \
  "/mnt/mmc/ports/retsurf/retsurf" \
  "/mnt/sdcard/ports/retsurf/retsurf" \
  "/roms/ports/retsurf/retsurf" \
  "/userdata/roms/ports/retsurf/retsurf" \
  "$controlfolder/../retsurf/retsurf" \
  "$controlfolder/runtimes/retsurf/retsurf" \
  "$(which retsurf 2>/dev/null)"; do
  if [ -x "$r" ]; then
    RUNNER="$r"
    break
  fi
done

# If retsurf is missing, attempt to fetch runtime via HarbourMaster if network is available
if [ -z "$RUNNER" ] && [ -x "$controlfolder/harbourmaster" ]; then
  $ESUDO "$controlfolder/harbourmaster" --runtime "retsurf"
  for r in "$controlfolder/../retsurf/retsurf" "$controlfolder/runtimes/retsurf/retsurf"; do
    if [ -x "$r" ]; then
      RUNNER="$r"
      break
    fi
  done
fi

# 4. Helper: Check if a TCP port is in use
check_port() {
  local p=$1
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$p" >/dev/null 2>&1
    return $?
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', $p)); s.close()" >/dev/null 2>&1
    return $?
  fi
  return 1
}

# 5. Dynamic Port Selection (find an open port starting at 8089)
PORT=8089
MAX_PORT=8100
while check_port "$PORT" && [ "$PORT" -lt "$MAX_PORT" ]; do
  PORT=$((PORT + 1))
done

# 6. Process State & Cleanup Trap
SERVER_PID=""
GPTOKEYB_PID=""

cleanup() {
  echo "[Mustache Protocol] Cleaning up processes..."
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
  fi
  if [ -n "$GPTOKEYB_PID" ]; then
    kill "$GPTOKEYB_PID" 2>/dev/null
    wait "$GPTOKEYB_PID" 2>/dev/null
  fi
  if [ -f "$controlfolder/control.txt" ]; then
    pm_finish
  fi
}
trap cleanup EXIT INT TERM

# 7. Start Local Offline Web Server
if command -v busybox >/dev/null 2>&1 && busybox --list | grep -q "^httpd$"; then
  busybox httpd -p 127.0.0.1:$PORT -h "$GAMEDIR/www" &
  SERVER_PID=$!
elif command -v python3 >/dev/null 2>&1; then
  python3 -m http.server $PORT --bind 127.0.0.1 --directory "$GAMEDIR/www" >/dev/null 2>&1 &
  SERVER_PID=$!
fi

# 8. Active Readiness Verification Loop (Max 5s timeout instead of static sleep)
SERVER_READY=0
for i in $(seq 1 50); do
  if check_port "$PORT"; then
    SERVER_READY=1
    break
  fi
  sleep 0.1
done

if [ "$SERVER_READY" -ne 1 ]; then
  echo "Error: Local HTTP daemon failed to bind to port $PORT within 5 seconds." > "$GAMEDIR/error.log"
  exit 1
fi

# 9. Bind Gamepad via gptokeyb (Track exact PID)
if [ -n "$GPTOKEYB" ] && [ -f "$GAMEDIR/Mustache Protocol.gptk" ]; then
  $GPTOKEYB "retsurf" -c "$GAMEDIR/Mustache Protocol.gptk" &
  GPTOKEYB_PID=$!
fi

# 10. Execute the Game
if [ -n "$RUNNER" ]; then
  "$RUNNER" "http://127.0.0.1:$PORT/index.html"
else
  echo "Error: retsurf runtime not found. Please install retsurf from PortMaster!" > "$GAMEDIR/error.log"
fi
