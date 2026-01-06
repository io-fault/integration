"""
# Instantiate the `fault-llvm` tools project into a target directory.
"""
import sys
import os.path
import itertools

from fault.vector import recognition

from fault.system import files
from fault.system import process
from fault.system import execution
from fault.system.factors import context as factors
from fault.system.query import executables

from fault.project import system as lsf
from fault.project import factory

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

def split_config_output(flag, output):
	return set(map(str.strip, output.split(flag)))

def profile_library(prefix, architecture):
	profile_libs = [x for x in prefix.fs_iterfiles('data') if 'profile' in x.identifier]

	if len(profile_libs) == 1:
		# Presume target of interest.
		return profile_libs[0]
	else:
		# Scan for library with matching architecture.
		for x in profile_libs:
			if architecture in x.identifier:
				return x

	return None

def compiler_libraries(compiler, prefix, version, executable, target):
	"""
	# Attempt to select the compiler libraries directory containing compiler support
	# libraries for profiling, sanity, and runtime.
	"""
	lib = prefix + ['lib', 'clang', version, 'lib']
	syslib = lib / 'darwin' # Naturally, not always consistent.
	if syslib.fs_type() != 'void':
		return syslib
	syslib = prefix / 'lib' / 'darwin'
	if syslib.fs_type() != 'void':
		return syslib

def parse_clang_version_1(string):
	"""
	# clang --version parser.
	"""

	lines = string.split('\n')
	version_line = lines[0].strip()

	cctype, version_spec = version_line.split(' version ')
	try:
		version_info, release = version_spec.split('(', 1)
	except ValueError:
		# 9.0 from FreeBSD ports does not appear to have a "release" tag.
		version_info = version_spec
		release = ''

	release = release.strip('()')
	version = version_info.strip()
	version_info = version.split('.', 3)

	# Extract the default target from the compiler.
	target = None
	for line in lines:
		if line.startswith('Target:'):
			target = line
			target = target.split(':', 1)
			target = target[1].strip()
			break
	else:
		target = None

	return cctype, release, version, version_info, target

def parse_clang_directories_1(string):
	"""
	# Parse -print-search-dirs output.
	"""
	search_dirs_data = [x.split(':', 1) for x in string.split('\n') if x]

	return dict([
		(k.strip(' =:').lower(), list((x.strip(' =') for x in v.split(':'))))
		for k, v in search_dirs_data
	])

def parse_clang_standards_1(string):
	"""
	# After retrieving a list from standard error, extract as much information as possible.
	"""
	lines = string.split('\n')
	# first line should start with error:
	assert lines[0].strip().startswith('error:')

	return {
		x.split("'", 3)[1]: x.rsplit("'", 3)[2]
		for x in map(str.strip, lines[1:])
		if x.strip()
	}

