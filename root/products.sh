CCONTEXT="$1"; shift 1
(cd "$FAULT_PYTHON_PATH/.." || exit
	pdctl connect "$FAULT_INSTALLATION_PATH/integration"
	pdctl -X "$CCONTEXT" integrate "$FAULT_CONTEXT_NAME" "$@") || exit
(cd "$FAULT_SYSTEM_PATH/.." || exit
	pdctl connect "$FAULT_INSTALLATION_PATH/python"
	pdctl -X "$CCONTEXT" integrate system "$@") || exit

libexec.sh "optimal"
