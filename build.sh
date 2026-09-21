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
chimerax="${CHIMERAX:-ChimeraX}"

"$chimerax" --nogui --exit --cmd "devel build '$bundle' exit true"
echo "Wheel written to: $bundle/dist"
