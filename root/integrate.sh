# Prepare fault.io/system and fault.io/python for use on the host system.
##

. "$FAULT_ROOT_PATH/tools.sh"

# Bootstrap Python extension modules.
python.sh

# Create product index.
f_pdctl -D "$SYSTEM_PRODUCT" delta -U -I "$PYTHON_PRODUCT"
f_pdctl -D "$PYTHON_PRODUCT" delta -U -I "$SYSTEM_PRODUCT"

# Bind system executables to python and integration factors.
libexec.sh "bootstrap"

# Initialize execution platform and construction context for the host.
host.sh "$HXP" "$FCC"

# Integrate fault.io/python and fault.io/integration using host/cc.
products.sh "$HXP" "$FCC" python-extension "-I$PYTHON_INCLUDE"
