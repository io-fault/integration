# Prepare fault.io/system and fault.io/python for use on the host system.

# Bootstrap Python extension modules.
python.sh

# Index Products.
"$PYTHON" "$PYX" system.products.bin.control -D "$SYSTEM_PRODUCT" index
"$PYTHON" "$PYX" system.products.bin.control -D "$PYTHON_PRODUCT" index

# Bind system executables to python and integration factors.
libexec.sh "bootstrap"

# Initialize execution platform and construction context for the host.
host.sh "$FAULT_INSTALLATION/host"

# Integrate fault.io/python and fault.io/integration using host/cc.
products.sh "$FAULT_INSTALLATION/host/cc" python-extension "-I$PYTHON_INCLUDE"
