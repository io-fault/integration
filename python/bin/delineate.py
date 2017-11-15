"""
# Delineate a Python module.

# Emits serialized Fragments to standard out of the selected Python module.
"""

import sys
from fault.system import libfactor
from fault.system import library as libsys
from fault.routes import library as libroutes
from .. import xml

def main(inv:libsys.Invocation):
	module_fullname, = inv.args

	r = libroutes.Import.from_fullname(module_fullname)
	w = sys.stdout.buffer.write
	wl = sys.stdout.buffer.writelines

	ctx = xml.Context(r)
	module = r.module(trap=False)
	module.__factor_composite__ = libfactor.composite(r)

	w(b'<?xml version="1.0" encoding="utf-8"?>')
	i = ctx.serialize(module)
	wl(i)
	sys.stdout.flush()
	sys.exit(0)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())
