# Function variants of some of the fault tools.
##

f_pyx ()
{
	"$PYTHON" "$PYX" "$@"
}

f_fictl ()
{
	f_pyx fictl "$@"
}

f_image ()
{
	f_pyx python .script \
		"$FAULT_ROOT_PATH/image-select.py" \
		"$@"
}
