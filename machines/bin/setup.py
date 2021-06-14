"""
# Extend construction contexts toolchains for targeting the system's machine.
"""
import sys
import importlib
import itertools

from fault.system import process
from fault.system import python
from fault.system import files

from ...factors import data as ccd
from ...factors import cc
from ...factors import constructors

from .. import query

# Construction Context modules.
from ..cc import host
from ..cc import llvm

def install(route, ctx, fault, args):
	"""
	# Initialize the tooling for arbitrary intentions contexts.
	"""

	intention = ctx.index['context']['intention']
	mech = (route / 'mechanisms' / 'fault.host')
	imp = python.Import.from_fullname(__package__).container

	data = host.dynamic(query.default_library_paths)
	data = {'host': data}
	ccd.update_named_mechanism(mech, 'root', data)
	ccd.update_named_mechanism(mech, 'path-setup', {'context':{'path':['host']}})

	route = llvm.compiler(args, fault, ctx, route, ctx.index['context'])
	if intention == 'delineation':
		sym, reqs = llvm.delineate(args, fault, ctx, route, ctx.index['context'])

def main(inv:process.Invocation) -> process.Exit:
	inv.imports({'FAULT_CONTEXT_NAME'})

	fault = inv.environ.get('FAULT_CONTEXT_NAME', 'fault')
	ctx_route = files.Path.from_absolute(inv.argv[0])
	ctx = cc.Context.from_directory(ctx_route)

	install(ctx_route, ctx, fault, inv.argv[1:])
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
