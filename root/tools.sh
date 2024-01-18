# Function variants of some of the fault tools.
##

f_pyx ()
{
	"$PYTHON" "$PYX" "$@"
}

f_pdctl ()
{
	f_pyx products-cc "$@"
}

f_image ()
{
	f_pyx python .script \
		"$FAULT_ROOT_PATH/image-select.py" \
		"$@"
}
