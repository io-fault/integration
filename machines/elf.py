"""
# Command constructors for ELF systems.

# This only contains constructors for GNU ld as it was the ubiquitous implementation
# for ELF systems.
"""

objects = {
	'executable': '.exe',
	'library': '.so',
	'extension': '.so',
	'partial': '.fo',
	None: '.so',
}

def debug_isolate(target, objcopy, strip):
	"""
	# Isolate debugging information from the target.
	"""
	debugfile = target + '.debug'

	return [
		(objcopy, '--only-keep-debug', target, debugfile),
		(strip, '--strip-debug', '--strip-unneeded', target),
		(objcopy, '--add-gnu-debuglink', target, debug),
	]

def gnu_link_editor(
		transform_mechanisms,
		build, adapter, o_type, output, i_type, inputs,
		partials, libraries, filepath=str,

		pie_flag='-pie',
		verbose_flag='-v',
		link_flag='-l',
		libdir_flag='-L',
		rpath_flag='-rpath',
		soname_flag='-soname',
		output_flag='-o',
		type_map={
			'executable': None,
			'library': '-shared',
			'extension': '-shared',
			'partial': '-r',
		},
		allow_runpath='--enable-new-dtags',
		use_static='-Bstatic',
		use_shared='-Bdynamic',
	):
	"""
	# Command constructor for the GNU link editor. For platforms other than Darwin and
	# Windows, this is often the default link editor.

	# Traditional link editors have an insane characteristic that forces the user to decide what
	# the appropriate order of archives are. The
	# (system/command)`lorder` command was apparently built long ago to alleviate this while
	# leaving the interface to (system/command)`ld` to be continually unforgiving.
	"""

	factor = build.factor
	f_type = factor.type
	intention = build.variants['intention']
	format = build.variants['format']
	mech = build.mechanism.descriptor

	command = [None]
	add = command.append
	iadd = command.extend
	add(verbose_flag)

	loutput_type = type_map[f_type] # failure indicates bad type parameter to libfactor.load()
	if loutput_type:
		add(loutput_type)

	if f_type == 'partial':
		# partial is an incremental link. Most options are irrelevant.
		command.extend(map(filepath, inputs))
	else:
		libs = [f for f in build.requirements[(factor.domain, 'library')]]
		libs.sort(key=lambda x: (getattr(x, '_position', 0), x.name))

		dirs = (x.integral() for x in libs)
		libdirs = [libdir_flag+filepath(x) for x in libc.unique(dirs, None)]

		link_parameters = [link_flag + y for y in set([x.name for x in libs])]

		if False:
			command.extend((soname_flag, sys['abi']))

		if allow_runpath:
			# Enable by default, but allow override.
			add(allow_runpath)

		prefix, suffix = mech['objects'][f_type][format]

		command.extend(prefix)
		command.extend(map(filepath, inputs))
		command.extend(libdirs)
		command.append('-(')
		command.extend(link_parameters)
		command.append('-lc')
		command.append('-)')

		resources = set()
		for xfmech in transform_mechanisms.values():
			for x in xfmech.get('resources').values():
				resources.add(x)

		command.extend(suffix)

	command.extend((output_flag, output))
	return command
