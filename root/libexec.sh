#!/bin/sh
# Populate (system/environ)`FAULT_LIBEXEC_PATH` and (system/environ)`FAULT_TOOL_PATH` directories
# with executable bindings. Presumes &system.root.parameters has been sourced.
##

. "$FAULT_ROOT_PATH/tools.sh"
INTENTION="${1-:optimal}"; shift 1

f_bind -i$INTENTION \
	"$FAULT_TOOL_PATH/pdctl" "system.products.bin.control" || exit

f_bind -i$INTENTION \
	"-lfault.context.execute" \
	"-lsystem.context.execute" \
	"$FAULT_TOOL_PATH/fault-tool" "fault.system.tool" || exit

f_bind -i$INTENTION \
	"-lfault.context.execute" \
	"-lsystem.context.execute" \
	"$FAULT_LIBEXEC_PATH/fault-dispatch" "fault.system.tool" || exit
