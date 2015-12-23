"""
Format the referenced structure set into
&..filesystem.library.Dictionary instance.
"""

import sys
import itertools
import os.path
import lzma
import types
import importlib.machinery

from ...routes import library as libroutes
from ...xml import library as libxml
from ...filesystem import library as libfs

from .. import xslt

def index_xml(directory, index):
	content = libxml.element('map',
		itertools.chain.from_iterable(
			libxml.element('item',
				libxml.escape_element_string(str(r)),
				('key', k)
			)
			for k, r in index.items()
		),
		('dictionary', directory),
		('xmlns', 'https://fault.io/xml/filesystem#index'),
	)

	return b''.join(content)

def main(source, target):
	src = os.path.realpath(source)
	structs = libfs.Dictionary.open(src)
	formats = libfs.Dictionary.create(libfs.Hash(), os.path.realpath(target))

	index = {
		k.decode('utf-8'): r
		for k, r in structs.references()
	}
	xml = index_xml(src, index)

	# temporary for the index.xml file
	with libroutes.File.temporary() as tr:
		idx_path = tr / 'index.xml'
		with idx_path.open('wb') as f:
			f.write(xml)

		for k, r in index.items():
			output = formats.route(k.encode('utf-8'))
			try:
				rtf = xslt.process_file(str(r), document_index=str(idx_path))
			except Exception as err:
				print(k, str(err))
				continue
			with output.open('wb') as f:
				rtf.write(f)

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))
