"""
# Extend metrics or delineation construction contexts with adapters built against the selected
# Python implementation.
"""
import sys
import importlib
import itertools
import pickle

from fault.system import execution as libexec
from fault.system import process
from fault.system import files
from fault.system import python

from ...factors import constructors
from ...factors import cc
from ...factors import data as ccd
from ...root import query

tool_name = 'python'
name = 'fault.python'

def identification():
	"""
	# Collect the python reference parameter from the &sysconfig module.
	"""

	from importlib.machinery import EXTENSION_SUFFIXES
	version = '.'.join(map(str, sys.version_info[:2]))
	abi = sys.abiflags

	cache_tag = getattr(sys.implementation, 'cache_tag')
	if cache_tag is None:
		cache_tag = sys.implementation.name + version.replace('.', '') + abi

	triplet = cache_tag + abi + '-' + sys.platform

	return {
		'identifier': triplet,
		'version': version,
		'abi': abi,
		'tag': cache_tag,
		'implementation': sys.implementation.name,
		'executable': sys.executable,
		'extension-suffix': EXTENSION_SUFFIXES[0],
	}

def instantiate_software(dst, package, name, template, type, fault='fault'):
	from fault.text.bin import ifst
	ctxpy = dst / 'lib' / 'python'
	return ifst.instantiate(
		(ctxpy / package / name),
		(template),
		type,
	)

def compilation(domain, system, architecture, command):
	"""
	# Generate mechanisms for compiling Python libraries.
	"""
	from . import compile

	return {
		'variants': {
			'system': system,
			'architecture': architecture,
		},
		'transformations': {
			# Effectively copy source files as &.bin.compile
			# takes Python source.
			'python': constructors.Projection,
		},

		'integrations': {
			'http://if.fault.io/factors/python.module':
				constructors.Inherit('tool:pyc-subprocess'),

			# Likely unused in cases where the executing Python is the target Python.
			'tool:pyc-subprocess': {
				'interface': compile.__name__ + '.subprocess_bytecode_compiler',
				'factor': __package__ + '.compile',
				'command': command,
				'tool': ['compile-python-source'],
			},
		},
	}

def delineation(domain, system, architecture, command):
	"""
	# Initialize the syntax tooling for delineation contexts.
	"""

	return {
		'variants': {
			'system': system,
			'architecture': architecture,
		},

		'transformations': {
			'python': constructors.Inherit('tool:pyd-subprocess'),
			'tool:pyd-subprocess': {
				'interface': constructors.__name__ + '.delineation',
				'factor': __package__ + '.delineate',
				'command': command,
				'tool': ['delineate-python-source'],
			},
		},

		'integrations': {
			'http://if.fault.io/factors/python.module':
				constructors.Clone,
		},
	}

def coverage(route, ctx, settings, domain):
	"""
	# Initialize the tooling for coverage contexts.
	"""
	imp = python.Import.from_fullname(__package__).container
	tmpl_path = imp.file().container / 'templates' / 'context.txt'
	return {}

default_tool = (query.libexec()/'fault-dispatch')

def install(route, ctx, settings):
	"""
	# Initialize the context for its configured intention.
	"""
	tool = settings.get('tool', default_tool)
	ctx_intention = ctx.index['context']['intention']
	host_system = ctx.index['host']['system']

	mechfile = route / 'mechanisms' / name

	pydata = identification()
	arch = pydata['tag'].replace('-', '')
	domain_id = pydata['identifier']

	if ctx_intention == 'delineation':
		data = delineation(domain_id, host_system, arch, str(tool))
		ccd.update_named_mechanism(mechfile, 'root', {domain_id: data})
	else:
		data = compilation(domain_id, host_system, arch, str(tool))
		ccd.update_named_mechanism(mechfile, 'root', {domain_id: data})

		if ctx_intention == 'coverage':
			layer = coverage(route, ctx, settings, domain_id)
			ccd.update_named_mechanism(mechfile, 'instrumentation-control', layer)

	ccd.update_named_mechanism(mechfile, 'path-setup', {'context': {'path': [domain_id]}})

def main(inv:process.Invocation) -> process.Exit:
	route = files.Path.from_absolute(inv.argv[0])
	settings = dict(zip(inv.argv[1::2], inv.argv[2::2]))
	ctx = cc.Context.from_directory(route)
	install(route, ctx, settings)
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
