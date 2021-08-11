"""
# Executable factor index for &fault.system.bin.tool bindings.
"""
import importlib
from ... import __name__ as context_name
from fault.system import process

index = {
	'delineate-kleptic-text': context_name + '.chapters.bin.delineate',
	'text-cc': context_name + '.chapters.bin.compile',
	'python-cc': context_name + '.python.bin.compile',
	'factors-cc': context_name + '.factors.bin.construct',
	'products-cc': context_name + '.products.bin.control',
}

def activate(factor, element, interface=None):
	importlib.import_module(factor).extend(lambda x: (index[x], 'main'))

def main(inv:process.Invocation) -> process.Exit:
	import sys
	for item in index.items():
		sys.stdout.write("%s %s\n" % item)
