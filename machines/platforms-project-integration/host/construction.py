"""
# Host construction context initialization.
"""
import itertools

from fault.project import system as lsf
from fault.project import factory

from fault.system import files
from fault.system import factors
from fault.system import identity
from fault.system import execution

from ...root import query

from ...machine import __name__ as machine_project
from ...python import __name__ as python_project
from ...chapters import __name__ as chapters_project

def mkinfo(path, name):
	return lsf.types.Information(
		identifier = 'i-http://fault.io//construction/' + path,
		name = name,
		authority = 'fault.io',
		abstract = "Construction Context.",
		icon = dict([('emoji', "#")]),
		contact = "&<http://fault.io/critical>"
	)

def mktype(semantics, type, language, identifier='http://if.fault.io/factors'):
	fpath = lsf.types.factor@semantics
	if type:
		fpath @= type
	return lsf.types.Reference(identifier, fpath, 'type', language)

interfaces = [
	lsf.types.Reference('http://fault.io/integration/machine', lsf.types.factor@'include'),
	lsf.types.Reference('http://fault.io/integration/python', lsf.types.factor@'include'),
]

ihost = {
	'*.c': [mktype('system', 'type', 'c.2011')],
	'*.h': [mktype('system', 'type', 'c.header')],
}

ipython = {
	'*.py': [mktype('python', 'module', 'python.psf-v3')],
	'*.pyi': [mktype('python', 'interface', 'python.psf-v3')],
}

ivector = {
	'*.v': [mktype('vector', 'set', 'fault-vc')],
	'*.sys': [mktype('vector', 'system', 'fault-vi')],
}

vtype = 'vector.set'
clang_delineate = (query.bindir() / 'clang-delineate')

def system(path, *args):
	xargs = [path]
	xargs.extend(args)
	return ''.join(execution.serialize_sx_plan(([], path, xargs)))

def iproduct(route, connections):
	"""
	# Initialize the product index and return the created instance.
	"""
	pd = lsf.Product(route)
	pd.update()
	pd.store()
	cxn = pd.connections_index_route
	cxn.fs_store('\n'.join(str(x) for x in connections).encode('utf-8'))
	return pd

def mksole(fpath, type, source):
	return (fpath, lsf.types.factor@type, source)

def mkset(fpath:str, type:str, symbols, sources):
	return (fpath, type, symbols, sources)

def getsource(project, name, ext='.v'):
	pj = factors.context.split('.'.join((project, name)))[1]
	return pj.route/(name+ext)

def comment(text):
	return "# " + text + "\n"

def constant(name, *types):
	init = name + ':\n'
	if types:
		return init + '\t: ' + '\n\t: '.join(types) + '\n\n'
	return init

def define(name, *types):
	s = name + ':\n'
	for conclusion, vfe in types:
		s += '\t' + conclusion + ':' + (' ' + vfe if vfe else '')
		s += '\n'
	return s

def form_host_target(hlinker):
	target = ""
	target += comment("Options for the selected CC. Included regardless of language.")
	target += constant('-system-cc-options')

	target += "\n"
	target += comment("Directory paths (-isystem) to system headers.")
	target += constant('-system-includes', "/usr/local/include")

	target += "\n"
	target += comment("Defines (-D implied) to include as command options.")
	target += constant('-system-defines')

	target += "\n"
	target += comment("Libraries to unconditionally link against.")
	target += constant('-system-libraries')

	target += "\n"
	target += comment("Additional paths to look in to find [-system-libraries].")
	target += constant('-system-library-directories', "/usr/local/lib")

	target += "\n"
	target += comment("Compiler flags used to select the target architecture.")
	target += constant('-cc-select-architecture', "-march=native")

	target += "\n"
	target += comment("One of: -apple-ld-macho -gnu-ld-elf -llvm-ld-elf")
	target += comment("Linker backend should be designated here as well if desired.")
	target += comment("However, it and the option must be matched with the corresponding adapter.")
	target += comment("-fuse-ld=llvm|bfd|gold")
	target += constant('-cc-select-ld-interface', hlinker)

	return target

def form_variants(system, architecture, forms=()):
	variants = ""
	variants += constant('[systems]', system)
	variants += constant('['+system+']', architecture)
	if forms:
		variants += constant('[forms]', *forms)
	return variants

def form_host_type():
	common = "# Alternatively, ..context.usr-cc.\n"
	common += define('-cc-compile-tool',
		('fv-form-delineated', '.cc-delineate'),
		('!', '.cc'),
	) + '\n'

	common += define('-cc-link-tool',
		('fv-form-delineated', '.archive-delineated'),
		('!', '.cc'),
	) + '\n'

	common += constant('Translate',
		'[-cc-compile-tool]',
		'-cc-compile-1',
		'.unix-cc-1',
		'.target',
	)
	common += constant('Render',
		'[-cc-link-tool]',
		'-cc-link-1',
		'.unix-cc-1',
		'.target',
	)
	return common

