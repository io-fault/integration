"""
# System command access to &.html rendering functionality.
"""
import sys
import pprint
import pdb
import traceback

from fault.system import process
from fault.system import files

def main(inv:process.Invocation) -> process.Exit:
	src, *styles = inv.argv
	sf = files.Path.from_path(src)

	with sf.fs_open('r') as f:
		doctext = f.read()

	try:
		sys.stdout.buffer.writelines(transform(doctext))
	except:
		p = pdb.Pdb()
		traceback.print_exc()
		sys.stderr.flush()
		p.interaction(None, sys.exc_info()[2])

	return inv.exit(0)
