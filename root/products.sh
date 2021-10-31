#!/bin/sh
# Process python and integration factors for use on the host.
##

HXP="$1"
FCC="$2"
shift 2

pdctl -D "$(dirname "$FAULT_PYTHON_PATH")" -x "$HXP" -X "$FCC" \
	integrate "$FAULT_CONTEXT_NAME" "$@" || exit
pdctl -D "$(dirname "$FAULT_SYSTEM_PATH")" -x "$HXP" -X "$FCC" \
	integrate system "$@" || exit

libexec.sh "optimal"
