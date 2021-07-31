#!/bin/sh
# Create the system process extensions necessary to initialize and execute construction contexts.
# Presumes &system.root.parameters has been sourced.

prefix="$PYTHON_PREFIX"
pylib="python$PYTHON_VERSION$PYTHON_ABI"

compile ()
{
	compiler="$1"; shift 1
	"$compiler" $osflags $CFLAGS "$@"
}

defsys=`uname -s | tr "[:upper:]" "[:lower:]"`
defarch=`uname -m | tr "[:upper:]" "[:lower:]"`

platsuffix="so" # Following platform switch overrides when necessary.

case "$defsys" in
	*darwin*)
		osflags="-Wl,-bundle,-undefined,dynamic_lookup,-lSystem,-L$prefix/lib,-l$pylib -fPIC";
	;;
	*freebsd*)
		osflags="-Wl,-lc,-L$prefix/lib,-l$pylib -fPIC -shared -pthread"
	;;
	*)
		osflags="-Wl,-shared,--export-all-symbols,--export-dynamic,-lc,-lpthread,-L$prefix/lib,-l$pylib -fPIC"
	;;
esac

cd "$FAULT_PYTHON_PATH"
fault_dir="$(pwd)"
container_dir="$(dirname "$fault_dir")"

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
	compile ${CC:-cc} -w -ferror-limit=2 \
		-o "../../$sofile" \
		"-I$FAULT_SYSTEM_PATH/python/include/src" \
		"-I$FAULT_SYSTEM_PATH/machine/include/src" \
		"-I$fault_dir/system/include/src" \
		"-I$prefix/include" \
		"-I$PYTHON_INCLUDE" \
		"-DFV_SYSTEM=$defsys" \
		"-DFV_ARCHITECTURE=$defarch" \
		"-DFV_INTENTION=debug" \
		"-DF_FACTOR_NAME=$modname" \
		"-DF_PROJECT_PATH=$projectfactor" \
		"-DF_FACTOR=$projectfactor.$modname" \
		-fwrapv src/*.c

	mkdir -p "$intdir"
	cp "../../$sofile" "$intdir/$modname.bootstrap.i"
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
