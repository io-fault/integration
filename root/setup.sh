#!/bin/sh
# Integrate the fault installation for use on the host system.
rpath () { (cd "$1" && pwd) }
SCRIPT_DIR="$(dirname "$0")"
SCRIPT_DIR="$(rpath "$SCRIPT_DIR")"

if test $# -eq 0
then
	python="$(which python3)"
	echo "[!# STATUS: no python executable designated, using '$python' selected by &which.]"
else
	python="$1"; shift 1
fi

FAULT_INSTALLATION="$(rpath "$SCRIPT_DIR"/../../..)"
export FAULT_INSTALLATION
cd "$FAULT_INSTALLATION" || exit
mkdir -p 'libexec' || exit

test -d 'libexec' || ! echo "[!# ERROR: no 'libexec' tool directory present.]" || exit
test -d 'integration' || ! echo "[!# ERROR: no 'integration' product directory present.]" || exit
test -d 'python' || ! echo "[!# ERROR: no 'python' product directory present.]" || exit

# Set arguments checked and exported by &system.root.parameters.
set -- \
	"$FAULT_INSTALLATION/python/fault" \
	"$FAULT_INSTALLATION/integration/system" \
	"$FAULT_INSTALLATION/libexec" \
	"$python"
. "$SCRIPT_DIR/parameters.sh"

(PATH="$FAULT_LIBEXEC_PATH:$FAULT_ROOT_PATH:$PATH"
	. "$SCRIPT_DIR/integrate.sh")
