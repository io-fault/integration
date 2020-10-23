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

from fault.system import execution as libexec
from fault.system import process
from fault.system import python
from fault.system import files
from fault.project import root

from ...context import templates

from ....factors import cc
from ....factors import data as ccd
from .. import query
from .. import constructors

name = 'fault.llvm'
transform_tool_name = 'tool:llvm-clang'
tool_name = 'llvm'

def detect_profile_library(mechanism, architectures):
	"""
	# Given an `tool:llvm-clang` mechanism and a sequence of architecures, discover
	# the appropriate profile library to link against when building targets
	# that consist of LLVM instrumented sources.
	"""
	cclib = files.Path.from_absolute(mechanism['libraries'])
	profile_libs = [x for x in cclib.files() if 'profile' in x.identifier]

	if len(profile_libs) == 1:
		# Presume target of interest.
		profile_lib = profile_libs[0]
	else:
		# Scan for library with matching architecture.
		for x, a in itertools.product(profile_libs, architectures):
			if a in x.identifier:
				profile_lib = x
				break
		else:
			profile_lib = None

	if profile_lib.fs_type() == 'void':
		profile_lib = None

	return profile_lib

clang_instrumentation_options = ('-fprofile-instr-generate', '-fcoverage-mapping')

def rewrite_mechanisms(route:files.Path, layer:str, metrics_data):
	"""
	# Add clang instrumentation options and resources.
	"""
	compiler = ccd.load_named_mechanism(route, 'clang')
	host = ccd.load_named_mechanism(route.container/'fault.host', 'default')
	data = {
		'host': {
			'transformations': {
				transform_tool_name: {
					'resources': {
						'profile': None
					},
					'options': [],
				},
			}
		},
		'metrics': {
			tool_name: metrics_data,
		},
	}

	tool_data = data['host']['transformations'][transform_tool_name]

	# Add compilation arguments to generate instrumented objects.
	options = tool_data['options']
	for opt in clang_instrumentation_options:
		if opt not in options:
			options.append(opt)

	# Set profile entry if none.
	arch = host['host']['architecture']
	libs = compiler['host']['transformations'][transform_tool_name]
	profile = str(detect_profile_library(libs, arch))
	tool_data['resources']['profile'] = profile

	# Note the metrics tool.
	tool_data['metrics'] = tool_name

	return ccd.update_named_mechanism(route, layer, data)

def instantiate_software(ctxpy, package, subpackage, name, template, type, fault='fault'):
	# Initiialize llvm instrumentation or delineation tooling inside the target context.
	command = [
		"python3", "-m",
		fault+'.text.bin.ifst',
		str(ctxpy / package / subpackage / name),
		str(template), type,
	]

	pid, status, data = libexec.effect(libexec.KInvocation(sys.executable, command))
	if status != 0:
		sys.stderr.write("! ERROR: tool software instantiation failed\n")
		sys.stderr.write("\t/command\n\t\t" + " ".join(command) + "\n")
		sys.stderr.write("\t/status\n\t\t" + str(status) + "\n")

		sys.stderr.write("\t/message\n")
		sys.stderr.buffer.writelines(b"\t\t" + x + b"\n" for x in data.split(b"\n"))
		raise SystemExit(1)

project_infra = b"""! CONTEXT:
	/protocol/
		&<http://if.fault.io/project/infrastructure>

/fault-c-interfaces/
	- &<http://fault.io/engineering/posix/include>
	- &<http://fault.io/engineering/python/include>
"""

# Implementation
sdk_deline = b"""
/sdk-llvm-delineation/
	- &<http://fault.io/engineering/tools.llvm/delineation>
"""

def fragments(args, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the syntax tooling for delineation construction contexts.
	"""
	mech = ctx_route / 'mechanisms' / name

	imp = python.Import.from_fullname(__package__).container
	tmpl_path = imp.file().container / 'templates' / 'context.txt'

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
				'c': templates.Inherit(transform_tool_name),
				'c++': templates.Inherit(transform_tool_name),
				'objective-c': templates.Inherit(transform_tool_name),
				'c-header': templates.Inherit(transform_tool_name),
				'c++-header': templates.Inherit(transform_tool_name),

				transform_tool_name: {
					'command': __package__ + '.delineate',
					'interface': constructors.__name__ + '.clang',
					'method': 'python',
				}
			},

			'integrations': {
				'archive': templates.Clone,
				'partial': templates.Clone,
				'extension': templates.Clone,
				'executable': templates.Clone,
				'library': templates.Clone,
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
		'interface': constructors.__name__ + '.clang',
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
		'language': {'standard': {None: ['c++11']}}
	}))

	ccd.update_named_mechanism(route, 'clang', data)
	return route

def install(args, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the context for using LLVM respecting the intention.
	"""
	ctx_intention = ctx_params['intention']

	route = compiler(args, fault, ctx, ctx_route, ctx_params)

	if ctx_intention == 'delineation':
		sym, reqs = fragments(args, fault, ctx, ctx_route, ctx_params)

	ccd.update_named_mechanism(route, 'language-specifications', {
		'syntax': {
			'target-file-extensions': {
				'c': 'c',
				'c-header': 'h',

				'c++': 'cpp cxx c++',
				'c++-header': 'hpp hxx h++',

				'objective-c': 'm',
				'objective-c-header': 'hm',

				'objective-c++': 'mm',
			},
		}
	})

def main(inv:process.Invocation) -> process.Exit:
	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = files.Path.from_absolute(inv.environ['CONTEXT'])
	ctx = cc.Context.from_directory(ctx_route)
	ctx_params = ctx.index['context']
	install(inv.args, fault, ctx, ctx_route, ctx_params)
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
