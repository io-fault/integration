"""
# Command constructors for Apple (macOS) hosts.
"""
from fault.context import tools
from fault.system import files

def debug_isolate(target):
	dtarget = target + '.dSYM'
	return dtarget, [
		('dsymutil', target, '-o', dtarget)
	]

type_map = {
	'executable': '-execute',
	'library': '-dylib',
	'extension': '-bundle',
	'partial': '-r',
}

def libflag(x):
	if isinstance(x, str):
		return x
	else:
		if x.context is not files.root:
			return ':'+x.identifier
		else:
			return x.identifier

def macos_link_editor(
		build, adapter, output, inputs,
		filepath=str,

		minimum_macos='10.13.0',
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
		lto_preserve_exports='-export_dynamic',
		platform_version_flag='-macosx_version_min',
	):
	"""
	# Command constructor for Mach-O link editor provided on Apple MacOS X systems.
	"""
	factor = build.factor
	f_type = factor.type.factor.identifier

	sysarch = build.mechanism.descriptor['architecture']

	command = [None, '-t', lto_preserve_exports, platform_version_flag, minimum_macos, '-arch', sysarch]

	intention = build.intention
	mech = build.mechanism.descriptor

	loutput_type = type_map[f_type]
	command.append(loutput_type)

	if f_type == 'executable':
		command.append(pie_flag)
	elif f_type == 'extension':
		command.extend(['-undefined', 'dynamic_lookup'])

	# SystemFactors
	dirs = list(build.select('http://if.fault.io/factors/system.directory#image'))
	command.extend([libdir_flag+filepath(x) for x in tools.unique(dirs, None)])

	# Using '-l:' to make sure image name is identified.
	libs = list(build.select('http://if.fault.io/factors/system.library#image'))

	dirs = [x.container for x in libs if not isinstance(x, str) and x.context != files.root]
	command.extend([libdir_flag+filepath(x) for x in tools.unique(dirs, None)])
	command.extend([link_flag+libflag(x) for x in libs])

	command.append(link_flag+'System')
	command.extend(inputs)

	command.extend((output_flag, filepath(output)))

	return command
