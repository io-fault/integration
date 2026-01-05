"""
# Instantiate the `fault-llvm` tools project into a target directory.
"""
import os.path

from fault.vector import recognition

from fault.system import files
from fault.system import process
from fault.system import execution
from fault.system.factors import context as factors
from fault.system.query import executables

from fault.project import system as lsf
from fault.project import factory

from . import query

restricted = {
	'-l': ('field-replace', True, 'link-only'),
	'-L': ('field-replace', False, 'link-only'),
	'-i': ('field-replace', True, 'instantiate-only'),
	'-I': ('field-replace', False, 'instantiate-only'),
	'-f': ('field-replace', True, 'instantiate-factors'),
	'-F': ('field-replace', False, 'instantiate-factors'),
}

required = {
	'-x': ('field-replace', 'target-directory'),
	'-X': ('field-replace', 'construction-context'),

	'-C': ('field-replace', 'cmake-path'),
	'-M': ('field-replace', 'gmake-path'),
}

def formats(ccv):
	return {
		'http://if.fault.io/factors/system': [
			('elements', 'cc', '20' + str(ccv), 'c++'),
			('elements', 'c', '2011', 'c'),
			('void', 'h', 'header', 'c'),
			('references', 'sr', 'lines', 'text'),
		],
		'http://if.fault.io/factors/python': [
			('module', 'py', 'psf-v3', 'python'),
			('interface', 'pyi', 'psf-v3', 'python'),
		],
		'http://if.fault.io/factors/meta': [
			('references', 'fr', 'lines', 'text'),
		],
	}

info = lsf.types.Information(
	identifier = '://fault.metrics/llvm',
	name = 'llvm',
	authority = 'fault.io',
	contact = "http://fault.io/critical"
)

fr = lsf.types.factor@'meta.references'
sr = lsf.types.factor@'system.references'

def declare(ccv, ipq, deline):
	includes, = ipq['include']
	includes = files.root@includes
	libdirs = sorted(list(ipq['library-directories']))

	soles = [
		('fault', fr, '\n'.join([
			'http://fault.io/integration/machines/include',
		])),
		('libclang-is', sr, '\n'.join(
			libdirs + ['clang', ''],
		)),
		('libllvm-is', sr, '\n'.join(
			libdirs + \
			sorted(list(ipq['coverage-libraries'])) + \
			sorted(list(ipq['system-libraries'])) + ['']
		)),
	]

	sets = [
		('libclang-if',
			'http://if.fault.io/factors/meta.sources', (), [
				('clang-c', (includes/'clang-c')),
			]),
		('libllvm-if',
			'http://if.fault.io/factors/meta.sources', (), [
				('llvm', (includes/'llvm')),
				('llvm-c', (includes/'llvm-c')),
			]),

		('delineate',
			'http://if.fault.io/factors/system.executable',
			['.fault', '.libclang-is', '.libclang-if'], [
				(x.identifier, x) for x in deline
			]),
		('ipquery',
			'http://if.fault.io/factors/system.executable',
			['.fault', '.libllvm-is', '.libllvm-if'], [
				('ipquery.cc', ipq['source']),
			]),
	]

	return factory.Parameters.define(info, formats(ccv), sets=sets, soles=soles)

cmake_source = \
	"""
	cmake_minimum_required(VERSION 3.20.0)
	project(fault-llvm-tools)

	find_package(LLVM REQUIRED CONFIG)
	message(STATUS "LLVM ${LLVM_PACKAGE_VERSION}: ${LLVM_DIR}/LLVMConfig.cmake")

	find_library(CLANG_LIB REQUIRED NAMES clang libclang HINTS ${LIBCLANG_PATH} ${LLVM_LIBRARY_DIRS})
	message(STATUS "libclang: ${CLANG_LIB}")

	# set(CMAKE_CXX_STANDARD 17)
	set(CMAKE_CXX_STANDARD_REQUIRED on)
	set(CMAKE_CXX_FLAGS "-DFV_INTENTION=optimal ${LLVM_CXX_FLAGS} ${CMAKE_CXX_FLAGS}")
	set(CMAKE_C_FLAGS "-DFV_INTENTION=optimal ${CMAKE_C_FLAGS}")

	include_directories(${LLVM_INCLUDE_DIRS} include)
	separate_arguments(LLVM_DEFINITIONS_LIST NATIVE_COMMAND ${LLVM_DEFINITIONS})
	add_definitions(${LLVM_DEFINITIONS_LIST})

	add_executable(clang-ipquery ipquery.cc)
	llvm_map_components_to_libnames(ipqlibs coverage)
	target_link_libraries(clang-ipquery ${ipqlibs})

	add_executable(clang-delineate delineate.c)
	target_link_libraries(clang-delineate PRIVATE ${CLANG_LIB})
	"""

