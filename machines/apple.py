"""
# Command constructors for apple hosts.
"""

mach_objects = {
	'executable': '.exe',
	'library': '.dylib',
	'extension': '.dylib',
	'partial': '.fo',
	None: '.so',
}

def macos_link_editor(
		transform_mechanisms,
		build, adapter, o_type, output, i_type, inputs,
		partials, libraries,
		filepath=str,

		pie_flag='-pie',
		libdir_flag='-L',
		rpath_flag='-rpath',
		output_flag='-o',
		link_flag='-l',
		ref_flags={
			'weak': '-weak-l',
			'lazy': '-lazy-l',
			'default': '-l',
		},
		type_map={
			'executable': '-execute',
			'library': '-dylib',
			'extension': '-bundle',
			'partial': '-r',
		},
		lto_preserve_exports='-export_dynamic',
		platform_version_flag='-macosx_version_min',
	):
	"""
	# Command constructor for Mach-O link editor provided on Apple MacOS X systems.
	"""
	assert build.factor.domain == 'system'
	factor = build.factor
	sysarch = build.mechanism.descriptor['architecture']

	command = [None, '-t', lto_preserve_exports, platform_version_flag, '10.13.0', '-arch', sysarch]

	intention = build.context.intention(None)
	format = build.variants['format']
	ftype = build.factor.type
	mech = build.mechanism.descriptor

	loutput_type = type_map[ftype]
	command.append(loutput_type)
	if ftype == 'executable':
		if format == 'pie':
			command.append(pie_flag)

	if factor.type == 'partial':
		# Fragments use a partial link.
		command.extend(inputs)
	else:
		libs = [f for f in build.references[(factor.domain, 'library')]]
		libs.sort(key=lambda x: (getattr(x, '_position', 0), x.name))

		dirs = (x.integral() for x in libs)
		command.extend([libdir_flag+filepath(x) for x in libc.unique(dirs, None)])

		support = mech['objects'][ftype][format]
		if support is not None:
			prefix, suffix = support
		else:
			prefix = suffix = ()

		command.extend(prefix)
		command.extend(inputs)

		command.extend([link_flag+x.name for x in libs])
		command.append(link_flag+'System')

		command.extend(suffix)

		# For each source transformation mechanism, extract the link time requirements
		# that are needed by the compiler. When building targets with mixed compilers,
		# each may have their own runtime dependency that needs to be fulfilled.
		resources = set()
		for xfmech in transform_mechanisms.values():
			for x in xfmech.get('resources').values():
				resources.add(x)

		command.extend(list(resources))

	command.extend((output_flag, filepath(output)))

	return command
