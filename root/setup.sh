#!/bin/sh
# Integrate the fault installation for use on the host system.
rpath () { (cd "$1" && pwd) }
SCRIPT_DIR="$(dirname "$0")"
SCRIPT_DIR="$(rpath "$SCRIPT_DIR")"
FAULT_INSTALLATION="$(rpath "$SCRIPT_DIR"/../../..)"

if test $# -eq 0
then
	python="$(which python3)"
	echo "[!# NOTICE: no python executable designated, using '$python' from PATH.]"
else
	python="$1"; shift 1

	# Installation directory override.
	# Usually unused as the target directory should be identifiable from &SCRIPT_DIR.
	if test $# -gt 0
	then
		FAULT_INSTALLATION="$1"; shift 1
	fi
fi

# Set arguments checked and exported by &system.root.parameters.
set -- "$FAULT_INSTALLATION" "$python"
. "$SCRIPT_DIR/parameters.sh"
cd "$FAULT_INSTALLATION_PATH"

(PATH="$FAULT_TOOL_PATH:$FAULT_LIBEXEC_PATH:$FAULT_ROOT_PATH:$PATH"
	. "$SCRIPT_DIR/integrate.sh")
