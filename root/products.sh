CCONTEXT="$1"; shift 1
(cd "$FAULT_PYTHON_PATH/.." || exit
	pdctl connect "$FAULT_INSTALLATION_PATH/integration"
	pdctl -x "$CCONTEXT" integrate -u "$FAULT_CONTEXT_NAME" "$@") || exit
(cd "$FAULT_SYSTEM_PATH/.." || exit
	pdctl connect "$FAULT_INSTALLATION_PATH/python"
	pdctl -x "$CCONTEXT" integrate -u system "$@") || exit

libexec.sh "optimal"
