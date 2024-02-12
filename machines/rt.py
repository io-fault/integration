"""
# Runtime object patterns.
# Currently unused as the compiler driver is used for linkage.
"""
from collections.abc import Sequence, Set, Mapping
from fault.system import files

def strings(x):
	return tuple(map(str, [y for y in x if y]))

def prepare(select, pattern, *, adjust=(lambda x: x + '.o')):
	return [
		strings(map(select, map(adjust, pattern[0]))),
		strings(map(select, map(adjust, pattern[1]))),
	]

def _search(
		search_paths:Sequence[str],
		xset:Set[str]
	) -> tuple[Mapping[str, files.Path], Set[str]]:
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

def search(libdirs):
	# Scan for system objects (crt1.o, crt0.o, etc)
	found, missing = _search(libdirs, [x+objext for x in rt.objects])
	return found

stem = 'crt'
objects = set([
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

posix_pde = (
	('crt1', 'crti', 'crtbegin'),
	('crtend', 'crtn'),
)

posix_pie = (
	('Scrt1', 'crti', 'crtbeginS'),
	('crtendS', 'crtn'),
)

apple_pie = (
	('crt1', 'crti', 'crtbeginS'),
	('crtendS', 'crtn'),
)

posix_pdc = (
	('crti', 'crtbegin'),
	('crtend', 'crtn'),
)

posix_pic = (
	('crti', 'crtbeginS'),
	('crtendS', 'crtn'),
)
