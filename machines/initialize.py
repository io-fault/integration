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

	# Compiler driver.
	'-d': ('field-replace', 'cd-path'),
	'-t': ('field-replace', 'cd-type'),
}

def perform(cdpath:files.Path, cdtype:str, target_directory:files.Path):
	from .host import construction as cci
	from fault.system import factors
	factors.context.load()
	factors.context.configure()
	cci.mkcc(target_directory, (cdpath, cdtype))

def main(inv:process.Invocation) -> process.Exit:
	config = {
		'machines': [],
		'cd-path': '/usr/bin/clang', # Compiler Driver; system linker interface + compiler.
		'cd-type': None, # llvm-clang or gnu-cc
	}
	optr = recognition.legacy(restricted, required, inv.argv)
	argv = recognition.merge(config, optr)

	if len(argv) != 1:
		sys.stderr.write("ERROR: initialize requires exactly one parameter, %d given.\n" %(len(argv),))
		return inv.exit(1)

	target = inv.fs_pwd@argv[0]
	if target.fs_type() == 'void':
		target.fs_mkdir()

	cdpath = config['cd-path']
	cdtype = config['cd-type']
	if cdtype is None:
		if 'clang' in cdpath:
			cdtype = 'llvm-clang'
		elif 'gcc' in cdpath:
			cdtype = 'gnu-cc'
		else:
			# clang tends to be more permissive so use gcc terms
			# when the type is unspecified.
			cdtype = 'gnu-cc'

	perform(inv.fs_pwd@cdpath, cdtype, target)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
