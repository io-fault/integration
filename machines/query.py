"""
# System queries for realizing extension and executable requirements.
"""
import subprocess
import os.path

def split_config_output(flag, output):
	return set(map(str.strip, output.split(flag)))

def profile_library(prefix, architecture):
	files = prefix.subnodes()[1]
	profile_libs = [x for x in files if 'profile' in x.identifier]

	if len(profile_libs) == 1:
		# Presume target of interest.
		return profile_libs[0]
	else:
		# Scan for library with matching architecture.
		for x in profile_libs:
			if architecture in x.identifier:
				return x

	return None

def instrumentation(llvm_config_path, merge_path=None, tool_name='llvm'):
	"""
	# Extract information necessary for compiling a Python extension using the LLVM
	# coverage tools for extracting counters from profile data.
	"""
	srcpath = str(llvm_config_path)
	libs_pipe = [srcpath, 'profiledata', '--libs']
	syslibs_pipe = [srcpath, 'profiledata', '--system-libs']
	covlibs_pipe = [srcpath, 'coverage', '--libs']
	incs_pipe = [srcpath, '--includedir']
	libdir_pipe = [srcpath, '--libdir']
	rtti_pipe = [srcpath, '--has-rtti']

	Popen = subprocess.Popen
	STDOUT = subprocess.STDOUT
	PIPE = subprocess.PIPE
	po = lambda x: Popen(x, stdin=None, stderr=PIPE, stdout=PIPE).communicate()

	outs = [
		po([srcpath, '--prefix']),
		po(libs_pipe),
		po(syslibs_pipe),
		po(covlibs_pipe),
		po(libdir_pipe),
		po(incs_pipe),
		po(rtti_pipe),
	]

	prefix, libs, syslibs, covlibs, libdirs, incdirs, rtti = [x[0].decode('utf-8') for x in outs]

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

	if not merge_path:
		merge_path = os.path.join(os.path.dirname(srcpath), 'llvm-profdata')

	fp = {
		'source': {
			'library': {
				x: {None} for x in incdirs
			},
			'parameters': {
				'MERGE_COMMAND': merge_path,
			},
		},
		'system': {
			'library': {
				dir: covlibs,
				None: syslibs,
			}
		},
	}

	refparams = {
		'source': srcpath,
		# Needed indirectly by dev.bin.measure to merge the raw profile data.
		'merge': merge_path,
		'factors': fp,
	}

	yield (tool_name+'/coverage', None, refparams)

def inspection(incdir, libdir, libname, tool_name='llvm'):
	"""
	# Construct the Reference Parameter factors
	"""
	r = {
		'system': {
			'library': {
				libdir: {libname},
			}
		},
		'source': {
			'library': {
				incdir: {None},
			}
		}
	}

	yield (tool_name+'/inspection', None, {'factors': r})
