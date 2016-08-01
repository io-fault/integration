"""
Structure and format the documentation into a pair of typed filesystem dictionaries.
"""
import os.path
import sys

from ...filesystem import library as libfs
from ...routes import library as libroutes
from ...development import libfactor

from . import structure
from . import format

from .. import theme
from .. import libif

def main(target, state):
	state_fsd = libfs.Dictionary.use(libroutes.File.from_path(state))
	r = libroutes.File.from_path(target)

	structs = r / 'text' / 'xml'
	formats = r / 'text' / 'html'
	structs.init('directory')
	formats.init('directory')

	css = r / 'text' / 'css'
	js = r / 'application' / 'javascript'

	packages = state_fsd[b'metrics:packages'].decode('utf-8').split('\n')
	for package in packages:
		structure.structure_package(str(structs), package, state)
		format.main(str(structs), str(formats), suffix='')

	d = libfs.Dictionary.use(css)
	i = libroutes.Import.from_fullname(theme.__name__)
	fr = libfactor.reduction(i, 'host', 'optimal')
	with fr.open('rb') as f:
		d[b'factor.css'] = f.read()

	d = libfs.Dictionary.use(js)
	d[b'factor.js'] = libif.bytes

	return 0

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))
