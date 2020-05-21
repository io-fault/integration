"""
# Extend construction contexts with a base host domain for linking executables.
"""
import sys
import importlib
import itertools

from fault.system import process
from fault.system import python
from fault.system import files

from ....factors import data as ccd
from ....factors import cc
from .. import library

project = library.__package__

def strings(x):
	return tuple(map(str, [y for y in x if y]))

def nix_pdc(select):
	return [
		strings((select('crt1.o'), select('crti.o'), select('crtbegin.o')),),
		strings((select('crtend.o'), select('crtn.o')),),
	]

def nix_pie(select):
	return [
		strings((select('Scrt1.o'), select('crti.o'), select('crtbeginS.o')),),
		strings((select('crtendS.o'), select('crtn.o')),),
	]

def apple_pie(select):
	return [
		strings((select('crt1.o'), select('crti.o'), select('crtbeginS.o')),),
		strings((select('crtendS.o'), select('crtn.o')),),
	]

def dynamic(paths):
	root = files.Path.from_absolute('/')
	ldname, ld = library.select(library.environ_paths(), library.linkers, library.linker_preference)

	libdirs = [
		files.Path.from_relative(root, str(x).strip('/'))
		for x in paths
	]
	libdirs.extend(map(files.Path.from_absolute, paths))

	# scan for system objects (crt1.o, crt0.o, etc)
	found, missing = library.search(libdirs, [x+'.o' for x in library.runtime_objects])

	host, vendor, osname, arch, alts = library.identity()
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
				'pdc': [
					strings((found.get('crti.o'), found.get('crtbegin.o')),),
					strings((found.get('crtend.o'), found.get('crtn.o')),),
				],
				'pic': [
					strings((found.get('crti.o'), found.get('crtbeginS.o')),),
					strings((found.get('crtendS.o'), found.get('crtn.o')),),
				],
			},
			'extension': {
				# Only position independent.
				'pic': [
					strings((found.get('crti.o'), found.get('crtbeginS.o')),),
					strings((found.get('crtendS.o'), found.get('crtn.o')),),
				],
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
				'interface': project + (
					'.apple.macos_link_editor'
					if osname == 'darwin' else
					'.elf.gnu_link_editor'
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
			'pie': apple_pie(found.get)
		}
	else:
		system['objects']['executable'] = {
			'pdc': nix_pdc(found.get),
			'pie': nix_pie(found.get),
		}

	return system

name = 'fault.host' # Name of mechanism entry.
def install(args, fault, ctx, ctx_route, ctx_params, ctx_intention):
	"""
	# Initialize the instrumentation tooling for instruments contexts.
	"""

	mech = (ctx_route / 'mechanisms' / name)
	imp = python.Import.from_fullname(__package__).container

	data = dynamic(library.default_library_paths)
	data = {'host': data}
	ccd.update_named_mechanism(mech, 'root', data)
	ccd.update_named_mechanism(mech, 'path-setup', {'context':{'path':['host']}})

def main(inv:process.Invocation) -> process.Exit:
	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = files.Path.from_absolute(inv.environ['CONTEXT'])
	ctx = cc.Context.from_directory(ctx_route)
	ctx_params = ctx.index['context']
	ctx_intention = ctx_params['intention']

	install(inv.args, fault, ctx, ctx_route, ctx_params, ctx_intention)
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
