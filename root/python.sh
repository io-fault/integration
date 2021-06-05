#!/bin/sh
# Create the system process extensions necessary to initialize and execute construction contexts.
# Presumes &system.root.parameters has been sourced.
SCD=`pwd`
if readlink "$PYTHON"
then
	cd "$(dirname "$PYTHON")"
	pylink="$(readlink "$PYTHON")"
	cd "$(dirname "$pylink")"
	cd ..
	prefix="$(pwd)"
else
	prefix="$(dirname "$(dirname "$PYTHON")")"
fi
cd "$SCD"
unset SCD

evalpy () { "$PYTHON" -c "$1"; }
pyversion="$(evalpy 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
pyabi="$(evalpy 'import sys; print(sys.abiflags)')"
pytype="$(evalpy 'import sys; print(sys.implementation.name)')"

test $? -eq 0 || exit 1

echo "ABI: $pyabi"
echo "VERSION: $pyversion"
echo "TYPE: $pytype"

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
		osflags="-Wl,-bundle,-undefined,dynamic_lookup,-lSystem,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC";
	;;
	*freebsd*)
		osflags="-Wl,-lc,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC -shared -pthread"
	;;
	*)
		osflags="-Wl,-shared,--export-all-symbols,--export-dynamic,-lc,-lpthread,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC"
	;;
esac

original="$(pwd)"

cd "$FAULT_PYTHON_PATH"
fault_dir="$(pwd)"
container_dir="$(dirname "$fault_dir")"
echo $container_dir

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
	compile ${CC:-cc} -w -ferror-limit=2 \
		-o "../../${modname}.${platsuffix}" \
		"-I$FAULT_SYSTEM_PATH/python/include/src" \
		"-I$FAULT_SYSTEM_PATH/machine/include/src" \
		"-I$fault_dir/system/include/src" \
		"-I$prefix/include" \
		"-I$prefix/include/python$pyversion$pyabi" \
		"-DF_SYSTEM=$defsys" \
		"-DF_TARGET_ARCHITECTURE=$defarch" \
		"-DF_INTENTION=debug" \
		"-DF_FACTOR_DOMAIN=system" \
		"-DF_FACTOR_TYPE=extension" \
		"-DFACTOR_BASENAME=$modname" \
		"-DFACTOR_SUBPATH=$modname" \
		"-DFACTOR_PROJECT=$projectfactor" \
		"-DFACTOR_PACKAGE=$package" \
		"-DFACTOR_QNAME=$fullname" \
		-fwrapv src/*.c
}

bootstrap_project ()
{
	cd "$1"
	root="$(dirname "$(pwd)")"

	echo $root
	echo $(pwd)
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
