"""
# Execute a factor by using the configured plan for the identified architecture.
"""
import os
import sys

from fault.system import files
from fault.system import process
from fault.system import query
from fault.vector import recognition

from fault.project.system import Context
from fault.system.execution import Platform, serialize_sx_plan

from .. import query

restricted = {
	# Common intentions.
	'-O': ('field-replace', 'optimal', 'intention'),
	'-g': ('field-replace', 'debug', 'intention'),
	'-p': ('field-replace', 'portable', 'intention'),
	'-y': ('field-replace', 'auxiliary', 'intention'),
	'-P': ('field-replace', 'profile', 'intention'),
	'-C': ('field-replace', 'coverage', 'intention'),
	'-Y': ('field-replace', 'capture', 'intention'),
}

required = {
	'-I': ('field-replace', 'intention'),
	'-A': ('field-replace', 'architecture'),
	'-F': ('field-replace', 'form'),

	# Defaults to pwd.
	'-D': ('field-replace', 'product-directory'),
	'-x': ('field-replace', 'platform-directory'),
}

def main(inv:(process.Invocation)) -> (process.Exit):
	config = {
		'emit-reference': False,
		'platform-directory': None,
		'product-directory': None,
		'architecture': None,
		'intention': 'optimal',
		'form': '',
	}
	optr = recognition.legacy(restricted, required, inv.argv)
	command, factor_path, *xargv = recognition.merge(config, optr)

	if config['product-directory'] is None:
		pdr = process.fs_pwd()
	else:
		pdr = files.Path.from_path(config['product-directory'])

	if config['platform-directory']:
		pfr = files.Path.from_path(config['platform-directory'])
		pfi = Platform.from_directory(pfr)
	else:
		pfi = query.platform()

	projects = Context()
	projects.connect(pdr)
	projects.load()

	try:
		plan = query.select(
			pfi, projects, factor_path, xargv,
			architecture=config['architecture'],
			intention=config['intention'],
			form=config['form']
		)
	except query.IntegrationError:
		sys.stderr.write(
			"ERROR: no images available for executing %r.\n" %(factor_path,)
		)
		sys.stderr.write("PRODUCT: %s\n" %(str(pdr),))
		sys.stderr.write("EXECUTION[%s]: %s\n" %(pfi.system, ' '.join(archseq),))
	finally:
		if 'plan' not in locals():
			# exit() raises exception; avoid the context chain with this check.
			return inv.exit(1)

	if command == 'prepare':
		sys.stdout.write(''.join(serialize_sx_plan(plan)))
		return inv.exit(0)
	elif command == 'execute':
		os.environ.update(plan[0])
		os.execv(plan[1], plan[2])
		sys.stderr.write("ERROR: execv did not replace process image.\n")
		return inv.exit(250)
	else:
		sys.stderr.write("ERROR: unknown command %r.\n" %(command,))
		return inv.exit(1)

	return inv.exit(250)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
