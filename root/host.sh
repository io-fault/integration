# Initialize the host execution platform ($1) and factor construction context ($2).
. "$FAULT_ROOT_PATH/tools.sh"
f_pyx system.platforms.bin.initialize "$1" || exit
f_pyx system.root.cc "$2" || exit
