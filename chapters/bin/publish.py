"""
# Publish the structures and formatted data.
# Essentially, convert the directories created by &.bin.structure and &.bin.format
# into a set of static uncompressed files that may be directly accessed.
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

def transparent_transfer(src, dst):
	data = src.read(1024*64)
	while data:
		dst.write(data)
		data = src.read(1024*64)

def path(out, factor, extension):
	if b'/' in factor:
		fs = factor.decode('utf-8')
		start, *remainder = fs.split('/')
		start += '.d'
		out = out / start
		return out.extend(remainder)
	else:
		return out / ((factor.decode('utf-8')) + extension)

def main(structs, formatting, output):
	structs = os.path.realpath(structs)
	formatting = os.path.realpath(formatting)
	out = libroutes.File.from_absolute(os.path.realpath(output))
	out.init('directory')

	sd = libfs.Dictionary.open(structs)
	fd = libfs.Dictionary.open(formatting)

	for factor, r in sd.references():
		dr = path(out, factor, '.xml')
		with r.open('rb') as fi:
			dr.init('file')
			with dr.open('wb') as fo:
				transparent_transfer(fi, fo)

	for factor, r in fd.references():
		dr = path(out, factor, '.html')
		with r.open('rb') as fi:
			dr.init('file')
			with dr.open('wb') as fo:
				transparent_transfer(fi, fo)

	specific = [
		(out / 'factor.css', theme.output()),
		(out / 'factor.js', libif.output()),
	]
	for dst, src in specific:
		with dst.open('wb') as out:
			with src.open('rb') as inp:
				transparent_transfer(inp, out)

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))

