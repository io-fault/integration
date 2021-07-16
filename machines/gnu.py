"""
# Command constructors for ELF systems.

# This only contains constructors for GNU ld as it was the ubiquitous implementation
# for ELF systems.
"""
from fault.context import tools

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
		build, adapter, output, inputs,
		filepath=str,

		pie_flag='-pie',
		verbose_flag='-v',
		link_flag='-l',
		libdir_flag='-L',
		rpath_flag='-rpath',
		soname_flag='-soname',
		output_flag='-o',
		type_map={
			'http://if.fault.io/factors/system.executable': '-pie',
			'http://if.fault.io/factors/system.library': '-shared',
			'http://if.fault.io/factors/system.extension': '-shared',
			'http://if.fault.io/factors/system.partial': '-r',
		},
		allow_runpath='--enable-new-dtags',
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
	f_domain = factor.domain
	intention = build.variants['intention']

	command = [None]
	command.append(verbose_flag)

	loutput_type = type_map[f_type]
	if loutput_type:
		command.append(loutput_type)

	if f_type == 'executable':
		command.append(pie_flag)
	elif f_type == 'extension':
		command.append('--unresolved-symbols=ignore-all')

	# Using '-l:' to make sure image name is identified.
	libs = list(build.select('http://if.fault.io/factors/system.library#image'))

	dirs = [x.container for x in libs if not isinstance(x, str) and x.context != files.root]
	command.extend([libdir_flag+filepath(x) for x in tools.unique(dirs, None)])
	command.extend([link_flag+libflag(x) for x in libs])

	link_parameters = [link_flag + y for y in set([x.name for x in libs])]

	command.append(allow_runpath)

	command.extend(map(filepath, inputs))
	command.extend(libdirs)
	command.append('-(')
	command.extend(link_parameters)
	command.append('-)')

	command.extend((output_flag, output))
	return command