def clang(executable, type='executable', libdir='lib'):
	"""
	# Extract information from the given clang &executable.
	"""
	warnings = []
	root = files.Path.from_absolute('/')
	cc_route = files.Path.from_absolute(executable)

	# gather compiler information.
	x = execution.prepare(type, executable, ['--version'])
	i = execution.KInvocation(*x)
	pid, exitcode, data = execution.dereference(i)
	data = data.decode('utf-8')
	cctype, release, version, version_info, target = parse_clang_version_1(data)

	# Analyze the library search directories.
	# Primarily interested in finding the crt*.o files for linkage.
	x = execution.prepare(type, executable, ['-print-search-dirs'])
	i = execution.KInvocation(*x)
	pid, exitcode, sdd = execution.dereference(i)
	search_dirs_data = parse_clang_directories_1(sdd.decode('utf-8'))

	ccprefix = files.Path.from_absolute(search_dirs_data['programs'][0])

	if target is None:
		warnings.append(('target', 'no target field available from --version output'))
		arch = None
	else:
		# First field of the target string.
		arch = target[:target.find('-')]

	cclib = compiler_libraries('clang', ccprefix, '.'.join(version_info), cc_route, target)
	builtins = None
	if cclib is None:
		cclib = files.Path.from_relative(root, search_dirs_data['libraries'][0])
		cclib = cclib / libdir / sys.platform

	if sys.platform in {'darwin'}:
		builtins = cclib / 'libclang_rt.osx.a'
	else:
		cclibs = [x for x in cclib.fs_iterfiles('data') if 'builtins' in x.identifier]

		if len(cclibs) == 1:
			builtins = str(cclibs[0])
		else:
			# Scan for library with matching architecture.
			for x, a in itertools.product(cclibs, [arch]):
				if a in x.identifier:
					builtins = str(x)
					break
			else:
				# clang, but no libclang_rt.
				builtins = None

	libdirs = [
		files.Path.from_relative(root, str(x).strip('/'))
		for x in search_dirs_data['libraries']
	]

	standards = {}
	for l in ('c', 'c++'):
		x = execution.prepare(type, executable, [
			'-x', l, '-std=void.abczyx.1', '-c', '/dev/null', '-o', '/dev/null',
		])
		pid, exitcode, stderr = execution.effect(execution.KInvocation(*x))
		standards[l] = parse_clang_standards_1(stderr.decode('utf-8'))

	clang = {
		'implementation': cctype.strip().replace(' ', '-').lower(),
		'libraries': str(cclib),
		'version': tuple(map(int, version_info)),
		'release': release,
		'command': str(cc_route),
		'runtime': str(builtins) if builtins else None,
		'standards': standards,
	}

	return clang

def instrumentation(llvm_config_path, merge_path=None, export_path=None, type='executable'):
	"""
	# Identify instrumentation related commands and libraries for making extraction tools.
	"""
	srcpath = str(llvm_config_path)
	v_pipe = ['--version']
	libs_pipe = ['profiledata', '--libs']
	syslibs_pipe = ['profiledata', '--system-libs']
	covlibs_pipe = ['coverage', '--libs']
	incs_pipe = ['--includedir']
	libdir_pipe = ['--libdir']
	rtti_pipe = ['--has-rtti']
	cxx_pipe = ['--cxxflags']
	bin_pipe = ['--bindir']

	po = lambda x: execution.dereference(execution.KInvocation(*execution.prepare(type, srcpath, x)))
	outs = [
		po([srcpath, '--prefix']),
		po(v_pipe),
		po(libs_pipe),
		po(syslibs_pipe),
		po(covlibs_pipe),
		po(libdir_pipe),
		po(incs_pipe),
		po(rtti_pipe),
		po(cxx_pipe),
		po(bin_pipe),
	]

	prefix, v, libs, syslibs, covlibs, libdirs, incdirs, rtti, cxx, bindir = [x[-1].decode('utf-8') for x in outs]

	libs = split_config_output('-l', libs)
	libs.discard('')
	libs.add('c++')

	covlibs = split_config_output('-l', covlibs)
	covlibs.discard('')

	syslibs = split_config_output('-l', syslibs)
	syslibs.discard('')
	syslibs.add('c++')

	libdirs = split_config_output('-L', libdirs)
	libdirs.discard('')
	dir, *reset = libdirs

	incdirs = split_config_output('-I', incdirs)
	incdirs.discard('')

	if rtti.lower() in {'yes', 'true', 'on'}:
		rtti = True
	else:
		rtti = False

	ccv = cxx[cxx.find('-std='):].split(maxsplit=1)[0].split('=')[1]

	if not merge_path:
		merge_path = llvm_config_path.container/'llvm-profdata'
	if not export_path:
		export_path = llvm_config_path.container/'llvm-cov'

	fp = {
		'merge-command': str(merge_path),
		'include': incdirs,
		'library-directories': libdirs,
		'coverage-libraries': covlibs,
		'system-libraries': syslibs,
		'cc-version': ccv,
		'cc-flags': cxx
	}

	return v.strip(), srcpath, str(merge_path), str(export_path), bindir, fp

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
	v, src, merge, export, bindir, ipqd = instrumentation(files.root@llvmconfig)
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
