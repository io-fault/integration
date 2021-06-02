"""
# Extend metrics or delineation construction contexts with adapters built against the selected
# LLVM implementation.

# The setup process will modify the tool support context referenced by the target construction context.
# The coverage tooling requires various LLVM libraries for extracting counters,
# and the delineation tooling requires (system/library)`libclang` and clang includes.

# [ Engineering ]
# The implementation depends on the Construction Context instance being
# that of &..factors. While the engine may need to be
# Python, the context implementation should be variable such that context
# extension interface are used rather than presuming the implementation.
"""

import os
import sys
import importlib
import itertools
import pickle

from fault.system import files
from ...factors import constructors
from ...factors import data as ccd

from ..llvm import query
from ..llvm import constructors as cmd
from ..materialize import instantiate_software

name = 'fault.llvm'
transform_tool_name = 'tool:llvm-clang'
tool_name = 'llvm'
clang_instrumentation_options = ('-fprofile-instr-generate', '-fcoverage-mapping')

project_infra = b"""! CONTEXT:
	/protocol/
		&<http://if.fault.io/project/infrastructure>

/fault-c-interfaces/
	- &<http://fault.io/integration/machine/include>
	- &<http://fault.io/integration/python/include>
"""

# Implementation
sdk_deline = b"""
/sdk-llvm-delineation/
	- &<http://fault.io/integration/machine/llvm-delineation>
"""

def delineate(args, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the tooling for delineation.
	"""
	mech = ctx_route / 'mechanisms' / name
	from ..llvm import delineate

	tmpl_path = ctx_route.from_absolute(__file__) ** 2
	tmpl_path = tmpl_path / 'llvm' / 'formulas.txt'

	pdpath = ctx_route@'local'
	instantiate_software(pdpath, 'f_intention', 'bin', tool_name, tmpl_path, 'delineation')
	infra = project_infra + sdk_deline
	(pdpath/'f_intention'/'infrastructure.txt').fs_init(infra)

	sdk_product = str(files.Path.from_absolute(__file__) ** 5) + "\n"
	(pdpath/'.product'/'CONNECTIONS').fs_init(sdk_product.encode('utf-8'))

	data = {
		'host': {
			'system': 'void',
			'architecture': 'fragments',
			'transformations': {
				'c': constructors.Inherit(transform_tool_name),
				'c++': constructors.Inherit(transform_tool_name),
				'objective-c': constructors.Inherit(transform_tool_name),
				'c-header': constructors.Inherit(transform_tool_name),
				'c++-header': constructors.Inherit(transform_tool_name),

				transform_tool_name: {
					'command': delineate.__name__,
					'interface': cmd.__name__ + '.clang',
					'method': 'python',
				}
			},

			'integrations': {
				'archive': constructors.Clone,
				'partial': constructors.Clone,
				'extension': constructors.Clone,
				'executable': constructors.Clone,
				'library': constructors.Clone,
			}
		}
	}
	ccd.update_named_mechanism(mech, tool_name, data)

	# Derive library and include locations from tool:llvm-clang command
	merged = ccd.load_named_mechanism(mech, 'clang')
	syscmd = merged['host']['transformations'][transform_tool_name]['command']
	prefix = files.Path.from_absolute(syscmd) ** 2
	libdir = prefix / 'lib'
	incdir = prefix / 'include'
	dep = (incdir, libdir, 'clang')

	return ('llvm-delineation-libclang', query.delineation(*(map(str, dep))))

def coverage(args, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the tooling for coverage contexts.
	"""
	mech = (ctx_route/'mechanisms'/name)

	imp = python.Import.from_fullname(__package__).container
	tmpl_path = imp.file().container / 'templates' / 'context.txt'

	pdpath = ctx_route@'local'
	instantiate_software(pdpath, 'f_intention', 'extensions', tool_name, tmpl_path, 'instrumentation')

	# Derive llvm-config location from tool:llvm-clang's 'command' entry.
	merged = ccd.load_named_mechanism(mech, 'clang')
	tool = merged['host']['transformations'][transform_tool_name]
	syscmd = tool['command']
	args = (files.Path.from_absolute(syscmd).container / 'llvm-config',)

	# Get instrumentation support flags.
	source, merge, export, projections = query.instrumentation(*args)
	fsyms = (ctx_route / 'context' / 'symbols' / 'llvm-coverage-instrumentation')
	fsyms.fs_store(pickle.dumps(projections))

def compiler(args, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the host domain with tool:llvm-clang compiler.
	"""
	route = (ctx_route/'mechanisms'/name)
	syms = (ctx_route/'symbols')

	clang = dict(zip(args[0::2], args[1::2])).pop('CC', None)
	if not clang:
		clang = os.environ.get('CC')
	tool_data = query.clang(clang)

	tool_data.update({
		'type': 'collection',
		'interface': cmd.__name__ + '.clang',
		'defaults': {},
		'options': [],
	})

	data = {
		'host': {
			'transformations': {
				transform_tool_name: tool_data,
				'c': {
					'inherit': transform_tool_name,
				},
				'c++': {
					'inherit': transform_tool_name,
				},
				'c++-header': {
					'inherit': transform_tool_name,
				},
				'c-header': {
					'inherit': transform_tool_name,
				},
			}
		}
	}

	std = (syms / 'context:c++11')
	std.fs_store(pickle.dumps({
		'system': {'library': {None: set(['c++'])}},
	}))

	ccd.update_named_mechanism(route, 'clang', data)
	return route
