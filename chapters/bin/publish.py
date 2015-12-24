"""
Publish the structures and formatted data.
Essentially, convert the directories created by &.bin.structure and &.bin.format
into a set of static uncompressed files that may be directly accessed.
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
from .. import theme
from .. import libif

def transfer(src, dst):
	deflate = lzma.LZMADecompressor()
	data = src.read(1024*64)
	while data:
		dst.write(deflate.decompress(data))
		data = src.read(1024*64)

def main(structs, formatting, output):
	structs = os.path.realpath(structs)
	formatting = os.path.realpath(formatting)
	out = libroutes.File.from_absolute(os.path.realpath(output))
	out.init('directory')

	sd = libfs.Dictionary.open(structs)
	fd = libfs.Dictionary.open(formatting)

	for factor, r in sd.references():
		with r.open('rb') as fi:
			dr = out / ((factor.decode('utf-8')) + '.xml')
			dr.init('file')
			with dr.open('wb') as fo:
				transfer(fi, fo)

	for factor, r in fd.references():
		with r.open('rb') as fi:
			dr = out / ((factor.decode('utf-8')) + '.html')
			dr.init('file')
			with dr.open('wb') as fo:
				transfer(fi, fo)

	css = out / 'factor.css'
	js = out / 'libif.js'

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))

