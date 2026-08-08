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

# Detect compiler driver and type.
if test x"$CC" = x""
then
	CC="$(which cc 2>/dev/null || which clang 2>/dev/null || which gcc 2>/dev/null)"
fi

# Detect clang.
(echo "int i=((int)__clang__+1);") | "$CC" -x c -c - -o /dev/null >/dev/null 2>/dev/null
if test $? -eq 0
then
	CDTYPE=llvm-clang
else
	CDTYPE=gnu-cc
fi

# Build project index; ./intregration twice for the generated machines context.
f_fictl query -D "$PYTHON_PRODUCT" -U -I "$SYSTEM_PRODUCT" || exit
f_fictl query -D "$SYSTEM_PRODUCT" -U -I "$PYTHON_PRODUCT" || exit
f_pyx python system.machines.initialize -d"$CC" -t"$CDTYPE" "$SYSTEMCONTEXT" || exit
f_fictl query -D "$SYSTEMCONTEXT" -U -I "$SYSTEM_PRODUCT" || exit
f_fictl query -D "$INTERFACE_PRODUCT" -U -I "$SYSTEM_PRODUCT" || exit

f_fictl integrate -L4 -D "$SYSTEMCONTEXT" -X "$SYSTEMCONTEXT" \
	machines
f_fictl integrate -L1 -D "$(dirname "$FAULT_SYSTEM_PATH")" -X "$SYSTEMCONTEXT" \
	system.intrinsics

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

# Integrate LLVM tooling for instrumentation support; only build when it's not already present.
"$FAULT_TOOL_PATH/fault-tool" python system.machines.llvm -u \
	-X "$SYSTEMCONTEXT" \
	-x "$FAULT_INSTALLATION_PATH/llvm" || \
	echo "NOTE: LLVM integration failed; coverage and delineation tooling (C/C++) will not be available."
