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
from ...machines import __name__ as machines_project

def mkinfo(path, name):
	return lsf.types.Information(
		identifier = 'i-http://fault.io/system/' + path,
		name = name,
		authority = 'fault.io',
		contact = "http://fault.io/critical"
	)

def mktype(semantics, type, language, identifier='http://if.fault.io/factors'):
	fpath = lsf.types.factor@semantics
	if type:
		fpath @= type
	return lsf.types.Reference(identifier, fpath, 'type', language)

interfaces = [
	lsf.types.Reference('http://fault.io/integration/machines', lsf.types.factor@'include'),
]

formats = {
	'http://if.fault.io/factors/system': [
		('type', 'c', '2011', 'c'),
		('type', 'h', '2011', 'c'),
		('references', 'sr', 'lines', 'text'),
	],
	'http://if.fault.io/factors/python': [
		('module', 'py', 'psf-v3', 'python'),
		('interface', 'pyi', 'psf-v3', 'python'),
	],
	'http://if.fault.io/factors/vector': [
		('set', 'v', '', 'fault-vc'),
		('system', 'sys', '', 'fault-vi'),
	],
}

vformats = {
	'http://if.fault.io/factors/system': [
		('type', 'c', '2011', 'c'),
		('type', 'h', '2011', 'c'),
		('references', 'sr', 'lines', 'text'),
	],

	'http://if.fault.io/factors/vector': [
		('set', 'v', '', 'fault-vc'),
		('system', 'sys', '', 'fault-vi'),
	],
	'http://if.fault.io/factors/meta': [
		('references', 'fr', 'lines', 'text'),
	],
}

vtype = 'vector.set'
metasources = 'http://if.fault.io/factors/meta.sources'
systemexecutable = 'http://if.fault.io/factors/system.executable'
systemreferences = 'system.references'
factorreferences = 'meta.references'
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

def fx(fpath, name, *argv, **env):
	return mksole(fpath, 'vector.system', query.dispatched(name, *argv, **env))

def mkset(fpath:str, type:str, symbols, sources):
	return (fpath, type, symbols, sources)

def getsource(project, name, ext='.v'):
	pd, pj, fp = factors.context.split('.'.join((project, name)))
	return (pj.route//fp).suffix(ext)

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
	target += constant('-system-cc-options', "[-clang-diagnostics]")

	target += "\n"
	target += comment("Directory paths (-isystem) to system headers.")
	target += constant('-system-includes', "/usr/local/include")

	target += "\n"
	target += comment("Defines (-D implied) to include as command options.")
	target += constant('-system-defines', '_DEFAULT_SOURCE')

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

def form_variants(system, architecture, modes=()):
	variants = ""
	if modes:
		variants += constant('[modes]', *modes)

	variants += constant('[systems]', system)
	variants += constant('['+system+']', architecture)

	return variants

def form_host_type():
	common = comment("Alternatively, ..context.usr-cc.")

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

def host(route, context, hlinker, hsystem, harch, factor='type', name='host.cc', cc='/usr/bin/cc'):
	machine_cc = getsource(machines_project, name)
	deline = system(str(clang_delineate))
	deline = query.dispatched(
		'python', '-L' + str(route), '.system', 'fault-metrics.llvm.delineate')
	adeline = query.dispatched('archive-delineated')
	cc_default = system(cc)

	target = form_host_target(hlinker)
	variants = form_variants(hsystem, harch, modes=['executable', 'delineation'])
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
	], []

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

def python_bind(system, architecture, host):
	import fault as f
	import fault.system as fsys
	import sys
	pyproduct = (files.root@fsys.__file__) ** 3

	quoted = (lambda x: '"' + x + '"')
	return '\n'.join([
		"/* Python and fault locations for binding executable (factor) modules. */",
		"#define PYTHON_EXECUTABLE_PATH " + quoted(sys.executable),
		"#define FAULT_PYTHON_IMPLEMENTATION 0",
		"#define FAULT_PYTHON_PRODUCT " + quoted(str(pyproduct)),
		"#define FAULT_CONTEXT_NAME " + quoted(f.__name__),
		"#define FACTOR_SYSTEM " + quoted(system),
		"#define FACTOR_PYTHON " + quoted(architecture),
		"#define FACTOR_ARCHITECTURE " + quoted(host),
	])

