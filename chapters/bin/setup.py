"""
# Extend a delineation context to parse text files.
"""
import os
import sys
import importlib
import itertools

from fault.system import process
from fault.system import python
from fault.system import files
from fault.project import root

from ...factors import constructors
from ...factors import cc
from ...factors import data as ccd

def install(args, fault, ctx, ctx_route, ctx_params, fs_symbol='fault.text'):
	"""
	# Install chapter parser.
	"""
	mechfile = ctx_route / 'mechanisms' / fs_symbol

	ccd.update_named_mechanism(mechfile, 'root', {
		'chapter-text': {
			'formats': {
				'chapter': 'i',
			},
			'transformations': {
				'tool:kleptic-parser': {
					'method': 'python',
					'command': __package__ + '.delineate',
					'interface': constructors.__name__ + '.delineation',
				},
				'kleptic-text': {
					'inherit': 'tool:kleptic-parser',
				},
			},

			'integrations': {
				'chapter': constructors.Clone,
			},
		}
	})

	ccd.update_named_mechanism(mechfile, 'path-setup', {
		'context': {'path': ['chapter-text']}
	})

def main(inv:process.Invocation) -> process.Exit:
	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = files.Path.from_absolute(inv.environ['CONTEXT'])
	ctx = cc.Context.from_directory(ctx_route)

	ctx_params = ctx.index['context']
	if ctx_params['intention'] == 'delineation':
		install(inv.args, fault, ctx, ctx_route, ctx_params)
	else:
		# Only delineation for text.
		pass

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
