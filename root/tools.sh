# Function variants of some of the fault tools.
##

f_pyx ()
{
	"$PYTHON" "$PYX" "$@"
}

f_pdctl ()
{
	f_pyx system.products.bin.control "$@"
}

f_bind ()
{
	f_pyx .module system.python.bin.bind \
		"-F$FAULT_PYTHON_PATH" "-L$SYSTEM_PRODUCT" \
		"$@"
}
