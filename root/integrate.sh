# Prepare fault.io/system and fault.io/python for use on the host system.

# Bootstrap Python extension modules.
python.sh

# Bind system executables to python and integration factors.
libexec.sh

# Initialize execution platform and construction context for the host.
host.sh "$FAULT_INSTALLATION/host"

# Integrate fault.io/python and fault.io/integration using host/cc.
products.sh "$FAULT_INSTALLATION/host/cc" python-extension "-I$PYTHON_INCLUDE"
