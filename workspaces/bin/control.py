"""
# System command interface for controlling and using a workspace context.
# Normally bound as (id)`wkctl`.
"""
import os
import sys
import importlib

from fault.vector import recognition
from fault.system import process
from fault.system import files

from .. import system
from .. import __name__ as project_package_name

restricted = {
	# Intentions effecting executable factors.
	'-I': ('set-add', 'identity', 'intentions'),
	'-O': ('set-add', 'optimal', 'intentions'),
	'-o': ('set-add', 'portable', 'intentions'),
	'-g': ('set-add', 'debug', 'intentions'),

	'-y': ('set-add', 'auxilary', 'intentions'),
	'-Y': ('set-add', 'capture', 'intentions'),

	'-P': ('set-add', 'profile', 'intentions'),
	'-C': ('set-add', 'coverage', 'intentions'),

	# Reprocess levels.
	'-U': ('field-replace', -1, 'relevel'),
	'-u': ('field-replace', +0, 'relevel'),
	'-r': ('field-replace', +1, 'relevel'),
	'-R': ('field-replace', +2, 'relevel'),
	'-.': ('ignore', None, None),
}

required = {
	'-i': ('set-add', 'intentions'),
	'-W': ('field-replace', 'workspace-directory'),
	'-w': ('field-replace', 'workspace-name'),
	'-D': ('field-replace', 'product-directory'),

	'-x': ('field-replace', 'execution-context'),
	'-X': ('field-replace', 'construction-context'),
	'-L': ('field-replace', 'processing-lanes'),

	'--cache': ('field-replace', 'cache-directory'),
}

command_index = {
	# Build factor integrals.
	'build': (
		'.process', 'build',
		({}, {}),
		'intentions', 'relevel', 'processing-lanes', 'argv',
	),
	# Execute test factors.
	'test': (
		'.process', 'test',
		({}, {}),
		'intentions', 'relevel', 'processing-lanes', 'argv',
	),

	# Delineate factor sources, analyze factor elements.
	'delineate': (
		# Delineation is recognized by the command identifier.
		'.process', 'delineate',
		({}, {}),
		'relevel', 'processing-lanes', 'argv',
	),
	'analyze': (
		'.process', 'analyze',
		({}, {}),
		'relevel', 'processing-lanes', 'argv',
	),
	'measure': (
		'.process', 'measure',
		({}, {}),
		'intentions', 'relevel', 'processing-lanes', 'argv',
	),

	# Clear build cache, clean product integrals.
	'clear': (
		'.manipulation', 'clear',
		({}, {}),
	),
	'clean': (
		'.manipulation', 'clean',
		({}, {}),
	),
}

def main(inv:process.Invocation) -> process.Exit:
	config = {
		'argv': (),
		'command': None,
		'intentions': set(),
		'relevel': '0',
		'processing-lanes': '4',
		'construction-context': None,
		'execution-context': None,
		'product-directory': None,
		'workspace-directory': None,
		'workspace-name': system.WORKSPACE,
		'cache-directory': None,
	}
	oeg = recognition.legacy(restricted, required, inv.argv)
	remainder = recognition.merge(config, oeg)

	if not remainder:
		# No command issued.
		return inv.exit(254)

	command_id = config['command'] = remainder[0]
	config['argv'] = remainder[1:]
	del remainder

	if command_id not in command_index:
		sys.stderr.write("ERROR: unknown command %r\n" %(command_id,))
		return inv.exit(253)

	module_name, opname, opargs, *opconfig = command_index[command_id]
	module = importlib.import_module(module_name, project_package_name)
	opcall = getattr(module, opname)
	pwd = process.fs_pwd()

	wkname = config['workspace-name']
	if config['workspace-directory'] is None:
		route = pwd/wkname
	else:
		route = (pwd@config['workspace-directory'])/wkname
	route.fs_require('rx/') # -W/.workspace does not exist.
	os.environ['WORKSPACE'] = str(route)

	if config['product-directory'] is None:
		product = pwd
	else:
		product = (pwd@config['product-directory'])
	os.environ['PRODUCT'] = str(product)

	# Override .workspace/cc default? Option consistent with pdctl.
	if config['construction-context'] is None:
		cc = (route/'cc')
	else:
		cc = (pwd@config['construction-context'])

	# Override .workspace/xc default? Option consistent with pdctl.
	if config['execution-context'] is None:
		xc = (route/'xc')
	else:
		xc = (pwd@config['execution-context'])

	os.environ['F_PRODUCT'] = str(cc)

	if config['cache-directory'] is not None:
		cache = (pwd@config['cache-directory'])
	else:
		cache = (route * system.CACHE) # workspace-directory/.cache
	works = system.Tooling(cc/'tools')
	wkenv = system.Environment(+route, +cache, works, product, cc, xc)

	status = opcall(wkenv, *[config.get(x) for x in opconfig])
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
