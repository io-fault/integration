import sys
import os
import os.path
import importlib

# Use sys.path entries and bootstrapped (python.sh) extension modules.
sys.path.append(os.path.dirname(os.environ['FAULT_PYTHON_PATH']))
sys.path.append(os.path.dirname(os.environ['FAULT_SYSTEM_PATH']))

module_path = '.'.join((os.environ['FAULT_CONTEXT_NAME'], 'system', 'bin', 'subexec'))
subexec = importlib.import_module(module_path)
subexec.process.control(subexec.main, subexec.process.Invocation.system())
