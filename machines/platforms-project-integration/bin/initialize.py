"""
# Initialize an execution platform on the local filesystem for dispatching Python factors.
"""
import os
import sys

from fault.system import files
from fault.system import identity
from fault.system import process
from fault.system import execution

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
	splan = ''.join(execution.serialize_sx_plan((env, str(exepath), xargv)))
	sxp_python.fs_init(splan.encode('utf-8'))

def priority(host, python, path:files.Path):
	"""
	# Designate the priority of the architectures and their symbols.
	"""
	hostsym = " ".join((host, 'system'))
	pythonsym = " ".join((python, 'python'))

	psyms = "\n".join([hostsym, pythonsym]) + "\n"
	(path/vector.A_RECORD).fs_init(psyms.encode('utf-8'))

def main(inv:(process.Invocation)) -> (process.Exit):
	sys, arch = identity.root_execution_context()
	psys, python_arch = identity.python_execution_context()

	target = files.Path.from_path(inv.argv[0])

	if target.fs_type() != 'directory':
		target.fs_mkdir()
	vector.fs_initialize(target, sys)

	native(arch, target)
	python(python_arch, target)
	priority(arch, python_arch, target)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
