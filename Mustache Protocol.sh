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

# Locate Game Directory
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

[ -z "$GAMEDIR" ] && GAMEDIR="$(cd "$(dirname "$0")/mustacheprotocol" 2>/dev/null && pwd)"

cd "$GAMEDIR"

# Redirect stdout and stderr to log.txt for full debugging
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1
echo "=== Starting Mustache Protocol ==="
echo "Working directory: $GAMEDIR"

# Auto-copy boxart & preview to muOS catalogue if running on muOS
for cat_dir in "/mnt/mmc/MUOS/info/catalogue" "/mnt/sdcard/MUOS/info/catalogue"; do
  if [ -d "$cat_dir" ]; then
    for pdir in "Ports" "PORTS" "ports"; do
      mkdir -p "$cat_dir/$pdir/box" "$cat_dir/$pdir/preview" 2>/dev/null
      [ -f "$GAMEDIR/cover.png" ] && cp -f "$GAMEDIR/cover.png" "$cat_dir/$pdir/box/Mustache Protocol.png" 2>/dev/null
      [ -f "$GAMEDIR/screenshot.png" ] && cp -f "$GAMEDIR/screenshot.png" "$cat_dir/$pdir/preview/Mustache Protocol.png" 2>/dev/null
    done
  fi
done

$ESUDO chmod +x "$GAMEDIR"/retsurf* 2>/dev/null || true

# Locate retsurf Engine
CPU_PART="$(grep -m1 -i 'CPU part' /proc/cpuinfo 2>/dev/null | grep -oiE '0x[0-9a-f]+' | head -1 | tr 'A-Z' 'a-z')"
select_binary() {
  case "$CPU_PART" in
    0xd05) grep -qw atomics /proc/cpuinfo 2>/dev/null && echo "retsurf.a55" || echo "retsurf.a53" ;;
    0xd04) echo "retsurf.a35" ;;
    *)     echo "retsurf.a53" ;;
  esac
}

BINNAME="$(select_binary)"
RUNNER=""

if [ -f "$GAMEDIR/$BINNAME" ]; then
  RUNNER="$GAMEDIR/$BINNAME"
elif [ -f "$GAMEDIR/retsurf.a53" ]; then
  RUNNER="$GAMEDIR/retsurf.a53"
  BINNAME="retsurf.a53"
elif [ -f "$GAMEDIR/retsurf.a55" ]; then
  RUNNER="$GAMEDIR/retsurf.a55"
  BINNAME="retsurf.a55"
elif [ -f "$GAMEDIR/retsurf.a35" ]; then
  RUNNER="$GAMEDIR/retsurf.a35"
  BINNAME="retsurf.a35"
elif [ -f "$GAMEDIR/retsurf" ]; then
  RUNNER="$GAMEDIR/retsurf"
  BINNAME="retsurf"
fi

if [ -z "$RUNNER" ]; then
  for r in \
    "$controlfolder/../retsurf/retsurf" \
    "$controlfolder/../retsurf/$BINNAME" \
    "/roms/ports/retsurf/retsurf" \
    "/mnt/mmc/ports/retsurf/retsurf" \
    "/mnt/sdcard/ports/retsurf/retsurf" \
    "/userdata/roms/ports/retsurf/retsurf" \
    "$(which retsurf 2>/dev/null)"; do
    if [ -x "$r" ]; then
      RUNNER="$r"
      break
    fi
  done
fi

if [ -z "$RUNNER" ] || [ ! -f "$RUNNER" ]; then
  echo "Error: retsurf engine not found in $GAMEDIR or system ports."
  pm_message "retsurf runtime missing!"
  sleep 5
  exit 1
fi

echo "Selected engine: $RUNNER ($BINNAME)"

# Setup Library Paths
if [ -d "$GAMEDIR/libs" ]; then
  export LD_LIBRARY_PATH="$GAMEDIR/libs:$LD_LIBRARY_PATH"
fi

# fontconfig configuration
fonts_in="$GAMEDIR/etc/fonts/fonts.conf.in"
fonts_conf="$GAMEDIR/data/fonts.conf"
if [ ! -f /etc/fonts/fonts.conf ] && [ -f "$fonts_in" ]; then
  if [ ! -s "$fonts_conf" ] || [ "$fonts_in" -nt "$fonts_conf" ] || ! grep -q "$GAMEDIR" "$fonts_conf"; then
    mkdir -p "$GAMEDIR/data"
    sed "s|@GAMEDIR@|$GAMEDIR|g" "$fonts_in" > "$fonts_conf"
  fi
  export FONTCONFIG_FILE="$fonts_conf"
fi

export HOME="$GAMEDIR"
export XDG_DATA_HOME="$GAMEDIR"
export RETSURF_DATA_DIR="$GAMEDIR/data"
export RETSURF_DOWNLOAD_DIR="$GAMEDIR/downloads"
export RETSURF_PANIC_FILE="$GAMEDIR/retsurf-panic.log"
export RETSURF_LOG_FILE="$GAMEDIR/retsurf.log"
export RETSURF_LOG_LEVEL=info
export SDL_GAMECONTROLLERCONFIG="${RETSURF_GAMECONTROLLERCONFIG:-$sdl_controllerconfig}"

GPTOKEYB_PID=""
cleanup() {
  echo "[Mustache Protocol] Cleaning up..."
  if [ -n "$GPTOKEYB_PID" ]; then
    kill "$GPTOKEYB_PID" 2>/dev/null
    wait "$GPTOKEYB_PID" 2>/dev/null
  fi
  if [ -f "$controlfolder/control.txt" ]; then
    pm_finish
  fi
}
trap cleanup EXIT INT TERM

# Bind gamepad via gptokeyb
if [ -n "$GPTOKEYB" ] && [ -f "$GAMEDIR/Mustache Protocol.gptk" ]; then
  $GPTOKEYB "$BINNAME" -c "$GAMEDIR/Mustache Protocol.gptk" &
  GPTOKEYB_PID=$!
fi

# Setup platform environment (SDL2 rotation, display driver, etc.)
if command -v pm_platform_helper >/dev/null 2>&1; then
  pm_platform_helper "$RUNNER"
fi

# Launch Game in retsurf Game Mode
echo "Launching retsurf in game mode with folder: $GAMEDIR/www"
"$RUNNER" --game-mode "$GAMEDIR/www"
