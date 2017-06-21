"""
# Structure and format the documentation into a pair of typed filesystem dictionaries.
"""
import os.path
import sys

from ...development import library as libdev
from ...system import library as libsys
from ...filesystem import library as libfs
from ...routes import library as libroutes
from ...system import libfactor

from . import structure
from . import format

from .. import theme
from .. import libif
from .. import library

def main(inv):
	target, state = inv.args
	ctx = libdev.Context.from_environment()
	state_fsd = libfs.Dictionary.use(libroutes.File.from_path(state))
	r = libroutes.File.from_path(target)

	structs = r / 'text' / 'xml'
	formats = r / 'text' / 'html'
	structs.init('directory')
	formats.init('directory')
	xml = libfs.Dictionary.use(structs)
	html = libfs.Dictionary.use(formats)

	css = r / 'text' / 'css'
	js = r / 'application' / 'javascript'

	packages = state_fsd[b'metrics:packages'].decode('utf-8').split('\n')
	for package in packages:
		structure.copy(ctx, str(structs), package, state)
		format.main(str(structs), str(formats), suffix="")

	# temporary for the index.xml file
	with libroutes.File.temporary() as tr:
		index = {
			k.decode('utf-8'): r
			for k, r in xml.references()
		}
		mapxml = library.construct_corpus_map(str(structs), index)

		idx_path = tr / 'index.xml'
		with idx_path.open('wb') as f:
			f.write(mapxml)
		idx = str(idx_path)

		# Format Corpus Index
		corpus_dot_html = html.route(b'')
		with corpus_dot_html.open('wb') as f:
			rtf = library.index(
				os.environ.get('CORPUS_TITLE', ''),
				packages,
				document_index = idx,
				reference_suffix = '',
			)
			rtf.write(f)

	d = libfs.Dictionary.use(css)
	d[b'factor.css'] = (libfactor.package_inducted(theme) / 'theme.css').load()

	d = libfs.Dictionary.use(js)
	d[b'factor.js'] = (libfactor.package_inducted(libif) / 'libif.js').load()

	sys.exit(0)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())
