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

default_library_paths = [
	"/usr/lib", # Common location for runtime objects.
	"/lib",
	"/usr/local/lib",
	"/opt/lib",
]

def ldconfig_list(path="/usr/bin/ldconfig"):
	"""
	# Extract library paths from (system/executable)`ldconfig`.
	"""

	(pid, exitcode, data) = execution.dereference(execution.KInvocation(path, [path, "-v"]))
	l = [x for x in data.splitlines(b"\n") if x[0:1] != '\t']
	l = [x.split(':', 1)[0] for x in l]
	return l
