"""
# Product configuration and integration system command.
"""
import sys
import os
import importlib
import contextlib

from fault.vector import recognition
from fault.system import files
from fault.system import process
from fault.transcript.io import Log

from . import __name__ as project_package_name
from . import context

restricted = {
	'-c': ('field-replace', 'transient', 'cache-type'),
	'-.': ('ignore', None, None),
}

required = {
	'-x': ('field-replace', 'machines-context-name'),
	'-X': ('field-replace', 'system-context-directory'),

	'-D': ('field-replace', 'product-directory'),
	'-L': ('field-replace', 'processing-lanes'),
	'-C': ('field-replace', 'persistent-cache'),
}

command_index = {
	# Process factors with respect to the product index.
	'integrate': ('.process', 'options', 'integrate'),
	'delineate': ('.process', 'options', 'delineate'),
	'identify': ('.process', 'options', 'identify'),
	'measure': ('.process', 'options', 'measure'),

	# Manipulate product index and connections.
	'delta': ('.manipulate', 'options', 'delta'),

	# Show product status.
	'status': ('.query', 'options', 'report')
}

def configure(restricted, required, argv):
	"""
	# Root option parser.
	"""
	config = {
		'features': set(),
		'processing-lanes': '4',
		'machines-context-name': 'machines',
		'system-context-directory': None,
		'construction-mode': 'executable',
		'persistent-cache': None,
		'cache-type': 'persistent',
		'product-directory': None,
		'default-product': None,

		'interpreted-connections': [],
		'interpreted-disconnections': [],
		'direct-connections': [],
		'direct-disconnections': [],

		'relevel': 0,
		'cache-directory': None,
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def main(inv:process.Invocation) -> process.Exit:
	pwd = process.fs_pwd()

	config, remainder = configure(restricted, required, inv.argv)
	if not remainder:
		command_id = 'status'

	if remainder:
		command_id = remainder[0]
	else:
		command_id = 'help'

	if command_id == 'help':
		sys.stderr.write(' '.join((
			"fictl",
				"[-X system-context-directory]"
				"[-x machines-context-name]"
				"[-D product-directory]",
			"(status | delta | integrate)",
			"project-selector ...\n"
		)))
		return inv.exit(63)
	elif command_id not in command_index:
		sys.stderr.write("ERROR: unknown command '%s'." %(command_id,))
		return inv.exit(2)

	# Identify command module, and merge global config with command options.
	module_name, optset, operation = command_index[command_id]
	module = importlib.import_module(module_name, project_package_name)
	oprestricted, oprequired = getattr(module, optset)

	cmd_oeg = recognition.legacy(oprestricted, oprequired, remainder[1:])
	cmd_remainder = recognition.merge(config, cmd_oeg)

	if config['product-directory']:
		pdr = files.Path.from_path(config['product-directory'])
		config['default-product'] = False
	else:
		pdr = pwd
		config['default-product'] = True

	# Identify the system context to use to process factors.
	origin, cc = context.resolve(config['system-context-directory'], product=pdr)

	if config['cache-directory'] is not None:
		cache = (pwd@config['cache-directory'])
	else:
		cache = (pdr/'.cache')

	fictl_operation = getattr(module, operation)
	with contextlib.ExitStack() as ctx:
		fictl_operation(ctx, Log.stderr(), Log.stdout(), config, cc, pdr, cmd_remainder)
	return inv.exit(0)
