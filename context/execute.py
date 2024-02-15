"""
# Executable factor index for &fault.system.tool bindings.
"""
import importlib
from .. import __name__ as context_name
from fault.system import process

index = {
	'archive-delineated': context_name + '.factors.delineated',
	'text-cc': context_name + '.chapters.compile',
	'python-cc': context_name + '.python.compile',
	'factors-cc': context_name + '.factors.construct',
	'products-cc': context_name + '.products.control',
	'pdctl': context_name + '.products.control',
	'fictl': context_name + '.products.control',
	'man': context_name + '.context.read',
	'error': context_name + '.factors.error',
}

def activate(factor, element, interface=None):
	importlib.import_module(factor).extend(lambda x: (index[x], 'main'))

def main(inv:process.Invocation) -> process.Exit:
	import sys
	for item in index.items():
		sys.stdout.write("%s %s\n" % item)
