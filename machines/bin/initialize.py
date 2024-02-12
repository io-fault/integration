"""
# Initialize an Execution Platform with a Construction Context on the local system
# for the processing and execution of Factors.
"""
import os
import sys

from fault.system import files
from fault.system import identity
from fault.system import process
from fault.vector import recognition

restricted = {
	'-c': ('field-replace', False, 'enable-cc'),
}

required = {
	'-C': ('field-replace', 'cc-dirpath'),
}

def main(inv:(process.Invocation)) -> (process.Exit):
	config = {
		'cc-dirpath': None,
		'enable-cc': True,
	}
	optr = recognition.legacy(restricted, required, inv.argv)
	argv = recognition.merge(config, optr)

	if not argv:
		sys.stderr.write("ERROR: host platform initialization requires target directory argument.\n")
		return inv.exit(1)
	if len(argv) > 1:
		sys.stderr.write("ERROR: initialization takes only one parameter, %d given.\n" %(len(argv),))
		return inv.exit(2)

	target = files.Path.from_path(argv[0])
	if target.fs_type() == 'void':
		target.fs_mkdir()

	from ..host.execution import initialize
	initialize(target)

	if config['enable-cc']:
		ccr = (target/'cc')
		if config['cc-dirpath'] is not None:
			# Link to cc; don't initialize.
			fcc = files.Path.from_path(config['cc-dirpath'])
			ccr.fs_link_relative(fcc)
		else:
			# Initialize host default cc.
			# Load the project index.
			from ..host import construction as cci
			from ..text import construction as cct
			from fault.system import factors
			factors.context.load()
			factors.context.configure()
			cci.mkcc(ccr)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
