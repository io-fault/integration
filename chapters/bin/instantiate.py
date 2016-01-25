"""
Structure and format the documentation into a pair of typed filesystem dictionaries.
"""
import os.path
import sys

from ...filesystem import library as libfs
from ...routes import library as libroutes

from . import structure
from . import format

from .. import theme
from .. import libif

def main(target, package):
	root = os.path.realpath(target)
	r = libroutes.File.from_absolute(root)

	structs = r / 'text' / 'xml'
	formats = r / 'text' / 'html'
	structs.init('directory')
	formats.init('directory')

	css = r / 'text' / 'css'
	js = r / 'application' / 'javascript'

	structure.main(str(structs), package)
	format.main(str(structs), str(formats), suffix='')

	d = libfs.Dictionary.use(css)
	d[b'factor.css'] = theme.bytes

	d = libfs.Dictionary.use(js)
	d[b'factor.js'] = libif.bytes

	return 0

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))
