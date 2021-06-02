# Initialize the host platform.
PLATFORM="$1"; shift 1

pyx system.platforms.bin.initialize "$PLATFORM" || exit
CONTEXT="$PLATFORM/cc/optimal"
export CONTEXT

pyx system.factors.bin.initialize optimal "$CONTEXT" || exit
pyx system.machine.bin.setup CC "$(which cc)" || exit
pyx system.python.bin.setup executable "$FAULT_LIBEXEC_PATH/compile-python" || exit
