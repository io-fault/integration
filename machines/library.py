"""
# Command constructors.
"""
import typing

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
	'injections': '0',
	'instruments': '0',
	'debug': '0',
	'delineation': '0',
}

def standard_parameters(build):
	arch = build.mechanism.descriptor.get('architecture', None)
	if arch is not None:
		yield ('F_TARGET_ARCHITECTURE', arch)

	yield from [
		('F_SYSTEM', build.system),
		('F_INTENTION', build.context.intention),
		('F_FACTOR_DOMAIN', build.factor.domain),
		('F_FACTOR_TYPE', build.factor.type),
	]

	yield from build.parameters

def clang(
		build, adapter,
		o_type, output, i_type, inputs,
		options=(), # Direct option injection.
		verbose=True, # Enable verbose output.
		root=False, # Designates the input as a root.
		includes:typing.Sequence[str]=(),

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
		format_map = {
			'pic': '-fPIC',
			'pie': '-fPIE',
			'pdc': '-mdynamic-no-pic',
		},
		co_flag='-O',
		define_flag='-D',
		empty = {}
	):
	"""
	# Construct an argument sequence for a common compiler collection command.

	# &unix_compiler_collection is the interface for constructing compilation
	# commands for a compiler collection.
	"""

	f = build.factor
	ctx = build.context
	intention = ctx.intention

	lang = adapter.get('language', i_type)
	if lang.endswith('-header') and intention != 'fragment':
		inputs = ['/dev/null']
		lang = 'c'

	f_ctl = adapter.get('feature-control', empty).get(lang, empty)

	command = [None, compile_flag]
	if verbose:
		command.append(verbose_flag)

	# Add language flag if it's a compiler collection.
	if i_type is not None:
		command.extend((language_flag, lang))

	lang_standards = adapter['standards'].get(lang, ())
	pl_version = build.requirements.get(('language', 'standard'), None)
	if pl_version:
		pl_version, = pl_version
		stdname = pl_version.name
		if stdname in lang_standards:
			command.append(standard_flag + '=' + stdname)

	pl_features = ()
	for feature, (f_on, f_off) in f_ctl.items():
		if feature in pl_features:
			command.append(f_on)
		else:
			command.append(f_off)

	command.append(visibility) # Encourage use of SYMBOL() define.
	command.append(color)

	# -fPIC, -fPIE or nothing. -mdynamic-no-pic for MacOS "static".
	format_flags = format_map.get(o_type)
	if format_flags is not None:
		command.append(format_flags)
	else:
		if o_type is not None:
			# The selected output type did not have
			# a corresponding flag. Noting this
			# may illuminate an error.
			pass

	# Compiler optimization target: -O0, -O1, ..., -Ofast, -Os, -Oz
	co = optimizations[intention]
	command.append(co_flag + co)

	# Include debugging symbols unconditionally.
	# Filter or separate later.
	command.append(debug_flag)

	if 0:
		# TODO: incorporate overflow parameter
		# factor.txt files being limited means that there is no
		# way to specify the overflow type. source level control is actually
		# needed anyways, but it does not appear to be popular with compilers.
		overflow_spec = getattr(build.factor.module, 'overflow', None)
		if overflow_spec is not None:
			command.append(overflow_control[overflow_spec])

	command.extend(adapter.get('options', ()))
	command.extend(options)

	# Include Directories; -I option.
	included = build.required('source', 'library')
	command.extend([id_flag + str(x) for x, xf in included])

	# -D defines.
	sp = [
		define_flag + '='.join(x)
		for x in standard_parameters(build)
		if x[1] is not None
	]
	command.extend(sp)

	# -U undefines.
	spo = ['-U' + x[0] for x in standard_parameters(build) if x[1] is None]
	command.extend(spo)

	# -include files. Forced inclusion.
	for x in includes:
		command.extend((si_flag, x))

	# finally, the output file and the inputs as the remainder.
	command.extend((output_flag, output))
	command.extend(inputs)

	return command
