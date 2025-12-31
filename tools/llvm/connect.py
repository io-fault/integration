"""
# Instantiate the `fault-llvm` tools project into a target directory.
"""
import os.path

from fault.system import files
from fault.system import process
from fault.system.factors import context as factors

from fault.project import system as lsf
from fault.project import factory

from . import query

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

def ifactors(route, ccv, ipqd, llvm_d, llvm_factors):
	"""
	# Instantiate as factors.
	"""

	# Sources of the image factors.
	deline = (
		llvm_factors[llvm_d/'delineate'][0][1],
	)

	p = declare(ccv, ipqd, deline)
	factory.instantiate(p, route)

def main(inv:process.Invocation) -> process.Exit:
	target, llvmconfig = inv.args
	route = process.fs_pwd()@target

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
	v, src, merge, export, ipqd = query.instrumentation(files.root@llvmconfig)
	ipqd['source'] = llvm_factors[llvm_d/'ipquery'][0][1]
	ccv = ipqd['cc-version'].strip("c+")
	ccf = ipqd['cc-flags'].split('std=' + ipqd['cc-version'])[1].strip()

	# Currently, unconditional. Factors requires adjustments to the
	# Construction Context in order for successful compilation.
	if 'cmake':
		icmake(route, ccv, ccf, inc, llvm_factors[llvm_d/'delineate'][0][1], ipqd['source'])
	else:
		ifactors(route, ccv, ipqd, llvm_d, llvm_factors)
	return inv.exit(0)
