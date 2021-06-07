# Initialize the host platform.
PLATFORM="$1"; shift 1
CCONTEXT="$PLATFORM/cc/optimal"

fault-tool python system.platforms.bin.initialize "$PLATFORM" || exit
fault-tool python system.factors.bin.initialize optimal "$CCONTEXT" || exit
fault-tool python system.machine.bin.setup "$CCONTEXT" CC "$(which cc)" || exit
fault-tool python system.python.bin.setup "$CCONTEXT" || exit
