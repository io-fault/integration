"""
# Create a construction context for the host system.
"""
import itertools

from fault.project import system as lsf
from fault.project import factory
from fault.system import process
from fault.system import files
from fault.system import factors
from fault.system import identity
from fault.system import execution

from . import query

from ..root import __name__ as root_project
from ..machine import __name__ as machine_project
from ..python import __name__ as python_project

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
dispatch_command = (query.libexec() / 'fault-dispatch')
clang_delineate = (query.bindir() / 'clang-delineate')

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

def host(context, hlinker, hsystem, harch, factor='type', name='cc'):
	machine_cc = getsource(machine_project, name)
	clang_delineate
	deline = ''.join(execution.serialize_sx_plan(([], str(clang_delineate), [
		str(clang_delineate),
	])))

	usr_cc = getsource(root_project, 'usr-cc', ext='.sys')
	bin_cp = getsource(root_project, 'bin-cp', ext='.sys')
	bin_ln = getsource(root_project, 'bin-ln', ext='.sys')

	target = ""
	target += comment("Directory paths to include directories.")
	target += constant('-system-includes', "/usr/local/include")
	target += comment("Libraries to unconditionally link against. Unused libraries will be filtered.")
	target += constant('-system-libraries')
	target += comment("Additional paths to look in to find [-system-libraries].")
	target += constant('-system-library-directories', "/usr/local/lib")

	target += comment("Compiler flags used to select the target architecture.")
	target += constant('-cc-select-architecture', "-march=native")

	target += "\n"
	target += comment("One of: -apple-ld-macho -gnu-ld-elf -llvm-ld-elf")
	target += comment("Linker backend should be designated here as well if desired.")
	target += comment("However, it and the option must be matched with the corresponding adapter.")
	target += comment("-fuse-ld=llvm|bfd|gold")
	target += constant('-cc-select-ld-interface', hlinker)

	variants = ""
	variants += constant('[systems]', hsystem)
	variants += constant('['+hsystem+']', harch)

	common = ""
	common += define('-cc-tool',
		('fv-idelineation', context + '.host.cc-delineate'),
		('!', context + '.host.usr-cc'),
	) + '\n'

	common += constant('Translate',
		'[-cc-tool]',
		'-cc-compile-1',
		'unix-cc-1',
		'target',
	)
	common += constant('Render',
		'[-cc-tool]',
		'-cc-link-1',
		'unix-cc-1',
		'target',
	)

	return [
		mksole('target', vtype, target),
		mksole('variants', vtype, variants),
		mksole('unix-cc-1', vtype, machine_cc.fs_load()),

		mksole('cc-delineate', 'vector.system', deline),
		mksole('bin-ln', 'vector.system', bin_ln.fs_load()),
		mksole('bin-cp', 'vector.system', bin_cp.fs_load()),
		mksole('usr-cc', 'vector.system', usr_cc.fs_load()),

		mksole('type', vtype, common),
		mksole('executable', vtype, ''),
		mksole('extension', vtype, ''),
		mksole('library', vtype, ''),
		mksole('archive', vtype, ''),
	]

def python(context, psystem, parch, factor='type', name='cc'):
	python_cc = getsource(python_project, name)

	variants = ""
	variants += constant('[systems]', psystem)
	variants += constant('['+psystem+']', parch)

	common = ""
	common += constant('-pyc-tool',
		context + '.python.ft-python-cc',
	)
	common += constant('Translate',
		'[-pyc-tool]',
		'-pyc-ast-1',
		'fault-pyc-1',
	)
	common += constant('Render',
		'[-pyc-tool]',
		'-pyc-bytecode-1',
		'fault-pyc-1',
	)

	pycc = ''.join(execution.serialize_sx_plan(([], str(dispatch_command), [
		str(dispatch_command),
		'python-cc',
	])))
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

def mkprojects(context, route):
	pi = mkinfo(context + '.context', 'image')
	soles = [
		mksole('projections', 'vector.set',
			'host:\n\t: http://if.fault.io/factors/system\n'
			'python:\n\t: http://if.fault.io/factors/python\n'
		),
	]
	pj = mkctx(pi, route, context, soles)
	factory.instantiate(*pj)

	pi = mkinfo(context + '.host', 'host')

	hsys, harch = identity.root_execution_context()
	if hsys == 'darwin':
		hlink = '[-apple-ld-macho]'
	elif hsys in {'linux', 'openbsd'}:
		hlink = '[-gnu-ld-elf]'
	else:
		hlink = '[-llvm-ld-elf]'

	pj = mkproject(pi, route, context, 'host', host(context, hlink, hsys, harch))
	factory.instantiate(*pj)

	pi = mkinfo(context + '.python', 'python')
	psys, parch = identity.python_execution_context()
	pj = mkproject(pi, route, context, 'python', python(context, psys, parch))
	factory.instantiate(*pj)

def main(inv:process.Invocation) -> process.Exit:
	target, = inv.argv

	# Load the project index.
	factors.context.load()
	factors.context.configure()

	route = files.Path.from_path(target)
	mkprojects('vectors', route)
	iproduct(route, [x.route for x in factors.context.product_sequence])

	return inv.exit(0)