def python_runtime():
	import sys
	prefix = sys.prefix
	v = '.'.join(map(str, sys.version_info[:2]))
	abi = sys.abiflags

	return '\n'.join([
		prefix + '/lib' + '//library',
		'python' + v,
	])

def python_interfaces():
	import sys
	prefix = sys.prefix
	v = '.'.join(map(str, sys.version_info[:2]))
	abi = sys.abiflags
	include = prefix + '/include'

	return '\n'.join([
		include + '//interfaces',
		'python' + v,
	])

def python_tool():
	from os.path import dirname as d
	intpath = d(d(d(d(__file__)))).replace("\"", "\\\"")

	return '\n'.join([
		"#include <fault/python/bind.h>",
		"#define TARGET_MODULE \"fault.system.tool\"",
		"#define EXECUTION_FACTOR_PATH FACTOR_PATH_STRING(F_PRODUCT_PATH) \\",
		"\tFACTOR_PATH_STRING(\"" + intpath + "\")",
		"#define FAULT_PYTHON_CONTROL_IMPORTS \\",
		"\tIMPORT(\"fault.context.execute\") \\",
		"\tIMPORT(\"system.context.execute\")",
		"#include <fault/python/execute.h>",
	])


def execute_python_image():
	return '\n'.join([
		"#include <fault/python/bind.h>",
		"#ifndef EXECUTED_FACTOR",
		"\t#define EXECUTED_FACTOR \"fault.system.execute\"",
		"\t#define ARGUMENT_COUNT 2",
		"\t#define ARGUMENTS ARGUMENT(\"-d\") ARGUMENT(\"--\")",
		"#endif",
		"#define TARGET_MODULE EXECUTED_FACTOR",
		"#include <fault/python/execute.h>",
	])


def python(context, psystem, parch, harch, factor='type', name='python'):
	python_cc = getsource(machines_project, name)
	variants = form_variants(psystem, parch, modes=['executable', 'delineation'])
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
		mksole('runtime', systemreferences, python_runtime()),
		mksole('c-interfaces', systemreferences, python_interfaces()),
		mksole('c-fault', factorreferences, 'http://fault.io/integration/machines/include'),
	], [
		mkset('include', metasources, (), [
			('fault/python/bind.h', python_bind(psystem, parch, harch))
		]),
		mkset('fault-tool', systemexecutable,
			('.include', '.c-fault', '.c-interfaces', '.runtime'), [
			('main.c', python_tool()),
		]),
	]

def mkctx(info, formats, product, context, soles=[]):
	route = (product/context/'context').fs_alloc()
	return (factory.Parameters.define(info, formats, sets=[], soles=soles), route)

def mkproject(info, product, context, project, soles, sets=[]):
	route = (product/context/project).fs_alloc()
	return (factory.Parameters.define(info, vformats, sets=sets, soles=soles), route)

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

def form_meter_type():
	common = comment("Process intercepted metrics and identity forms.")
	common += define('[factor-type]',
		('', 'http://if.fault.io/factors/meter'),
	) + '\n'

	common += define('Translate',
		('cc-mode-metrics', '.measure-source -stdio .adapters'),
		('cc-mode-identity', '.identify-source -stdio .adapters'),
		('!', '.form-error -error-context .adapters'),
	) + '\n'

	common += define('Render',
		('cc-mode-metrics', '.aggregate-metrics -metrics-join .adapters'),
		('cc-mode-identity', '.form-identity -identity-join .adapters'),
		('!', '.form-error -error-context .adapters'),
	) + '\n'

	return common

def meter(context):
	return [
		fx('form-error', 'python', '.string', 'exit(1)'),
		fx('measure-source', 'python', 'system.metrics.measure', 'source'),
		fx('aggregate-metrics', 'python', 'system.metrics.aggregate'),
		fx('identify-source', 'python', 'system.tools.identify', 'source', '-'),
		fx('form-identity', 'python', 'system.tools.identify', 'index'),

		mksole('adapters', vtype,
			define('-telemetry',
				('if-metrics', '[telemetry-directory]'),
				('!', '-'),
			) + \
			constant('-stdio',
				'"measure-source-file" input output',
			) + \
			constant('-error-context',
				'"unconditional-failure" - -',
				'[factor]',
				'[cc-mode]',
			) + \
			constant('-metrics-join',
				'"aggregate-metrics" - -',
				'[factor-image] [work-directory]',
				'[-telemetry]',
				'[project-path] [factor-relative-path]',
				'[units]',
			) + \
			constant('-identity-join',
				'"combine-identities" - -',
				'[factor-image]',
				'[units]',
			)
		),
		mksole('type', vtype, form_meter_type()),
		mksole('variants', vtype, constant('[modes]',
			'metrics', 'identity',
		)),
	]

