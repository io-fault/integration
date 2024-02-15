#!/bin/sh
# Create the system process extensions necessary to initialize and execute construction contexts.
# Presumes &system.root.parameters has been sourced.
##

cd "$FAULT_PYTHON_PATH"
fault_dir="$(pwd)"
container_dir="$(dirname "$fault_dir")"

# Prefer connecting with a symbolic link rather than -I so that
# &(fictl integrate) can function without additional configuration.
rm -f "$FAULT_SYSTEM_PATH/machines/include/fault/python/implementation"
ln -sf "$PYTHON_INCLUDE" "$FAULT_SYSTEM_PATH/machines/include/fault/python/implementation"

BINDH="$FAULT_SYSTEM_PATH/machines/include/fault/python/bind.h"
echo >"$BINDH" '/* Python and fault locations for binding executable (factor) modules. */'
echo >>"$BINDH" '#define PYTHON_EXECUTABLE_PATH "'"$PYTHON"'"'
echo >>"$BINDH" '#define FAULT_PYTHON_IMPLEMENTATION 1'
echo >>"$BINDH" '#define FAULT_PYTHON_PRODUCT "'"$container_dir"'"'
echo >>"$BINDH" '#define FAULT_CONTEXT_NAME "'"$(basename "$fault_dir")"'"'

prefix="$PYTHON_PREFIX"
pylib="python$PYTHON_VERSION$PYTHON_ABI"

# Configure library reference binding executable modules.
PYMACHINESR="$FAULT_SYSTEM_PATH/machines/python/runtime.sr"
echo >"$PYMACHINESR" "$prefix/lib"'//library'
echo >>"$PYMACHINESR" "$pylib"

compile ()
{
	compiler="$1"; shift 1
	"$compiler" -fPIC -x c -std=iso9899:2011 $osflags $CFLAGS "$@"
}

defsys=`uname -s | tr "[:upper:]" "[:lower:]"`
defarch=`uname -m | tr "[:upper:]" "[:lower:]"`

platsuffix="so" # Following platform switch overrides when necessary.

case "$defsys" in
	*darwin*)
		osflags="-Wl,-bundle,-undefined,dynamic_lookup,-lSystem,-L$prefix/lib,-l$pylib"
	;;
	*freebsd*)
		osflags="-shared -Wl,-lc,-L$prefix/lib,-l$pylib -pthread"
	;;
	*)
		osflags="-shared -Wl,--unresolved-symbols=ignore-all,--export-dynamic"
	;;
esac

module_path ()
{
	local dirpath relpath
	dirpath="$1"
	shift 1

	relpath="$(echo "$dirpath" | sed "s:${container_dir}::")"
	echo "$relpath" | sed 's:/:.:g' | sed 's:.::'
}

bootstrap_extension ()
{
	cd "$1" || return
	local extension_path modname pkgname
	local fullname package projectfactor targetname

	extension_path="$(pwd)"
	modname="${extension_path##*/}"

	fullname="$(module_path "$extension_path")"
	package="$(cd ..; module_path "$(pwd)")"
	projectfactor="$(cd ../..; module_path "$(pwd)")"
	targetname="$(echo "$fullname" | sed 's/.extensions//')"
	pkgname="$(echo "$fullname" | sed 's/[.][^.]*$//')"

	: "$(pwd)"
	sofile="${modname}.${platsuffix}"
	intdir="../../extensions/__f-int__/$defsys-$defarch/"
	compile ${CC:-cc} -w \
		-o "../../$sofile" \
		"-I$FAULT_SYSTEM_PATH/machines/include" \
		"-I$fault_dir/system/include" \
		"-I$prefix/include" \
		\
		"-D_DEFAULT_SOURCE" \
		\
		'-DF_PRODUCT_PATH="'"$container_dir"'"' \
		"-DFV_SYSTEM=$defsys" \
		"-DFV_ARCHITECTURE=$defarch" \
		"-DFV_INTENTION=debug" \
		\
		"-DF_FACTOR_NAME=$modname" \
		"-DF_PROJECT_PATH=$projectfactor" \
		"-DF_FACTOR=$projectfactor.$modname" \
		-fwrapv ./*.c

	mkdir -p "$intdir/bootstrap"
	cp "../../$sofile" "$intdir/bootstrap/$modname.i"
}

bootstrap_project ()
{
	cd "$1"
	root="$(dirname "$(pwd)")"

	# Nothing to do?
	test -d ./extensions || return 0

	for module in ./extensions/*/
	do
		iscache="$(echo "$module" | grep '__pycache__\|__f-cache__\|__f-int__')"
		if ! test x"$iscache" = x""
		then
			continue
		fi

		(bootstrap_extension "$module")
	done
}

(bootstrap_project "$fault_dir/system")
