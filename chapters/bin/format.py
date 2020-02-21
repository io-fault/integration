"""
# Format the referenced structure set into a &libhkp.Dictionary instance.
"""

import sys
import itertools
import os.path
import lzma
import types
import importlib.machinery
import io

from fault.system import files
from fault.hkp import library as libhkp

from .. import library as libfactors

def main(source, target, suffix='.html'):
	src = os.path.realpath(source)
	structs = libhkp.Dictionary.open(src)
	formats = libhkp.Dictionary.create(libhkp.Hash(), os.path.realpath(target))

	index = {
		k.decode('utf-8'): r
		for k, r in structs.references()
	}
	xml = libfactors.construct_corpus_map(src, index)

	# temporary for the index.xml file
	with files.Path.fs_tmpdir() as tr:
		idx_path = tr / 'index.xml'
		with idx_path.fs_open('wb') as f:
			f.write(xml)
		idx = str(idx_path)

		for k, r in index.items():
			ek = k.encode('utf-8')
			output = formats.route(ek)
			spd = ''

			try:
				rtf = libfactors.transform(str(r),
					document_index = idx,
					reference_suffix = suffix,
					metrics_profile = spd,
				)
			except Exception as err:
				print(k, str(err))
				continue

			try:
				with output.fs_open('wb') as f:
					rtf.write(f)
			except Exception as err:
				print(str(output), err)
				continue

if __name__ == '__main__':
	main(*sys.argv[1:])
