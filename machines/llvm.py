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
	'-U': ('field-replace', True, 'update-build'),
	'-u': ('field-replace', False, 'update-build'),
}

required = {
	'-x': ('field-replace', 'target-directory'),
	'-X': ('field-replace', 'construction-context'),

	'-C': ('field-replace', 'cmake-path'),
	'-M': ('field-replace', 'gmake-path'),
	'--llvm-config': ('field-replace', 'llvm-path'),
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

def declare(ccv, ipq):
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
				('delineate.c', "#include <fault/llvm/delineate.c>\n")
			]),
		('ipquery',
			'http://if.fault.io/factors/system.executable',
			['.fault', '.libllvm-is', '.libllvm-if'], [
				('ipquery.cc', "#include <fault/llvm/ipquery.cc>\n"),
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

def mksources(directory):
	with (directory/'delineate.c').fs_open('w') as f:
		f.write("#include <fault/llvm/delineate.c>")
	with (directory/'ipquery.cc').fs_open('w') as f:
		f.write("#include <fault/llvm/ipquery.cc>")

def icmake(route, ccv, ccf, include):
	"""
	# Instantiate as a cmake project.

	# Currently preferred over &factors as integrating with LLVM's
	# configuration is slightly easier due to the current limits
	# of Construction Contexts.
	"""

	route.fs_alloc().fs_mkdir()
	(route/'include').fs_link_absolute(include)
	mksources(route)

	with (route/'CMakeLists.txt').fs_open('w') as f:
		f.write('set(LLVM_CXX_FLAGS "' + ccf + '")\n')
		f.write("set(CMAKE_CXX_STANDARD " + ccv + ")\n")
		f.write(cmake_source)

def ifactors(route, ccv, ipqd):
	"""
	# Instantiate as factors.
	"""

	p = declare(ccv, ipqd)
	factory.instantiate(p, route)

def link_tools(ctx, llvm_bindir, itools):
	ctxllvm = (ctx/'.llvm').fs_mkdir()
	cipq = (ctxllvm/'clang-ipquery').fs_link_absolute(itools/'clang-ipquery').fs_type()
	cdel = (ctxllvm/'clang-delineate').fs_link_absolute(itools/'clang-delineate').fs_type()
	pdt = (ctxllvm/'pd-tool').fs_link_absolute(llvm_bindir/'llvm-profdata').fs_type()

	# Used by delineate to collect any coverable syntax areas.
	ctxtools = (ctx/'.coverage-tools').fs_mkdir()
	(ctxtools/'llvm').fs_link_relative(ctxllvm/'clang-ipquery')

	return 'void' not in set([cipq, cdel]), pdt != 'void'

def find(pwd, *names):
	for exe in names:
		if exe[:1] in './':
			return pwd@exe
		else:
			for fullpath in executables(exe):
				return fullpath

def system(exe, *argv):
	xpath = str(exe)
	args = [xpath] + list(argv)
	print('-> ' + ' '.join(args), flush=True)
	ki = execution.KInvocation(xpath, args)
	return execution.perform(ki)

def configure(pwd, restricted, required, argv):
	config = {
		'target-directory': None,
		'update-build': True, # build and replace by default.
		'instantiate-factors': False, # cmake project by default.
		'instantiate-only': False, # Build by default.
		'link-only': False,
		'cmake-path': 'cmake',
		'gmake-path': 'gmake',
		'construction-context': os.environ.get('FCC') or None,
		'llvm-path': 'llvm-config',
		'target-route': None,
		'pwd': pwd,
	}

	oeg = recognition.legacy(restricted, required, argv)

	# llvm-config
	remainder = recognition.merge(config, oeg)
	if remainder:
		llvm_path = config['llvm-path'] = remainder[0]
	else:
		llvm_path = config['llvm-path']

	# Default option; the llvm-config path.
	if llvm_path[:1] in './':
		# If absolute or dot-leading relative, use pwd.
		config['llvm-config'] = pwd@llvm_path
	else:
		# Otherwise, scan PATH for the executable.
		for exe in executables(llvm_path):
			config['llvm-config'] = exe
			break
		else:
			print('ERROR: ' + repr(llvm_path) + " not found in path.")
			raise SystemExit(1)

	# -x option.
	if config['target-directory'] is not None:
		config['target-route'] = pwd@config['target-directory']
	else:
		config['target-route'] = (pwd@config['construction-context'])@'.llvm/build'

	return config

def main(inv:process.Invocation) -> process.Exit:
	pwd = process.fs_pwd()
	config = configure(pwd, restricted, required, inv.argv)
	update_build = config['update-build']

	# Get the libraries and interfaces needed out of &query
	config['llvm-config'].fs_require('x') # --llvm-config
	v, src, merge, export, bindir, ipqd = instrumentation(config['llvm-config'])

	bindir = files.root@bindir.strip()
	if (bindir/'llvm-config').fs_type() != 'void':
		# Prefer a more canonical path if it is present.
		config['llvm-config'] = bindir/'llvm-config'

	ccv = ipqd['cc-version'].strip("c+")
	ccf = ipqd['cc-flags'].split('std=' + ipqd['cc-version'])[1].strip()

	route = config['target-route']
	llvm = config['llvm-config']
	print('Selected LLVM installation(--llvm-config): ' + str(llvm))

	# Identify ipquery.cc, delineate.c
	factors.load()
	factors.configure()
	pd, pj, fp = factors.split(__name__)
	llvm_d = fp.container
	llvm_factors = {k[0]: v[1] for k, v in pj.select(llvm_d)}

	# Include path.
	mpd, mpj, ifp = factors.split(pj.factor.container + ['machines', 'include'])
	inc = mpd.route // mpj.factor // ifp

	# Link tools to construction context.
	links_exist = None
	pd_tool_exists = None
	cctx = config['construction-context']
	if cctx:
		print('Linking LLVM tools to construction context(-X): ' + str(cctx))
		links_exist, pd_tool_exists = link_tools(pwd@cctx, bindir, route)
		if not pd_tool_exists:
			print('WARNING: llvm-profdata tool does not exist; coverage data will not be processed.')

		if config['link-only']:
			return inv.exit(0)
	else:
		if config['link-only']:
			print('ERROR: no construction context (-X) referenced for link only setup.')
			return inv.exit(1)
		else:
			print('NOTE: no construction context referenced, no links will be created.')

	if update_build:
		# Default is to update whatever is instantiated.
		pass
	else:
		# If the configured links exist, a build is already present.
		if links_exist:
			print('NOTE: Using existing build.')
			return inv.exit(0)
		else:
			print('NOTE: Links do not exist, updating build.')

	if not config['instantiate-factors']:
		icmake(route, ccv, ccf, inc)
	else:
		ifactors(route, ccv, ipqd)

	if config['instantiate-only']:
		return inv.exit(0)

	print('Selected target directory(-x): ' + str(route))
	os.chdir(str(route))
	os.environ['PWD'] = str(route)
	userpwd = pwd
	pwd = route

	# Find make tools.
	cmake = find(pwd, config['cmake-path'])
	print('Using cmake: ' + str(cmake))
	gmake = find(pwd, config['gmake-path'], 'make')
	print('Using gmake: ' + str(gmake))

	# Perform build.
	status = system(cmake, '.')
	if status != 0:
		inv.exit(status)
	status = system(gmake)
	if status != 0:
		inv.exit(status)

	return inv.exit(0)
