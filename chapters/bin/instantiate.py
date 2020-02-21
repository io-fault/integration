"""
# Structure and format the documentation into a pair of typed filesystem dictionaries.
"""
import os.path
import sys

from fault.system import process
from fault.system import files
from fault.system import libfactor
from fault.hkp import library as libhkp

from ...factors import cc as libdev
from ...factors.bin import stitch

from . import format

from .. import theme
from .. import libif
from .. import library

def main(inv:process.Invocation) -> process.Exit:
	target, state = inv.args
	ctx = libdev.Context.from_environment()
	state_fsd = libhkp.Dictionary.use(files.Path.from_path(state))
	r = files.Path.from_path(target)

	structs = r / 'text' / 'xml'
	formats = r / 'text' / 'html'
	structs.fs_mkdir()
	formats.fs_mkdir()
	xml = libhkp.Dictionary.use(structs)
	html = libhkp.Dictionary.use(formats)

	css = r / 'text' / 'css'
	js = r / 'application' / 'javascript'

	packages = state_fsd[b'metrics:packages'].decode('utf-8').split('\n')
	for package in packages:
		stitch.copy(ctx, str(structs), package, state)
		format.main(str(structs), str(formats), suffix="")

	# temporary for the index.xml file
	with files.Path.fs_tmpdir() as tr:
		index = {
			k.decode('utf-8'): r
			for k, r in xml.references()
		}
		mapxml = library.construct_corpus_map(str(structs), index)

		idx_path = tr / 'index.xml'
		with idx_path.fs_open('wb') as f:
			f.write(mapxml)
		idx = str(idx_path)

		# Format Corpus Index
		corpus_dot_html = html.route(b'')
		with corpus_dot_html.fs_open('wb') as f:
			rtf = library.index(
				os.environ.get('CORPUS_TITLE', ''),
				packages,
				document_index = idx,
				reference_suffix = '',
			)
			rtf.write(f)

	d = libhkp.Dictionary.use(css)
	d[b'factor.css'] = (libfactor.package_inducted(theme) / 'theme.css').fs_load()

	d = libhkp.Dictionary.use(js)
	d[b'factor.js'] = (libfactor.package_inducted(libif) / 'libif.js').fs_load()

	sys.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
