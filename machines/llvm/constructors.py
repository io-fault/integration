"""
# Command constructors.
"""
import itertools

overflow_control = {
	'wrap': '-fwrapv',
	'none': '-fstrict-overflow',
	'undefined': '-fno-strict-overflow',
}

dependency_options = (
	('exclude_system_dependencies', '-MM', True),
)

optimizations = {
	'optimal': '3',
	'coverage': '0',
	'profile': '3',
	'debug': '0',
	'delineation': '0',
}

def source_parameters(build):
	arch = build.mechanism.descriptor.get('architecture', None)
	if arch is not None:
		yield ('F_TARGET_ARCHITECTURE', arch)

	factorpath = str(build.factor.route)
	parts = factorpath.split('.')
	project = str(build.factor.project.factor)
	tail = factorpath[len(project)+1:].split('.')[1:]

	yield from [
		('FV_SYSTEM', build.system),
		('FV_ARCHITECTURE', build.architecture),
		('FV_INTENTION', build.intention),

		('F_SYSTEM', build.system),
		('F_INTENTION', build.intention),
		('F_FACTOR_TYPE', str(build.factor.type)),

		('FACTOR_SUBPATH', '.'.join(tail)),
		('FACTOR_PROJECT', project),
		('FACTOR_QNAME', factorpath),
		('FACTOR_BASENAME', parts[-1]),
		('FACTOR_PACKAGE', '.'.join(parts[:-1])),
	]

format_type_map = {
	'http://if.fault.io/factors/system.executable': '-fPIE',
}

def format_sp(define_flag, undef_flag, name, value):
	if not value:
		if value is None:
			return undef_flag + name
		else:
			return define_flag + name
	else:
		return define_flag + '='.join((name, value))

def clang(
		build, adapter, output, i_type, inputs, *,
		options=(), # Direct option injection.
		verbose=True, # Enable verbose output.
		root=False, # Designates the input as a root.
		includes=(),

		verbose_flag='-v',
		language_flag='-x',
		standard_flag='-std',
		visibility='-fvisibility=hidden',
		color='-fcolor-diagnostics',

		output_flag='-o',
		compile_flag='-c',
		sid_flag='-isystem',
		id_flag='-I', si_flag='-include',
		debug_flag='-g',
		co_flag='-O',
		define_flag='-D',
		undef_flag='-U',
		empty = {}
	):
	"""
	# Construct an argument sequence for a common compiler collection command.

	# &unix_compiler_collection is the interface for constructing compilation
	# commands for a compiler collection.
	"""

	f = build.factor
	ftyp = f.type
	intention = build.intention

	if i_type.dialect == 'header':
		if intention != 'delineation':
			inputs = ['/dev/null']
	else:
		if i_type.dialect:
			command.append(standard_flag + '=' + i_type.dialect)

	command = [None, compile_flag]
	if verbose:
		command.append(verbose_flag)

	# Add language flag if it's a compiler collection.
	command.extend((language_flag, i_type.language))

	pl_features = ()
	f_ctl = adapter.get('feature-control', empty)
	for feature, (f_on, f_off) in f_ctl.items():
		if feature in pl_features:
			command.append(f_on)
		else:
			command.append(f_off)

	command.append(visibility) # Encourage use of SYMBOL() define.
	command.append(color)

	# -fPIC, -fPIE
	format_flag = format_type_map.get(ftyp, '-fPIC')
	command.append(format_flag)

	# Compiler optimization target: -O0, -O1, ..., -Ofast, -Os, -Oz
	co = optimizations[intention]
	command.append(co_flag + co)

	# Include debugging symbols unconditionally.
	# Filter or separate later.
	command.append(debug_flag)

	command.extend(adapter.get('options', ()))
	command.extend(options)

	# Include Directories; -I option.
	included = build.select('http://if.fault.io/factors/lambda.sources#source-paths')
	command.extend([id_flag + str(x) for x in included])

	# Source Parameters
	params = build.select('http://if.fault.io/factors/lambda.control#parameters')
	command.extend([
		format_sp(define_flag, undef_flag, *x)
		for x in itertools.chain.from_iterable(params)
	])

	# -D defines.
	sp = [
		define_flag + '='.join(x)
		for x in source_parameters(build)
		if x[1] is not None
	]
	command.extend(sp)

	# -include files. Forced inclusion.
	for x in includes:
		command.extend((si_flag, x))

	# finally, the output file and the inputs as the remainder.
	command.extend((output_flag, output))
	command.extend(inputs)

	return command
