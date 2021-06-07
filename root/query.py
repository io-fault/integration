"""
# Location information module for identifying directories prepared by &..root.
"""
import os
from fault.system import files

# The default fault-io installation layout.
root_project_path = files.Path.from_absolute(__file__) ** 1
installation_path = root_project_path ** 3

# Check for explicit designation.
installation_envstr = os.environ.get('FAULT_INSTALLATION', '').strip() or None
if installation_envstr is not None:
	ipath = files.Path.from_absolute(installation_envstr)
	if ipath.fs_type() != 'directory':
		ipath = installation_path
else:
	ipath = installation_path

# Paths are accessed through functions in case applications need to globally switch prefixes.

def libexec():
	"""
	# Get the path to the `libexec` directory used by the fault installation.
	"""
	return ipath/'libexec'

def bindir():
	"""
	# Get the path to the user executable tools directory used by the fault installation.
	"""
	return ipath/'bin'

def libdir():
	"""
	# Get the path to the `lib` directory used by the fault installation.
	"""
	return ipath/'lib'

def tool(name):
	"""
	# Prepare a structured plan for executing the tool identified by &name.
	"""
	path = (bindir()/'fault-tool')
	# (environment, executable[files.Path], argument-vector)
	return ([], path, [str(path), str(name)])

def dispatch(name):
	"""
	# Prepare a structured plan for executing the tool identified by &name.

	# This is intended for use by tools and daemons that spawn high-level
	# operations as subprocesses.
	"""
	path = (libexec()/'fault-dispatch')
	# (environment, executable[files.Path], argument-vector)
	return ([], path, [str(path), str(name)])

def platform():
	"""
	# Get the path to the logical platform used by the fault installation.
	"""
	return ipath/'host'
