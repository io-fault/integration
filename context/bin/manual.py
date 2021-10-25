"""
# Execute the (system/command)`man` found in (system/environ)`PATH` with the environment
# configured to find fault manual pages provided by the product set initialized by &..root.
"""
import sys
import os
from fault.system import process
from fault.system import query
from ...root.query import ipath

def main(inv:process.Invocation) -> process.Exit:
	suffix = os.environ.get('MANPATH') or ''
	if suffix:
		suffix = ':' + suffix
	os.environ['MANPATH'] = str(ipath/'man') + suffix

	for x in query.executables('man'):
		man_exe = str(x)
		break
	else:
		man_exe = '/usr/bin/man'

	os.execve(man_exe, [man_exe] + inv.argv, os.environ)
	sys.stderr.write("ERROR: execve did not replace the process image with a man executable.\n")
	return inv.exit(250)
