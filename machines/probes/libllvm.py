"""
LLVM Probe for collecting compilation and linkage information.

Gathers information using (system:executable)`llvm-config`.
"""
import sys
import sysconfig
import subprocess

__factor_type__ = 'system'
__factor_dynamics__ = 'probe'

parameters = {
	'executable':
		"The `llvm-config` executable to extract information from.",
}

libs_pipe = ['llvm-config', 'profiledata', '--libs'] #r"""{} profiledata --libs"""
syslibs_pipe = ['llvm-config', 'profiledata', '--system-libs'] #r"""{} profiledata --system-libs"""
incs_pipe = ['llvm-config', '--includedir'] #r"""{} --includedir"""
libdir_pipe = ['llvm-config', '--libdir'] #r"""{} --libdir"""
rtti_pipe = ['llvm-config', '--has-rtti']

def deploy(*args):
	Popen = subprocess.Popen
	STDOUT = subprocess.STDOUT
	PIPE = subprocess.PIPE


	outs = [
		Popen(libs_pipe, stdin=None, stderr=STDOUT, stdout=PIPE).communicate(),
		Popen(syslibs_pipe, stdin=None, stderr=STDOUT, stdout=PIPE).communicate(),
		Popen(libdir_pipe, stdin=None, stderr=STDOUT, stdout=PIPE).communicate(),
		Popen(incs_pipe, stdin=None, stderr=STDOUT, stdout=PIPE).communicate(),
		Popen(rtti_pipe, stdin=None, stderr=STDOUT, stdout=PIPE).communicate(),
	]

	libs, syslibs, libdirs, incdirs, rtti = [x[0].decode('utf-8') for x in outs]

	libs = set(map(str.strip, libs.split('-l')))
	libs.update(map(str.strip, syslibs.split('-l')))
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
