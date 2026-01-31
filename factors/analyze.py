"""
# Analyze the accuracy and efficiency of a set of projects.

# Procedure performing the necessary tasks for collecting measurements using the
"""
import os
import sys
import contextlib
from collections.abc import Iterable, Sequence

from fault.context import tools
from fault.vector import recognition
from fault.system import files
from fault.system import process
from fault.status import frames

from fault.system import execution
from fault.project import system as lsf

from ..root import query

restricted = {
	'-.': ('ignore', None, None),
	'-E': ('field-replace', False, 'efficiency'),
	'-e': ('field-replace', True, 'efficiency'),
	'-A': ('field-replace', False, 'accuracy'),
	'-a': ('field-replace', True, 'accuracy'),

	'-K': ('field-replace', False, 'reset-metrics'),
	'-k': ('field-replace', True, 'reset-metrics'),

	'--opened-frames': ('field-replace', True, 'opened-frames'),
	'--closed-frames': ('field-replace', False, 'opened-frames'),
}

required = {
	'-x': ('field-replace', 'machines-context-name'),
	'-X': ('field-replace', 'system-context-directory'),

	'-D': ('field-replace', 'product-directory'),
	'-L': ('field-replace', 'processing-lanes'),
	'-M': ('field-replace', 'status-monitors'),
	'-C': ('field-replace', 'persistent-cache'),
}

def execute(exe, argv):
	xpath = str(exe)
	args = [xpath] + list(argv)

	ki = execution.KInvocation(xpath, args)
	return execution.perform(ki)

def configure(restricted, required, argv):
	config = {
		'processing-lanes': '4',
		'status-monitors': None,
		'machines-context-name': None,
		'system-context-directory': None,
		'persistent-cache': None,
		'product-directory': None,
		'cache-directory': None,

		'reset-metrics': True,
		'efficiency': False,
		'accuracy': True,

		'opened-frames': False,
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def framew(file, typ, title, ext, channel=''):
	f = frames.compose(typ, title, channel, ext)
	file.write(frames.sequence(f))
	return f

def main(inv:process.Invocation):
	pwd = process.fs_pwd()
	config, argv = configure(restricted, required, inv.argv)
	env, exepath, xargv = query.dispatch('fictl')
	xargv = xargv[1:]
	selection, test = argv

	pd = pwd@config['product-directory']
	if config['opened-frames']:
		ctx = ['--opened-frames']
	else:
		ctx = ['--closed-frames']

	# For analyze, presume persistence.
	if config['cache-directory'] is None:
		(pd/'.cache').fs_mkdir() # Signal integrate to use a cache.

	# Prepare to forward some options to integrate.
	for opt, (op, slot) in required.items():
		if config[slot] is not None:
			ctx.append(opt)
			ctx.append(config[slot])
	ficmd = (lambda cmd, a: execute(exepath, xargv + [cmd] + ctx + a))
	sf = (lambda t, m, x: framew(sys.stdout, t, m, x))

	sf('->', 'Factor analysis: ' + selection, {})

	# Reset metrics images.
	if config['reset-metrics']:
		if (pd/'.metrics').fs_type() != 'void':
			(pd/'.metrics').fs_void()
			sf('-.', str(pd/'.metrics'), {})

	sys.stdout.flush()
	try:
		# Unconditionally integrate and delineate against coverage images.
		ficmd('integrate', ['-mcoverage', '-g', selection])
		ficmd('delineate', [selection])

		if config['accuracy']:
			ficmd('test', [test])
		else:
			# Still need delineated forms.
			ficmd('delineate', [selection])

		# Profiling
		if config['efficiency']:
			ficmd('integrate', ['-mprofile', '-O', selection])
			ficmd('test', [test])

		# Aggregate metrics for printing.
		# Reprocessing is necessary here in order to ignore the cache.
		ficmd('measure', ['-R', selection])
	finally:
		sf('<-', 'Analyzed: ' + selection, {})
		sys.stdout.flush()
