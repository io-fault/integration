"""
LLVM Probe for collecting compilation and linkage information.

Gathers information using (system:executable)`llvm-config`.
"""
import os
import sys
import sysconfig
import subprocess

__factor_type__ = 'system'
__factor_dynamics__ = 'probe'

parameters = {
	'executable':
		"The `llvm-config` executable to extract information from.",
}

llvm_config = os.environ.get('LLVM_CONFIG', 'llvm-config')

libs_pipe = [llvm_config, 'profiledata', '--libs']
syslibs_pipe = [llvm_config, 'profiledata', '--system-libs']
covlibs_pipe = [llvm_config, 'coverage', '--libs']
incs_pipe = [llvm_config, '--includedir']
libdir_pipe = [llvm_config, '--libdir']
rtti_pipe = [llvm_config, '--has-rtti']

def deploy(*args):
	Popen = subprocess.Popen
	STDOUT = subprocess.STDOUT
	PIPE = subprocess.PIPE
	po = lambda x: Popen(x, stdin=None, stderr=PIPE, stdout=PIPE).communicate()

	outs = [
		po(libs_pipe),
		po(syslibs_pipe),
		po(covlibs_pipe),
		po(libdir_pipe),
		po(incs_pipe),
		po(rtti_pipe),
	]

	libs, syslibs, covlibs, libdirs, incdirs, rtti = [x[0].decode('utf-8') for x in outs]

	libs = set(map(str.strip, libs.split('-l')))
	libs.update(map(str.strip, syslibs.split('-l')))
	libs.update(map(str.strip, covlibs.split('-l')))
	libs.discard('')
	libs.add('c++')

	libdirs = set(map(str.strip, libdirs.split('-L')))
	libdirs.discard('')

	incdirs = set(map(str.strip, incdirs.split('-I')))
	incdirs.discard('')

	if rtti.lower() in {'yes', 'true', 'on'}:
		rtti = True
	else:
		rtti = False

	return {
		'system': {
			'library.set': libs,
			'library.directories': libdirs,
			'include.directories': incdirs,
			'standards': {
				'c++': 'c++11',
			},
			'command.option.injection': [
				'-fno-exceptions', '-fno-rtti',
			]
		},

		'software': {
			'llvm': {
				'rtti': rtti,
			}
		}
	}

if __name__ == '__main__':
	print(deploy())
