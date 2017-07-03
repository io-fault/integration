"""
# Probe for libclang.

# Gathers information relative to (system/executable)`clang`.
"""
import sys
import sysconfig
import shutil

from fault.routes import library as libroutes
from fault.development import library as libdev

__factor_domain__ = 'system'
__factor_type__ = 'probe'

parameters = {
	'clang-library-path':
		"Path to the libclang to use.",
	'clang-includes-path':
		"Path to include directory containing libclang headers.",
}

def deploy(*args):
	clang = shutil.which('clang-3.9')
	r = libroutes.File.from_path(clang)
	prefix = r.container.container
	cl = prefix / 'lib'
	ci = prefix / 'include'

	return (), (), [
		libdev.iFactor(
			domain = 'system',
			type = 'library',
			name = 'clang',
			integral = cl,
		),
		libdev.iFactor(
			domain = 'source',
			type = 'library',
			name = None,
			integral = ci,
		),
	]

if __name__ == '__main__':
	print(deploy())
