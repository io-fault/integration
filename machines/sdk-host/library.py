"""
# Host directory defaults and information supporting Construction Context initialization.

# The data and functions here solely support initialization for the default host domain.
# Command constructors used by the mechanisms normally exist as platform specific modules adjacent to this.
"""
import os
import typing
import types

from fault.system import execution as libexec
from fault.system import files

# map path strings to routes
def fs_routes(i:typing.Iterator[str]) -> typing.Sequence[files.Path]:
	return list(map(files.Path.from_absolute, i))

def environ_paths(env='PATH', sep=os.pathsep):
	"""
	# Construct a sequence of &files.Path instances to the paths stored
	# in an environment variable. &os.environ is referred to upon
	# each invocation, no caching is performed so each call represents
	# the latest version.

	# Defaults to `PATH`, &environ_paths can select an arbitrary environment variable
	# to structure using the &env keyword parameter.

	# This function exists to support &search as `search(environ_paths(), {...})` is
	# the most common use case.

	# [ Parameters ]
	# /env/
		# The environment variable containing absolute paths.
		# Defaults to `'PATH'`
	# /sep/
		# The path separator to split the environment variable on.
		# Defaults to &os.pathsep.
	"""

	s = os.environ[env].split(sep)
	seq = fs_routes(s)

	return seq

def search(
		search_paths:typing.Sequence[str],
		xset:typing.Set[str]
	) -> typing.Tuple[typing.Mapping[str, files.Path], typing.Set[str]]:
	"""
	# Query the sequence of search paths for the given set of files.

	# All paths will be scanned for each requested identifier in &xset. When an identifier
	# is found to exist, it is removed from the set that is being scanned for causing
	# the first path match to be the one returned.
	"""

	ws = set(xset)
	removed = set()
	rob = {}

	for r in search_paths:
		if not ws:
			break

		for x in ws:
			xr = r/x
			if xr.fs_type() != 'void':
				rob[x] = xr
				removed.add(x)

		if removed:
			ws.difference_update(removed)
			removed = set()

	return rob, ws

def select(paths, possibilities, preferences):
	"""
	# Select a file from the given &paths using the &possibilities and &preferences
	# to identify the most desired.
	"""

	# Override for particular version
	possible = set(possibilities)

	found, missing = search(paths, tuple(possible))
	if not found:
		return None
	else:
		for x in preferences:
			if x in found:
				path = found[x]
				name = x
				break
		else:
			# select one randomly
			name = tuple(found)[0]
			path = found[name]

	return name, path

def executables(xset:typing.Set[str]):
	"""
	# Query the (system/envvar)`PATH` for executables with the exact name.
	# Returns a pair whose first item is the matches that currently exist,
	# and the second is the set of executables that were not found in the path.
	"""
	return search(environ_paths(), xset)

linkers = {
	'lld': (
		'objects',
	),
	'ld': (
		'objects',
	),
}

linker_preference = ('lld', 'ld.lld', 'ld')

default_library_paths = [
	"/usr/lib", # Common location for runtime objects.
	"/lib",
	"/usr/local/lib",
]

extended_library_paths = [
	"/opt/lib",
]

# C-Family Runtime Objects in common use.
runtime_stem = 'crt'
runtime_objects = set([
	'crt0', # No constructor support.

	# Executable with constructor support.
	'crt1',

	'Scrt1', # Position Independent Executables.
	'gcrt1',
	'crt1S',

	'crtbeginT', # Statically Linked Executables.
	'crtend',

	# Shared Libraries
	'crtbeginS', # Position Independent Code.
	'crtendS',

	# Init and eNd.
	'crti',
	'crtn',
])

def uname(flag, path="/usr/bin/uname"):
	"""
	# Execute the (system/executable)`uname` returning its output for the given &flag.
	"""

	inv = libexec.KInvocation(path, [path, flag])
	pid, exitcode, out = libexec.dereference(inv)

	return out.strip().decode('utf-8')

def ldconfig_list(path="/usr/bin/ldconfig"):
	"""
	# Extract library paths from (system/executable)`ldconfig`.
	"""

	(pid, exitcode, data) = libexec.dereference(libexec.KInvocation(path, [path, "-v"]))
	l = [x for x in data.splitlines(b"\n") if x[0:1] != '\t']
	l = [x.split(':', 1)[0] for x in l]
	return l

def identity():
	"""
	# Constructs a tuple of identifiers for recongizing the host.
	"""
	vendor = None
	osname = uname('-s').lower()

	if osname == 'darwin':
		# Presume apple.
		vendor = 'apple'
	elif osname == 'linux':
		vendor = 'penguin'

	# First field of the target string.
	arch = uname('-m').lower()
	name = uname('-n').lower()

	arch_alt = arch.replace('_', '-')
	h_archs = [arch, arch_alt]
	if osname == 'darwin':
		h_archs.extend(['osx', 'macos'])

	return name, vendor, osname, arch, h_archs
