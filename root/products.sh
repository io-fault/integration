# Process python and integration factors for use on the host.
##
FCC="$1"; shift 1

pdctl -D "$FAULT_PYTHON_PATH/.." -x "$FCC" integrate "$FAULT_CONTEXT_NAME" "$@" || exit
pdctl -D "$FAULT_SYSTEM_PATH/.." -x "$FCC" integrate system "$@" || exit

libexec.sh "optimal"
