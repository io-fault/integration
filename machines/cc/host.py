from fault.system import files

from .. import query
from .. import rt

def dynamic(paths):
	ldname, ld = query.select(query.query.paths(), query.linkers, query.linker_preference)

	libdirs = [
		files.Path.from_relative(files.root, str(x).strip('/'))
		for x in paths
	]
	libdirs.extend(map(files.Path.from_absolute, paths))

	# Scan for system objects (crt1.o, crt0.o, etc)
	found, missing = query.search(libdirs, [x+'.o' for x in rt.objects])

	host, vendor, osname, arch, alts = query.identity()
	system = {
		# domain data
		'identifier': '-'.join(([vendor] if vendor is not None else []) + [osname, arch]),
		'vendor': vendor,
		'system': osname,
		'architecture': arch,
		'alternates': alts,
		'name': host,

		'variants': {
			'system': osname,
			'architecture': arch,
		},

		'target-file-extensions': {
			'library': '.so',
			'extension': '.so',
			'executable': '.exe',
			'partial': '.fo',
		},

		# Format selected for factor-types.
		'formats': {
			'executable': 'pie',
			'library': 'pic',
			'extension': 'pic',
			# Partials inherit format.
		},

		# objects used to support the construction of system targets
		# The split (prefix objects and suffix objects) is used to support
		# linkers where the positioning of the parameters is significant.
		'objects': {
			'library': {
				'pdc': rt.prepare(found.get, rt.posix_pdc),
				'pic': rt.prepare(found.get, rt.posix_pic),
			},
			'extension': {
				# Only position independent.
				'pic': rt.prepare(found.get, rt.posix_pic),
			},
			# partials do not have any standard link time objects.
			'partial': None,
		},

		'transformations': {
			None: None,
		},

		# subject interfaces.
		'integrations': {
			'tool:link-editor': {
				'type': 'linker',
				'interface': query.__package__ + (
					'.apple.macos_link_editor'
					if osname == 'darwin' else
					'.gnu.gnu_link_editor'
				),
				'name': ldname,
				'command': str(ld),
			},
			'library': {
				'inherit': 'tool:link-editor',
			},
			'executable': {
				'inherit': 'tool:link-editor',
			},
			'extension': {
				'inherit': 'tool:link-editor',
			},
			'partial': {
				'inherit': 'tool:link-editor',
			},
			None: None,
		},
	}

	if osname == 'darwin':
		# No support for statically linked executables.
		# https://developer.apple.com/library/content/qa/qa1118/_index.html
		system['objects']['executable'] = {
			'pie': rt.prepare(found.get, rt.apple_pie)
		}
	else:
		system['objects']['executable'] = {
			'pdc': rt.prepare(found.get, rt.posix_pdc),
			'pie': rt.prepare(found.get, rt.posix_pie),
		}

	return system
