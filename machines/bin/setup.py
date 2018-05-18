"""
# Extend construction contexts with a base host domain for linking executables.
"""
import sys
import importlib
import itertools

from fault.system import library as libsys
from fault.routes import library as libroutes
from ....factors import cc
from .. import library

tool_name = 'host'

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
	root = libroutes.File.from_absolute('/')
	ldname, ld = library.select(library.environ_paths(), library.linkers, library.linker_preference)

	libdirs = [
		libroutes.File.from_relative(root, str(x).strip('/'))
		for x in paths
	]
	libdirs.extend(map(libroutes.File.from_absolute, paths))

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
				'interface': None,
				'name': ldname,
				'command': str(ld),
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

def install(args, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the instrumentation tooling for instruments contexts.
	"""

	mech = (ctx_route / 'mechanisms' / 'intent.xml')
	imp = libroutes.Import.from_fullname(__package__).container

	data = dynamic(library.default_library_paths)
	data = {'host': data}
	cc.update_named_mechanism(ctx_route / 'mechanisms' / 'intent.xml', tool_name, data)

def main(inv:libsys.Invocation) -> libsys.Exit:
	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])
	ctx = cc.Context.from_environment()
	ctx_params = ctx.parameters.load('context')[-1]
	ctx_intention = ctx_params['intention']

	intent(inv.args, fault, ctx, ctx_route, ctx_params)
	return inv.exit(0)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