def icmake(route, ccv, ccf, include, delineate, ipquery):
	"""
	# Instantiate as a cmake project.

	# Currently preferred over &factors as integrating with LLVM's
	# configuration is slightly easier due to the current limits
	# of Construction Contexts.
	"""

	route.fs_alloc().fs_mkdir()
	(route/'include').fs_link_absolute(include)
	(route/'delineate.c').fs_link_absolute(delineate)
	(route/'ipquery.cc').fs_link_absolute(ipquery)

	with (route/'CMakeLists.txt').fs_open('w') as f:
		f.write('set(LLVM_CXX_FLAGS "' + ccf + '")\n')
		f.write("set(CMAKE_CXX_STANDARD " + ccv + ")\n")
		f.write(cmake_source)

def ifactors(route, ccv, delineate_src, ipqd):
	"""
	# Instantiate as factors.
	"""

	p = declare(ccv, ipqd, (delineate_src,))
	factory.instantiate(p, route)

def link_tools(ctx, llvm_bindir, itools):
	ctxtools = (ctx/'.llvm')
	ctxtools.fs_mkdir()
	(ctxtools/'clang-ipquery').fs_link_absolute(itools/'clang-ipquery')
	(ctxtools/'clang-delineate').fs_link_absolute(itools/'clang-delineate')
	(ctxtools/'pd-tool').fs_link_absolute(llvm_bindir/'llvm-profdata')

def system(exe, *argv):
	if exe[:1] in './':
		xpath = pwd@exe
	else:
		xpath, = executables(exe)

	xpath = str(xpath)
	args = [xpath] + list(argv)
	print('-> ' + ' '.join(args), flush=True)
	ki = execution.KInvocation(xpath, args)
	return execution.perform(ki)

def configure(restricted, required, argv):
	config = {
		'target-directory': None,
		'instantiate-factors': False, # cmake project by default.
		'instantiate-only': False, # Build by default.
		'link-only': False,
		'cmake-path': 'cmake',
		'gmake-path': 'make',
		'construction-context': None,
	}
	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def main(inv:process.Invocation) -> process.Exit:
	pwd = process.fs_pwd()
	config, remainder = configure(restricted, required, inv.argv)

	target = config['target-directory']
	llvmconfig, = remainder
	if target is None:
		# Default to PREFIX/fault.
		route = (pwd@llvmconfig) ** 2 / 'fault'
	else:
		route = pwd@target

	# Identify ipquery.cc, delineate.c
	factors.load()
	factors.configure()
	pd, pj, fp = factors.split(__name__)
	llvm_d = fp.container
	llvm_factors = {k[0]: v[1] for k, v in pj.select(llvm_d)}

	# Include path.
	mpd, mpj, ifp = factors.split(pj.factor.container + ['machines', 'include'])
	inc = mpd.route // mpj.factor // ifp

	# Get the libraries and interfaces needed out of &query
	v, src, merge, export, bindir, ipqd = query.instrumentation(files.root@llvmconfig)
	ccv = ipqd['cc-version'].strip("c+")
	ccf = ipqd['cc-flags'].split('std=' + ipqd['cc-version'])[1].strip()

	ipquery_src = ipqd['source'] = llvm_factors[llvm_d/'ipquery'][0][1]
	delineate_src = llvm_factors[llvm_d/'delineate'][0][1]

	# Link tools to construction context.
	cctx = config['construction-context']
	if cctx:
		print('Linking LLVM tools to construction context: ' + str(cctx))
		link_tools(pwd@cctx, files.root@(bindir.strip()), route)

		if config['link-only']:
			return inv.exit(0)
	else:
		if config['link-only']:
			print('ERROR: no construction context referenced for link only setup.')
			return inv.exit(1)
		else:
			print('NOTE: no construction context referenced, no links will be created.')

	if not config['instantiate-factors']:
		icmake(route, ccv, ccf, inc, delineate_src, ipqd['source'])
	else:
		ifactors(route, ccv, delineate_src, ipqd)

	if config['instantiate-only']:
		return inv.exit(0)

	os.chdir(str(route))
	os.environ['PWD'] = str(route)
	userpwd = pwd
	pwd = route

	# Perform build.
	status = system(config['cmake-path'], '.')
	if status != 0:
		inv.exit(status)
	status = system(config['gmake-path'])
	if status != 0:
		inv.exit(status)
