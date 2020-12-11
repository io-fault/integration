"""
# Runtime object patterns.
"""

def strings(x):
	return tuple(map(str, [y for y in x if y]))

def prepare(select, pattern, *, adjust=(lambda x: x + '.o')):
	return [
		strings(map(select, map(adjust, pattern[0]))),
		strings(map(select, map(adjust, pattern[1]))),
	]

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
