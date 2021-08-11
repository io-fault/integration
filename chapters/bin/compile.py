"""
# Compile and archive text factors.
"""
import sys
import importlib

from fault.system import process
from fault.system import files

def replicate(target, origin):
	(target).fs_alloc().fs_mkdir()
	(target).fs_replace(origin)

def archive(output, source):
	"""
	# Copy the units directory, &source, to the target image location &output.
	"""
	replicate(output, source)

def delineate(output, source):
	"""
	# Parse kleptic text and serialize its element tree as JSON.
	"""
	from fault.text.bin import parse
	import json

	with source.fs_open('r') as f:
		chapter = parse.chapter(f.read())
	root = ('factor', [chapter], {})

	r = output
	r.fs_alloc().fs_mkdir()

	with (r/"elements.json").fs_open('w') as f:
		json.dump(root, f)

def main(inv:process.Invocation) -> process.Exit:
	out, src, *plist = inv.argv
	output = files.Path.from_path(out)
	source = files.Path.from_path(src)
	params = dict(zip(plist[0::2], plist[1::2]))
	del plist

	language, dialect = params.pop('format').split('.', 1)
	if (language, dialect) == ('directory', 'tree'):
		# Clean json and copy tree.
		archive(output, source)
	else:
		# Ignoring the actual language for the moment.
		# Markdown support will likely come at some point.
		delineate(output, source)

	return inv.exit(0)
