"""
# Extend metrics or inspect construction contexts with adapters built against the selected LLVM implementation.

# The setup process will modify the tool support context referenced by the target construction context.
# The instrumentation tooling requires various LLVM libraries for extracting coverage counters,
# and the inspection tooling requires (system/library)`libclang` and clang includes.

# [ Engineering ]
# The implementation depends on the Construction Context instance being
# that of &fault.development.cc. While the engine may need to be
# Python, the context implementation should be variable such that context
# extension interface are used rather than presuming the implementation.
"""
import sys
import importlib
import itertools
from .. import query

from fault.system import library as libsys
from fault.routes import library as libroutes
from fault.development import cc

transform_tool_name = 'tool:llvm-clang'
tool_name = 'llvm'

def detect_profile_library(mechanism, architectures):
	"""
	# Given an `tool:llvm-clang` mechanism and a sequence of architecures, discover
	# the appropriate profile library to link against when building targets
	# that consist of LLVM instrumented sources.
	"""
	cclib = libroutes.File.from_absolute(mechanism['libraries'])
	files = cclib.subnodes()[1]
	profile_libs = [x for x in files if 'profile' in x.identifier]

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

	if not profile_lib.exists():
		profile_lib = None

	return profile_lib

clang_instrumentation_options = ('-fprofile-instr-generate', '-fcoverage-mapping')

def rewrite_mechanisms(route:libroutes.File, tool_name:str):
	"""
	# Given a route to a core mechanism file in a metrics construction context,
	# update the file with the necessary information about the profile requirement
	# and the associated tooling.
	"""
	doc, merged = cc.Context.load_xml(route)
	data = cc.load_named_mechanism(route, tool_name)

	if not data:
		data = {
			'system': {
				'transformations': {
					'tool:llvm-clang': {
						'resources': {
							'profile': None
						},
						'options': [],
					},
				}
			}
		}

	instr_mech = merged['system']['transformations']['tool:llvm-clang']
	tool_data = data['system']['transformations']['tool:llvm-clang']

	# Add compilation arguments to generate instrumented objects.
	options = tool_data['options']
	for opt in clang_instrumentation_options:
		if opt not in options:
			options.append(opt)

	# Set profile entry if none.
	stored_reqs = instr_mech['resources']
	if stored_reqs.get('profile', None) is None:
		arch = merged['system']['architecture']
		profile = str(detect_profile_library(instr_mech, arch))
		tool_data['resources']['profile'] = profile

	# Note the telemtry tool.
	tool_data['telemetry'] = tool_name

	return cc.update_named_mechanism(route, tool_name, data)

def instantiate_software(dst, package, subpackage, name, template, type, fault='fault'):
	# Initiialize llvm instrumentation or inspection tooling inside the target context.
	ctxpy = dst / 'lib' / 'python'

	command = [
		"python3", "-m",
		fault+'.text.bin.ifst',
		str(ctxpy / package / subpackage / name),
		str(template), 'context', type,
	]

	pid, status, data = libsys.effect(libsys.KInvocation(sys.executable, command))
	if status != 0:
		sys.stderr.write("! ERROR: tool instantiation failed\n")
		sys.stderr.write("\t/command\n\t\t" + " ".join(command) + "\n")
		sys.stderr.write("\t/status\n\t\t" + str(status) + "\n")

		sys.stderr.write("\t/message\n")
		sys.stderr.buffer.writelines(b"\t\t" + x + b"\n" for x in data.split(b"\n"))
		raise SystemExit(1)

def inspect(inv, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the syntax tooling for inspect construction contexts.
	"""
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])

	args = inv.args

	imp = libroutes.Import.from_fullname(__package__).container
	tmpl = imp / 'templates'

	instantiate_software(ctx_route, 'f_syntax', 'bin', tool_name, tmpl, 'inspection')

	# Identify target parameter set.
	build_ctx = (ctx_route / 'context')
	root = build_ctx / 'parameters'

	llvm = {
		'command': __package__ + '.delineate',
		'interface': cc.__name__ + '.compiler_collection',
		'method': 'python',
		'redirect': 'stdout',
	}

	data = {
		'system': {
			'transformations': {
				'objective-c': llvm,
				'c++': llvm,
				'c': llvm,
				'c-header': llvm,
				'c++-header': llvm,
			}
		}
	}

	if not args:
		# Derive library and include locations from tool:llvm-clang command
		xml, merged = cc.Context.load_xml(build_ctx / 'mechanisms' / 'intent.xml')
		syscmd = merged['system']['transformations'][transform_tool_name]['command']
		prefix = libroutes.File.from_absolute(syscmd) ** 2
		libdir = prefix / 'lib'
		incdir = prefix / 'include'
		args = (incdir, libdir, 'clang')

	for k, a, v in query.inspection(*(map(str, args))):
		path = (build_ctx / 'parameters').extend(k.split('/')).suffix('.xml')
		cc.Parameters.store(path, a, v)

	cc.update_named_mechanism(ctx_route / 'mechanisms' / 'intent.xml', tool_name, data)

	return inv.exit(0)

def metrics(inv, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the instrumentation tooling for metrics contexts.
	"""
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])
	mech = (ctx_route / 'mechanisms' / 'intent.xml')

	args = inv.args

	imp = libroutes.Import.from_fullname(__package__).container
	tmpl = imp / 'templates'

	instantiate_software(ctx_route, 'f_telemetry', 'extensions', tool_name, tmpl, 'instrumentation')

	# Identify target parameter set.
	build_ctx = ctx_route / 'context'
	root = build_ctx / 'parameters'

	if not args:
		# Derive llvm-config location from tool:llvm-clang's 'command' entry.
		xml, merged = cc.Context.load_xml(mech)
		syscmd = merged['system']['transformations'][transform_tool_name]['command']
		args = (libroutes.File.from_absolute(syscmd).container / 'llvm-config',)

	for k, a, v in query.instrumentation(*args):
		path = root.extend(k.split('/')).suffix('.xml')
		cc.Parameters.store(path, a, v)

	# Inherit detected llvm-profdata path.
	# &..library.Probe needs this information in order to process
	# the raw profile data emitted to disk.

	b_params = cc.Parameters([root])
	name, auth, cov = b_params.load('llvm/coverage')

	from .. import library # For Probe constructor addressing.
	tool_data = ctx_route / 'parameters' / 'tools' / (tool_name + '.xml')
	cc.Parameters.store(tool_data, None, {
			'source': cov['source'],
			'merge': cov['merge'],
			'constructor': '.'.join((library.__name__, library.Probe.__qualname__)),
		}
	)
	rewrite_mechanisms(mech, tool_name)

	return inv.exit(0)

def main(inv:libsys.Invocation):
	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])
	ctx = cc.Context.from_directory(ctx_route)
	ctx_params = ctx.parameters.load('context')[-1]
	ctx_intention = ctx_params['intention']

	if ctx_intention == 'metrics':
		return metrics(inv, fault, ctx, ctx_route, ctx_params)
	elif ctx_intention == 'inspect':
		return inspect(inv, fault, ctx, ctx_route, ctx_params)
	else:
		sys.stderr.write("! ERROR: unsupported context with %r intention\n" %(ctx_intention,))
		return inv.exit(1)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
