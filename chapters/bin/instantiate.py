"""
Structure and format the documentation into a pair of typed filesystem dictionaries.
"""
import os.path
import sys

from ...filesystem import library as libfs
from ...routes import library as libroutes
from ...development import libsurvey

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

	packages = state_fsd[b'survey:packages'].decode('utf-8').split('\n')
	for package in packages:
		structure.structure_package(str(structs), package)
		format.main(str(structs), str(formats), survey=state_fsd, suffix='')

	d = libfs.Dictionary.use(css)
	d[b'factor.css'] = theme.bytes

	d = libfs.Dictionary.use(js)
	d[b'factor.js'] = libif.bytes

	return 0

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))