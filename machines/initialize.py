"""
# Initialize the System Context for the integration processing and machine execution of Factors.
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

def perform(target_directory:files.Path):
	from .host import construction as cci
	from fault.system import factors
	factors.context.load()
	factors.context.configure()
	cci.mkcc(target_directory)

def main(inv:process.Invocation) -> process.Exit:
	config = {
		'machines': [],
	}
	optr = recognition.legacy(restricted, required, inv.argv)
	argv = recognition.merge(config, optr)

	if len(argv) != 1:
		sys.stderr.write("ERROR: initialize requires exactly one parameter, %d given.\n" %(len(argv),))
		return inv.exit(1)

	target = files.Path.from_path(argv[0])
	if target.fs_type() == 'void':
		target.fs_mkdir()

	perform(target)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
