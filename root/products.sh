CCONTEXT="$1"; shift 1
(cd "$FAULT_PYTHON_PATH/.." || exit
	pdctl index
	pdctl -X "$CCONTEXT" integrate "$FAULT_CONTEXT_NAME")
(cd "$FAULT_SYSTEM_PATH/.." || exit
	pdctl index
	pdctl -X "$CCONTEXT" integrate system)
