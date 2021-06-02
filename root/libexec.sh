#!/bin/sh
# Populate the (system/environ)`FAULT_LIBEXEC_PATH` directory with executable bindings.
# Presumes &system.root.parameters has been sourced.

"$PYTHON" "$PYX" .module system.python.bin.bind \
	"-F$FAULT_PYTHON_PATH" \
	"-L$(cd "$FAULT_SYSTEM_PATH/.." && pwd)" \
	"-lfault.context.bin.tools" \
	"-lsystem.context.bin.tools" \
	"$FAULT_LIBEXEC_PATH/pyx" "fault.system.bin.tool" || exit

(cd "$FAULT_LIBEXEC_PATH" || exit
	ln -f pyx http-cache
	ln -f pyx factors-cc
	ln -f pyx compile-python
	ln -f pyx delineate-python
	ln -f pyx pdctl)
