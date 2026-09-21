#!/bin/sh
# Build a redistributable wheel of the ChimeraX-Vinardock bundle.
#
# Requires ChimeraX (https://www.rbvi.ucsf.edu/chimerax/download.html).
# Usage:
#   ./build.sh
#   CHIMERAX=/path/to/ChimeraX ./build.sh
#
# The wheel is written to src/bundles/vinardock/dist and can be uploaded to the
# ChimeraX Toolshed (https://cxtoolshed.rbvi.ucsf.edu) or installed with
# "toolshed install <wheel>".

set -e

here=$(cd "$(dirname "$0")" && pwd)
bundle="$here/src/bundles/vinardock"

if [ -n "$CHIMERAX" ]; then
    chimerax="$CHIMERAX"
elif command -v chimerax >/dev/null 2>&1; then
    chimerax=chimerax
elif command -v ChimeraX >/dev/null 2>&1; then
    chimerax=ChimeraX
else
    chimerax=""
fi

if [ -z "$chimerax" ] || { ! command -v "$chimerax" >/dev/null 2>&1 && [ ! -x "$chimerax" ]; }; then
    echo "ChimeraX executable not found (tried: \$CHIMERAX, chimerax, ChimeraX)." >&2
    echo "Install ChimeraX from https://www.rbvi.ucsf.edu/chimerax/download.html" >&2
    exit 1
fi

"$chimerax" --nogui --exit --cmd "devel build '$bundle' exit true"
echo "Wheel written to: $bundle/dist"
