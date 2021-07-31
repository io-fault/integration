# Initialize the host platform.
PLATFORM="$1"; shift 1
CCONTEXT="$PLATFORM/cc"

fault-tool python system.platforms.bin.initialize "$PLATFORM" || exit
fault-tool python system.root.cc "$CCONTEXT" || exit
