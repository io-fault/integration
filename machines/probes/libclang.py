"""
Probe for libclang.

Gathers information relative to (system:executable)`clang`.
"""
import sys
import sysconfig
import shutil

from ...routes import library as libroutes

__factor_type__ = 'system.probe'

parameters = {
	'executable':
		"The `llvm-config` executable to extract information from.",
}

def deploy(*args):
	clang = shutil.which('clang')
	r = libroutes.File.from_path(clang)
	prefix = r.container.container
	cl = prefix / 'lib'
	ci = prefix / 'include'

	return {
		'system': {
			'library.set': {'clang', 'c'},
			'library.directories': {str(cl)},
			'include.directories': {str(ci)},
		},
	}

if __name__ == '__main__':
	print(deploy())
