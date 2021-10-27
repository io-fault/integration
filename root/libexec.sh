#!/bin/sh
# Populate (system/environ)`FAULT_LIBEXEC_PATH` and (system/environ)`FAULT_TOOL_PATH` directories
# with executable bindings. Presumes &system.root.parameters has been sourced.
##
. "$FAULT_ROOT_PATH/tools.sh"
INTENTION="${1-:optimal}"; shift 1

f_bind -i$INTENTION \
	"-F$FAULT_PYTHON_PATH" "-L$SYSTEM_PRODUCT" \
	"$FAULT_TOOL_PATH/pdctl" "system.products.bin.control" || exit

f_bind -i$INTENTION \
	"-F$FAULT_PYTHON_PATH" "-L$SYSTEM_PRODUCT" \
	"-lfault.context.bin.tools" \
	"-lsystem.context.bin.tools" \
	"$FAULT_TOOL_PATH/fault-tool" "fault.system.bin.tool" || exit

f_bind -i$INTENTION \
	"-F$FAULT_PYTHON_PATH" "-L$SYSTEM_PRODUCT" \
	"-lfault.context.bin.tools" \
	"-lsystem.context.bin.tools" \
	"$FAULT_LIBEXEC_PATH/fault-dispatch" "fault.system.bin.tool" || exit
