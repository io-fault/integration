# Check parameters used by &system.root and export them.

# [ Parameters ]
# Parameters are exported for use with all the stages of initialization.

# /FAULT_PYTHON_PATH/
	# String path identifier for the &<http://fault.io/python> product.
	# Must include the context directory.
# /FAULT_SYSTEM_PATH/
	# String path identifier for the &<http://fault.io/integration> product.
# /FAULT_LIBEXEC_PATH/
	# String path identifier for the location that will contain tool bindings used
	# to support initialization and default construction contexts.
# /PYTHON/
	# Path to the python3 executable that initialization should use.

# Location of root setup scripts.
if test x"$FAULT_ROOT_PATH" = x""
then
	FAULT_ROOT_PATH="$(cd "$(dirname "$0")" && pwd)"
fi
PYX="$FAULT_ROOT_PATH/factor-execute.py"

FAULT_PYTHON_PATH="$1"; shift 1
if ! test -d "$FAULT_PYTHON_PATH"
then
	echo >&2 "first argument must be the 'fault' (python) context package root directory."
	exit 2
fi

FAULT_SYSTEM_PATH="$1"; shift 1
if ! test -d "$FAULT_SYSTEM_PATH"
then
	echo >&2 "second argument must be the 'system' (integration) context package root directory."
	exit 3
fi

FAULT_LIBEXEC_PATH="$1"; shift 1
if ! test -d "$FAULT_LIBEXEC_PATH"
then
	echo >&2 "third argument must be a directory path that can be used to contain executables."
	exit 4
fi

PYTHON="$1"; shift 1
if ! test -x "$PYTHON"
then
	echo >&2 "fourth argument must be the selected Python implementation; the system executable."
	exit 100
fi

# Get final name in path.
if test x"" = "x"$FAULT_CONTEXT_NAME
then
	IFS=/
	for i in $FAULT_PYTHON_PATH
	do
		if ! test x"" = "$i"
		then
			FAULT_CONTEXT_NAME="$i"
		fi
	done
	unset i IFS
fi

export FAULT_ROOT_PATH FAULT_LIBEXEC_PATH PYX
export FAULT_CONTEXT_NAME
export FAULT_PYTHON_PATH
export FAULT_SYSTEM_PATH
export PYTHON
