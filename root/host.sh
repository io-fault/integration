#!/bin/sh
# Initialize the host execution platform ($1) and factor construction context ($2).
##

. "$FAULT_ROOT_PATH/tools.sh"

HXP="$1"
shift 1
f_pyx system.platforms.bin.initialize "$HXP" || exit
