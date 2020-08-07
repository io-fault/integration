"""
# System command access to &.join primary functionality.
"""
import sys
from fault.system import process
from fault.system import files
from .. import join

def main(inv:process.Invocation) -> process.Exit:
	source, *metas = inv.args
	r = files.Path.from_path(source)
	j = join.transform(r)
	sys.stdout.writelines(j)
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
