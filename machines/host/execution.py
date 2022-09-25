"""
# Execution Platform initialization tools for the host system.
"""
from fault.system import files
from fault.system import identity

from fault.system.execution import serialize_sx_plan

from .. import vector
from ...root import query

def native(architecture:str, path:files.Path):
	"""
	# Create the default native execution handler.
	"""
	sxp_native = (path/vector.P_RECORD/architecture)
	sxp_native.fs_init(b'')

def python(architecture:str, path:files.Path):
	"""
	# Assign the host Python to the context.
	"""
	sxp_python = (path/vector.P_RECORD/architecture)
	env, exepath, xargv = query.tool('python')
	xargv.append('-d')
	splan = ''.join(serialize_sx_plan((env, str(exepath), xargv)))
	sxp_python.fs_init(splan.encode('utf-8'))

def priority(host, python, path:files.Path):
	"""
	# Designate the priority of the architectures and their symbols.
	"""
	hostsym = " ".join((host, 'system'))
	pythonsym = " ".join((python, 'python'))

	psyms = "\n".join([hostsym, pythonsym]) + "\n"
	(path/vector.A_RECORD).fs_init(psyms.encode('utf-8'))

def initialize(target:files.Path):
	"""
	# Initialize the &target with the default host execution platform.
	"""
	sys, arch = identity.root_execution_context()
	psys, python_arch = identity.python_execution_context()

	vector.fs_initialize(target, sys)
	native(arch, target)
	python(python_arch, target)
	priority(arch, python_arch, target)
