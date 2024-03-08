# Prepare fault.io/integration and fault.io/python for use on the host system.
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
chmod a+x "$FAULT_LIBEXEC_PATH/fault-dispatch"

# Build project index; ./intregration twice for the generated machines context.
f_fictl query -D "$PYTHON_PRODUCT" -U -I "$SYSTEM_PRODUCT" # For machines/include.
f_fictl query -D "$SYSTEM_PRODUCT" -U -I "$PYTHON_PRODUCT"
f_pyx python system.machines.initialize "$SYSTEMCONTEXT"
f_fictl query -D "$SYSTEM_PRODUCT" -U

f_fictl integrate -L4 -D "$SYSTEMCONTEXT" -X "$SYSTEMCONTEXT" \
	machines

f_fictl integrate -L8 -D "$(dirname "$FAULT_PYTHON_PATH")" -X "$SYSTEMCONTEXT" \
	"$FAULT_CONTEXT_NAME"
f_fictl integrate -L8 -D "$(dirname "$FAULT_SYSTEM_PATH")" -X "$SYSTEMCONTEXT" \
	system

# Copy host executables.
# Overwrites the script calling factor-execute.py.
(
	tool="$(f_image 'machines.python.fault-tool')"
	cp "$tool" "$FAULT_TOOL_PATH/fault-tool"
	cp "$tool" "$FAULT_LIBEXEC_PATH/fault-dispatch"
)
