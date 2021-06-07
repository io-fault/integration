#!/bin/sh
# Integrate the fault installation for use on the host system.
#
# [ Parameters ]
#
# /PYTHON/
	# Absolute path to the python executable to build against.
	# By default, (system/environ)`PATH` is scanned for (system/command)`python3`.
# /FAULT_INSTALLATION/
	# Optional. Path to the fault installation directory.
	# Normally this identified relatively from &.setup.

rpath () { (cd "$1" && pwd) }
SCRIPT_DIRNAME="$(dirname "$0")"
SCRIPT_DIR="$(rpath "$SCRIPT_DIRNAME")"
FAULT_INSTALLATION="$(rpath "$SCRIPT_DIR"/../../..)"

python="$("${1:-python3}" -c 'import sys; print(sys.executable)')"
if test $# -eq 0
then
	echo "[!# NOTICE: python executable not explicitly designated, using from 'python3' from PATH.]"
else
	shift 1; # python executable

	# Installation directory override.
	# Usually unused as the target directory should be identifiable from &SCRIPT_DIR.
	if test $# -gt 0
	then
		FAULT_INSTALLATION="$1"; shift 1
	fi
fi

echo "[!= PYTHON: '$python' '$("$python" -c 'import sys; print(sys.prefix)')']"

# Set arguments checked and exported by &system.root.parameters.
set -- "$FAULT_INSTALLATION" "$python"
. "$SCRIPT_DIR/parameters.sh"
cd "$FAULT_INSTALLATION_PATH"

(PATH="$FAULT_TOOL_PATH:$FAULT_LIBEXEC_PATH:$FAULT_ROOT_PATH:$PATH"
	. "$SCRIPT_DIR/integrate.sh")
