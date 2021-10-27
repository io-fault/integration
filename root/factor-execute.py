"""
# Python factor execution script used in the absence of system bindings.

# Normally, this is only executed by &.setup, but in cases where &..python.bin.bind
# cannot create usable executables with the system's compiler driver, shell scripts
# will be created instead invoking this script with the necessary environment variables.
"""
import sys
import os
import os.path
import importlib

# Environment variables normally set by &..root.setup.
path_sources = ['FAULT_PYTHON_PATH', 'FAULT_SYSTEM_PATH']
fault_name = os.environ['FAULT_CONTEXT_NAME']
factors_module_path = '.'.join((fault_name, 'system', 'factors'))
subexec_module_path = '.'.join((fault_name, 'system', 'bin', 'subexec'))

def extend_python_path(pathrefs):
	# Use sys.path entries and bootstrapped (python.sh) extension modules.
	ext = list(map(os.path.dirname, (os.environ[x] for x in pathrefs)))
	sys.path.extend(ext)

	# Some tools (root.cc) need to resolve non-python factors.
	factors = importlib.import_module(factors_module_path)
	factors.setup(paths=ext)
	del sys.meta_path[0:1]

def av_execution(module_path):
	extend_python_path(path_sources)
	subexec = importlib.import_module(module_path)
	subexec.process.control(subexec.main, subexec.process.Invocation.system())

if __name__ == '__main__':
	av_execution(subexec_module_path)