def host(context, hlinker, hsystem, harch, factor='type', name='cc', cc='/usr/bin/cc'):
	machine_cc = getsource(machine_project, name)
	deline = system(str(clang_delineate))
	deline = query.dispatched('python', '-d', '.system', 'tools.fault-llvm.delineate')
	adeline = query.dispatched('archive-delineated')
	cc_default = system(cc)

	target = form_host_target(hlinker)
	variants = form_variants(hsystem, harch)
	common = form_host_type()

	return [
		mksole('target', vtype, target),
		mksole('variants', vtype, variants),
		mksole('unix-cc-1', vtype, machine_cc.fs_load()),

		mksole('cc-delineate', 'vector.system', deline),
		mksole('archive-delineated', 'vector.system', adeline),
		mksole('cc', 'vector.system', cc_default),

		mksole('type', vtype, common),
		mksole('executable', vtype, ''),
		mksole('extension', vtype, ''),
		mksole('library', vtype, ''),
		mksole('archive', vtype, ''),
	]

def form_text_type():
	common = ""
	common += constant('-text-tool',
		'.ft-text-cc',
	)
	common += constant('Translate',
		'[-text-tool]',
		'-parse-text-1',
		'.text-delineate-1',
	)
	common += constant('Render',
		'[-text-tool]',
		'-store-chapter-1',
		'.text-delineate-1',
	)
	return common

def text(context, factor='type', name='cc'):
	text_cc_vectors = getsource(chapters_project, name)

	variants = form_variants('void', 'json', forms=['delineated'])
	common = form_text_type()

	txtcc = query.dispatched('text-cc')

	return [
		mksole('ft-text-cc', 'vector.system', txtcc),
		mksole('text-delineate-1', vtype, text_cc_vectors.fs_load()),
		mksole('variants', vtype, variants),
		mksole('type', vtype, common),

		# Intregation types.
		mksole('chapter', vtype, ''),
		mksole('manual', vtype, ''),
		mksole('source', vtype, ''),
	]

def form_python_type():
	common = ""
	common += constant('-pyc-tool',
		'.ft-python-cc',
	)
	common += constant('Translate',
		'[-pyc-tool]',
		'-pyc-ast-1',
		'.fault-pyc-1',
	)
	common += constant('Render',
		'[-pyc-tool]',
		'-pyc-reduce-1',
		'.fault-pyc-1',
	)
	return common

def python(context, psystem, parch, factor='type', name='cc'):
	python_cc = getsource(python_project, name)
	variants = form_variants(psystem, parch)
	common = form_python_type()

	pycc = query.dispatched('python-cc')

	return [
		mksole('ft-python-cc', 'vector.system', pycc),
		mksole('fault-pyc-1', vtype, python_cc.fs_load()),
		mksole('variants', vtype, variants),
		mksole('type', vtype, common),

		# Intregation types.
		mksole('module', vtype, ''),
		mksole('interface', vtype, ''),
		mksole('source', vtype, ''),
	]

def mkctx(info, product, context, soles=[]):
	route = (product/context/'context').fs_alloc()
	i = list(itertools.chain(
		ihost.items(),
		ipython.items(),
		ivector.items()
	))
	return (factory.Parameters.define(info, i, sets=[], soles=soles), route)

def mkproject(info, product, context, project, soles):
	route = (product/context/project).fs_alloc()
	i = list(ivector.items())
	return (factory.Parameters.define(info, i, sets=[], soles=soles), route)

def mktools(context, route, name='cc-tool-adapters'):
	pi = mkinfo(context + '.context', name)
	pj = mkctx(pi, route, context, [])
	factory.instantiate(*pj)

def system_select_linker(system):
	"""
	# Select the linker command interface to use based on the system's name.
	"""
	if system == 'darwin':
		return '[-apple-ld-macho]'
	elif system in {'linux', 'openbsd'}:
		return '[-gnu-ld-elf]'
	else:
		return '[-llvm-ld-elf]'

def mkvectors(context, route, name='vectors'):
	soles = [
		mksole('usr-cc', 'vector.system', system('/usr/bin/cc')),
		mksole('usr-ar', 'vector.system', system('/usr/bin/ar')),
		mksole('bin-cp', 'vector.system', system('/bin/cp')),
		mksole('bin-ln', 'vector.system', system('/bin/ln')),

		mksole('projections', vtype,
			constant('host', 'http://if.fault.io/factors/system') + \
			constant('python', 'http://if.fault.io/factors/python') + \
			constant('text', 'http://if.fault.io/factors/text')
		),
	]

	# Vectors Context
	pi = mkinfo(context + '.context', name)
	pj = mkctx(pi, route, context, soles)
	factory.instantiate(*pj)

	hsys, harch = identity.root_execution_context()
	hlink = system_select_linker(hsys)

	# Host Machine
	pi = mkinfo(context + '.host', 'host')
	pj = mkproject(pi, route, context, 'host', host(context, hlink, hsys, harch))
	factory.instantiate(*pj)

	# Python
	psys, parch = identity.python_execution_context()
	pi = mkinfo(context + '.python', 'python')
	pj = mkproject(pi, route, context, 'python', python(context, psys, parch))
	factory.instantiate(*pj)

	# Chapters
	pi = mkinfo(context + '.text', 'text')
	pj = mkproject(pi, route, context, 'text', text(context))
	factory.instantiate(*pj)

def mkcc(route):
	mkvectors('vectors', route)
	mktools('tools', route)
	iproduct(route, [x.route for x in factors.context.product_sequence])
