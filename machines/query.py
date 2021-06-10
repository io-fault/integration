"""
# Host directory defaults and information supporting Construction Context initialization.

# The data and functions here solely support initialization for the default host domain.
# Command constructors used by the mechanisms normally exist as platform specific modules adjacent to this.
"""
import os
import typing
import types

from fault.system import execution
from fault.system import files
from fault.system import query

# map path strings to routes
def fs_routes(i:typing.Iterator[str]) -> typing.Sequence[files.Path]:
	return list(map(files.Path.from_absolute, i))

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

def executables(paths, xset:typing.Set[str]):
	"""
	# Query the (system/envvar)`PATH` for executables with the exact name.
	# Returns a pair whose first item is the matches that currently exist,
	# and the second is the set of executables that were not found in the path.
	"""
	return search(paths, xset)

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

def uname(flag, path="/usr/bin/uname"):
	"""
	# Execute the (system/executable)`uname` returning its output for the given &flag.
	"""

	inv = execution.KInvocation(path, [path, flag])
	pid, exitcode, out = execution.dereference(inv)

	return out.strip().decode('utf-8')

def ldconfig_list(path="/usr/bin/ldconfig"):
	"""
	# Extract library paths from (system/executable)`ldconfig`.
	"""

	(pid, exitcode, data) = execution.dereference(execution.KInvocation(path, [path, "-v"]))
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

def detect_profile_library(libdir, architectures):
	"""
	# Given an `tool:llvm-clang` mechanism and a sequence of architecures, discover
	# the appropriate profile library to link against when building targets
	# that consist of LLVM instrumented sources.
	"""
	profile_libs = [x for x in libdir.fs_iterfiles('data') if 'profile' in x.identifier]

	if len(profile_libs) == 1:
		# Presume target of interest.
		profile_lib = profile_libs[0]
	else:
		# Scan for library with matching architecture.
		for x, a in itertools.product(profile_libs, architectures):
			if a in x.identifier:
				profile_lib = x
				break
		else:
			profile_lib = None

	if profile_lib.fs_type() == 'void':
		profile_lib = None

	return profile_lib
