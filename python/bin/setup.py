"""
# Extend metrics or delineation construction contexts with adapters built against the selected
# Python implementation.
"""
import sys
import importlib
import itertools

from fault.system import library as libsys
from fault.routes import library as libroutes
from ....factors import cc

tool_name = 'python'

delineate_template = {
	'command': __package__ + '.delineate',
	'interface': cc.__name__ + '.package_module_parameter',
	'method': 'python',
	'name': 'delineate-python-source',
	'redirect': 'stdout'
}

telemetry_layer = {
	'telemetry': tool_name,
}

def add_delineate_mechanism(route:libroutes.File, tool_name:str):
	"""
	# Add delineation mechanism.
	"""

	return cc.update_named_mechanism(route, tool_name, delineate_template)

def delineation(inv, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the syntax tooling for delineation contexts.
	"""
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])

	args = inv.args
	mechanism_layer = {
		'bytecode.python': {
			'transformations': {
				'python': delineate_template,
			}
		}
	}

	cc.update_named_mechanism(ctx_route / 'mechanisms' / 'intent.xml', tool_name, mechanism_layer)
	return inv.exit(0)

def instantiate_software(dst, package, name, template, type, fault='fault'):
	# Initiialize llvm instrumentation or delineation tooling inside the target context.
	ctxpy = dst / 'lib' / 'python'

	command = [
		"python3", "-m",
		fault+'.text.bin.ifst',
		str(ctxpy / package / name),
		str(template), 'context', type,
	]

	print(command)
	pid, status, data = libsys.effect(libsys.KInvocation(sys.executable, command))
	if status != 0:
		sys.stderr.write("! ERROR: tool instantiation failed\n")
		sys.stderr.write("\t/command\n\t\t" + " ".join(command) + "\n")
		sys.stderr.write("\t/status\n\t\t" + str(status) + "\n")

		sys.stderr.write("\t/message\n")
		sys.stderr.buffer.writelines(b"\t\t" + x + b"\n" for x in data.split(b"\n"))
		raise SystemExit(1)

def metrics(inv, fault, ctx, ctx_route, ctx_params):
	"""
	# Initialize the instrumentation tooling for metrics contexts.
	"""
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])
	mech = (ctx_route / 'mechanisms' / 'intent.xml')

	args = inv.args

	imp = libroutes.Import.from_fullname(__package__).container
	instantiate_software(ctx_route, 'f_telemetry', tool_name, imp / 'templates', 'metrics')

	mechanism_layer = {
		'bytecode.python': {
			'transformations': {
				'python': telemetry_layer,
			}
		}
	}
	cc.update_named_mechanism(ctx_route / 'mechanisms' / 'intent.xml', tool_name, mechanism_layer)

	# Register tool and probe constructor.
	from .. import library
	data = {
		'constructor': '.'.join((library.__name__, library.Probe.__qualname__)),
	}
	tool_data_path = ctx_route / 'parameters' / 'tools' / (tool_name + '.xml')
	cc.Parameters.store(tool_data_path, None, data)

	return inv.exit(0)

def main(inv:libsys.Invocation) -> libsys.Exit:
	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = libroutes.File.from_absolute(inv.environ['CONTEXT'])
	ctx = cc.Context.from_directory(ctx_route)
	ctx_params = ctx.parameters.load('context')[-1]
	ctx_intention = ctx_params['intention']

	if ctx_intention == 'metrics':
		return metrics(inv, fault, ctx, ctx_route, ctx_params)
	elif ctx_intention == 'delineation':
		return delineation(inv, fault, ctx, ctx_route, ctx_params)
	else:
		sys.stderr.write("! ERROR: unsupported context with %r intention\n" %(ctx_intention,))
		return inv.exit(1)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system(environ=('FAULT_CONTEXT_NAME', 'CONTEXT')))
