"""
# LLVM Probe for collecting compilation and linkage information.

# Gathers information using (system/executable)`llvm-config`.
"""
import os
import sys
import sysconfig
import subprocess
from fault.development import library as libdev

__factor_type__ = 'probe'

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
	libs.discard('')
	libs.add('c++')

	covlibs = set(map(str.strip, covlibs.split('-l')))
	covlibs.discard('')

	syslibs = set(map(str.strip, syslibs.split('-l')))
	syslibs.discard('')

	libdirs = set(map(str.strip, libdirs.split('-L')))
	libdirs.discard('')
	dir, *reset = libdirs

	incdirs = set(map(str.strip, incdirs.split('-I')))
	incdirs.discard('')

	if rtti.lower() in {'yes', 'true', 'on'}:
		rtti = True
	else:
		rtti = False

	include_factors = [
		libdev.iFactor(
			domain = 'source',
			type = 'library',
			name = None,
			integral = x,
		)
		for x in incdirs
	]

	coverage_factors = [
		libdev.iFactor(
			domain = 'system',
			type = 'library',
			name = x,
			integral = dir,
		)
		for x in covlibs
	]

	system_factors = [
		libdev.iFactor(
			domain = 'system',
			type = 'library',
			name = x,
			integral = None,
		)
		for x in syslibs
	]

	system_factors.append(
		libdev.iFactor(
			domain = 'system',
			type = 'library',
			name = 'c++',
			integral = None,
		)
	)

	variants = {
		'rtti':'off', 'exceptions':'off',
		'c++-standard': 'c++11',
	}
	srcparams = ()

	return variants, srcparams, include_factors + coverage_factors + system_factors

if __name__ == '__main__':
	print(deploy())
