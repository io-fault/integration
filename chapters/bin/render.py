"""
# Render text element trees.
"""
import sys
import importlib

from fault.system import process
from fault.system import files

def main(inv:process.Invocation) -> process.Exit:
	imodule, src, *xargv = inv.argv
	sf = files.Path.from_path(src)

	with sf.fs_open('r') as f:
		doctext = f.read()

	rtype = importlib.import_module('..'+imodule, __package__)

	rs = rtype.transform((), doctext)
	sys.stdout.writelines(x+'\n' for x in rs if x)
	return inv.exit(0)
