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

from ...factors import constructors
from ...factors import cc
from ...factors import data as ccd
from ...root import query

def install(route, ctx, settings, fs_symbol='fault.text'):
	"""
	# Install chapter parser.
	"""
	mechfile = route / 'mechanisms' / fs_symbol
	tool = settings.get('tool', default_tool)

	ccd.update_named_mechanism(mechfile, 'root', {
		'chapter-text': {
			'formats': {
				'text.chapter': 'i',
			},
			'transformations': {
				'tool:kleptic-parser': {
					'interface': constructors.__name__ + '.delineation',
					'factor': __package__ + '.delineate',
					'command': str(tool),
					'tool': ['delineate-kleptic-text'],
				},
				'kleptic': {
					'inherit': 'tool:kleptic-parser',
				},
			},

			'integrations': {
				'text.chapter': constructors.Clone,
			},
		}
	})

	ccd.update_named_mechanism(mechfile, 'path-setup', {
		'context': {'path': ['chapter-text']}
	})

default_tool = (query.libexec()/'fault-dispatch')

def main(inv:process.Invocation) -> process.Exit:
	route = files.Path.from_absolute(inv.argv[0])
	settings = dict(zip(inv.argv[1::2], inv.argv[2::2]))
	ctx = cc.Context.from_directory(route)

	if ctx.index['context']['intention'] == 'delineation':
		install(route, ctx, settings)
	else:
		# Only delineation for text.
		pass

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
