#!/bin/sh
# Build and install the ChimeraX-Vinardock bundle into an existing ChimeraX.
#
# ChimeraX is NOT included with this bundle; install it from
# https://www.rbvi.ucsf.edu/chimerax/download.html first.
#
# Usage:
#   ./install.sh
#   CHIMERAX=/path/to/ChimeraX ./install.sh

set -e

here=$(cd "$(dirname "$0")" && pwd)
bundle="$here/src/bundles/vinardock"
chimerax="${CHIMERAX:-ChimeraX}"

if ! command -v "$chimerax" >/dev/null 2>&1 && [ ! -x "$chimerax" ]; then
    echo "ChimeraX executable not found: $chimerax" >&2
    echo "Install ChimeraX from https://www.rbvi.ucsf.edu/chimerax/download.html" >&2
    echo "or set CHIMERAX to its path, e.g. CHIMERAX=/opt/ChimeraX/bin/ChimeraX ./install.sh" >&2
    exit 1
fi

echo "Installing $bundle into: $chimerax"
"$chimerax" --nogui --exit --cmd "devel install '$bundle' exit true"
echo "Done. Restart ChimeraX to load the bundle."