def text(context, factor='type', name='text.cc'):
	text_cc_vectors = getsource(machines_project, name)
	variants = form_variants('void', 'json', modes=['delineation'])
	txtcc = query.dispatched('text-cc')

	return [
		mksole('ft-text-cc', 'vector.system', txtcc),
		mksole('text-delineate-1', vtype, text_cc_vectors.fs_load()),
		mksole('variants', vtype, variants),
	]

def form_meta_type():
	common = comment("Process intercepted metrics and identity forms.")
	common += define('[factor-type]',
		('', 'http://if.fault.io/factors/meta'),
	) + '\n'
	common += define('[integration-type]',
		('', 'chapter'),
	) + '\n'

	common += define('Translate',
		('cc-mode-delineation', '.ft-text-cc -parse-text-1 .text-delineate-1'),
	) + '\n'

	common += define('Render',
		('cc-mode-delineation', '.ft-text-cc -store-chapter-1 .text-delineate-1'),
	) + '\n'

	return common

def meta(context):
	return text(context) + [
		mksole('projections', vtype,
			constant('host', 'http://if.fault.io/factors/system') + \
			constant('python', 'http://if.fault.io/factors/python') + \
			constant('meta', 'http://if.fault.io/factors/meta') + \
			constant('text', 'http://if.fault.io/factors/text')
		),
		mksole('intercepts', vtype,
			constant('metrics', 'meter', '.', 'executable') + \
			constant('identity', 'meter', '.', 'executable') + \
			constant('delineation', '.', 'delineated', '.')
		),
		mksole('type', vtype, form_meta_type()),
	]

def execution_project(context, system, python):
	"""
	# Construct the execution project containing system.executable factors
	# providing system access to the configured machines.
	"""

	return [], [
		mkset(python, systemexecutable,
			('..python.include', '..python.c-fault', '..python.c-interfaces', '..python.runtime'), [
			('main.c', execute_python_image()),
		]),
	]

def mkvectors(context, route, name='machines'):
	soles = [
		mksole('usr-cc', 'vector.system', system('/usr/bin/cc')),
		mksole('usr-ar', 'vector.system', system('/usr/bin/ar')),
		mksole('bin-cp', 'vector.system', system('/bin/cp')),
		mksole('bin-ln', 'vector.system', system('/bin/ln')),
	]

	# Vectors Context
	pi = mkinfo(context + '.context', name)
	pj = mkctx(pi, formats, route, context, soles)
	factory.instantiate(*pj)

	hsys, harch = identity.root_execution_context()
	hlink = system_select_linker(hsys)

	# Meta. projections, intercepts, and error cases.
	pi = mkinfo(context + '.meta', 'meta')
	pj = mkproject(pi, route, context, 'meta', meta(context))
	factory.instantiate(*pj)

	# Meter. Source measurements.
	pi = mkinfo(context + '.meter', 'meter')
	pj = mkproject(pi, route, context, 'meter', meter(context))
	factory.instantiate(*pj)

	# Host Machine
	pi = mkinfo(context + '.host', 'host')
	pj = mkproject(pi, route, context, 'host', *host(route, context, hlink, hsys, harch))
	factory.instantiate(*pj)

	# Python Machine
	psys, parch = identity.python_execution_context()
	pi = mkinfo(context + '.python', 'python')
	pj = mkproject(pi, route, context, 'python', *python(context, psys, parch, harch))
	factory.instantiate(*pj)

	# Machine execution factors
	pi = mkinfo(context + '.execution', 'execution')
	hid = hsys + '-' + harch
	pid = psys + '-' + parch
	pj = mkproject(pi, route, context, 'execution', *execution_project(context, hid, pid))
	factory.instantiate(*pj)

def mkcc(route, context_name='machines'):
	mkvectors(context_name, route)
	iproduct(route, [x.route for x in factors.context.product_sequence])
