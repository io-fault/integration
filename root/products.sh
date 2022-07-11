#!/bin/sh
# Process python and integration factors for use on the host.
##

FXC="$1"
FCC="$2"
shift 2

pdctl -D "$(dirname "$FAULT_PYTHON_PATH")" -x "$FXC" -X "$FCC" \
	integrate "$FAULT_CONTEXT_NAME" "$@" || exit
pdctl -D "$(dirname "$FAULT_SYSTEM_PATH")" -x "$FXC" -X "$FCC" \
	integrate system "$@" || exit

libexec.sh "optimal"
