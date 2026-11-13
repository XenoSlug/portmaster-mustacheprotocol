#!/bin/bash
# ==============================================================================
# PortMaster Launch Script for Mustache Protocol
# ==============================================================================

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

# Locate the game directory
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

# Locate or install retsurf runtime
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

# If retsurf is missing, attempt to fetch runtime via HarbourMaster if network available
if [ -z "$RUNNER" ] && [ -x "$controlfolder/harbourmaster" ]; then
  $ESUDO "$controlfolder/harbourmaster" --runtime "retsurf"
  for r in "$controlfolder/../retsurf/retsurf" "$controlfolder/runtimes/retsurf/retsurf"; do
    if [ -x "$r" ]; then
      RUNNER="$r"
      break
    fi
  done
fi

# Start local offline web server (bypasses browser CORS module blocks)
PORT=8089
SERVER_PID=""

if command -v busybox >/dev/null 2>&1 && busybox --list | grep -q "^httpd$"; then
  busybox httpd -p 127.0.0.1:$PORT -h "$GAMEDIR/www" &
  SERVER_PID=$!
elif command -v python3 >/dev/null 2>&1; then
  python3 -m http.server $PORT --bind 127.0.0.1 --directory "$GAMEDIR/www" >/dev/null 2>&1 &
  SERVER_PID=$!
fi

sleep 1

# Setup gamepad to keyboard mapping
if [ -n "$GPTOKEYB" ] && [ -f "$GAMEDIR/Mustache Protocol.gptk" ]; then
  $GPTOKEYB "retsurf" -c "$GAMEDIR/Mustache Protocol.gptk" &
fi

# Launch the game
if [ -n "$RUNNER" ]; then
  "$RUNNER" "http://127.0.0.1:$PORT/index.html"
else
  echo "Error: retsurf runtime not found. Please install retsurf from PortMaster!" > "$GAMEDIR/error.log"
fi

# Clean up background services upon exit
[ -n "$SERVER_PID" ] && kill -9 "$SERVER_PID" 2>/dev/null
pkill -f "gptokeyb" 2>/dev/null

if [ -f "$controlfolder/control.txt" ]; then
  pm_finish
fi
