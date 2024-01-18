# Prepare fault.io/system and fault.io/python for use on the host system.
##

. "$FAULT_ROOT_PATH/tools.sh"

# Bootstrap Python extension modules and connect system.machines to the selected Python.
python.sh

# Overwrite any binaries from a prior integration.
# Dispatch is used by the construction context to build bytecode.
(
	echo "#!/bin/sh"
	echo "exec '$PYTHON'" "'$PYX'" '"$@"'
) >"$FAULT_LIBEXEC_PATH/fault-dispatch"

# Create product index.
f_pdctl -D "$SYSTEM_PRODUCT" delta -U -I "$PYTHON_PRODUCT"
f_pdctl -D "$PYTHON_PRODUCT" delta -U -I "$SYSTEM_PRODUCT"

# Initialize execution platform and construction context for the host.
f_pyx python system.machines.initialize "$FXC"

# Integrate fault.io/python and fault.io/integration using host/cc.
f_pdctl -D "$(dirname "$FAULT_PYTHON_PATH")" -x "$FXC" -X "$FCC" \
	integrate -t "$FAULT_CONTEXT_NAME" "$@"
f_pdctl -D "$(dirname "$FAULT_SYSTEM_PATH")" -x "$FXC" -X "$FCC" \
	integrate -t system "$@"

# Copy host executables.
# Overwrites the script calling factor-execute.py.
(
	tool="$(f_image 'system.machines.python.tool')"
	cp "$tool" "$FAULT_TOOL_PATH/fault-tool"
	cp "$tool" "$FAULT_LIBEXEC_PATH/fault-dispatch"
)
