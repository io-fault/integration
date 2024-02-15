"""
# Python factor execution script used in the absence of system bindings.
"""
import sys
import os
import os.path
import importlib

# Environment variables normally set by &..root.setup.
path_sources = ['FAULT_PYTHON_PATH', 'FAULT_SYSTEM_PATH']
fault_name = os.environ['FAULT_CONTEXT_NAME']
factors_module_path = '.'.join((fault_name, 'system', 'factors'))
subexec_module_path = '.'.join((fault_name, 'system', 'execute'))
tool_module_path = '.'.join((fault_name, 'system', 'tool'))

def extend_python_path(pathrefs):
	# Use sys.path entries and bootstrapped (python.sh) extension modules.
	ext = list(map(os.path.dirname, (os.environ[x] for x in pathrefs)))
	sys.path.extend(ext)

	# Some tools (root.cc) need to resolve non-python factors.
	try:
		factors = importlib.import_module(factors_module_path)
		factors.setup(paths=ext)
		del sys.meta_path[0:1]
	except FileNotFoundError:
		# Compensates for the initialization stage where
		# project indexes have yet to be built.
		pass

def av_execution(module_path):
	extend_python_path(path_sources)
	subexec = importlib.import_module(module_path)
	inv = subexec.process.Invocation.system()
	inv.argv[0:0] = [
		'-lfault.context.execute',
		'-lsystem.context.execute',
		tool_module_path,
	]
	subexec.process.control(subexec.main, inv)

if __name__ == '__main__':
	av_execution(subexec_module_path)
