"""
# Execution switch for spawning system processes controlled by a factor's image.
"""
import sys
import os
import contextlib
from collections.abc import Sequence
from typing import Callable

from fault.context import tools
from fault.system import process
from fault.system import files
from fault.system import identity
from fault.vector import recognition

from fault.system.execution import KInvocation
from fault.project import system as lsf

from ..root import query
from .context import resolve
from . import filters

restricted = {
	'--option': ('field-replace', True, 'field'),
}

required = {
	'-E': ('sequence-append', 'posix-environment'),

	'-A': ('field-replace', 'image-architecture'),
	'-X': ('field-replace', 'system-context-directory'),
	'-D': ('field-replace', 'product-directory'),

	'--system-name': ('field-replace', 'system-name'),
	'--system-architecture': ('field-replace', 'system-architecture'),
}

def product_variants(product):
	idr = product/'.images'
	for p in idr.fs_list()[0]:
		try:
			sys, arch = p.identifier.split('-', 1)
		except ValueError:
			continue
		yield lsf.types.Variants(sys, arch)

def system_execute(systemcontext, product, factor, path, image, argv):
	os.environ['SYSTEMCONTEXT'] = str(systemcontext)
	os.environ['PRODUCT'] = str(product)
	os.environ['FACTOR'] = str(factor)
	os.environ['FACTORIMAGE'] = str(image)
	os.execv(path, argv)

def export_execute(systemcontext, product, factor, argv):
	xfi = (product/'.export'/argv[0])
	xfi.fs_require('.x') # RequirementViolation
	system_execute(systemcontext, product, factor, xfi, '/var/empty/export', argv)

def configure(restricted, required, argv):
	sn, sa = identity.root_execution_context()
	config = {
		'posix-environment': [],
		'product-directory': None,
		'system-context-directory': None,
		'image-architecture': None,
		'system-name': sn,
		'system-architecture': sa,
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)
	return config, remainder

def main(inv:process.Invocation) -> process.Exit:
	config, remainder = configure(restricted, required, inv.argv)

	if config['product-directory'] is not None:
		pdr = process.fs_pwd() @ config['product-directory']
	else:
		pdr = process.fs_pwd()

	for x in config['posix-environment']:
		k, v = x.split('=')
		os.environ[k] = v

	# Identify the system context to use to process factors.
	origin, systemctx = resolve(config['system-context-directory'], product=pdr)

	if not remainder:
		sys.stderr.write("no factor designated\n")
		return inv.exit(249)

	# Try fast path; .export/factor.path.
	try:
		export_execute(systemctx, pdr, remainder[0], remainder)
	except files.RequirementViolation:
		pass
	else:
		assert False # Expects violation or os.execv error.

	# Configured Factor Context and lookup image.
	factors = lsf.Context()
	factors.connect(pdr)
	factors.load()
	factors.configure()

	fpathstr = remainder[0]
	fpath = lsf.types.factor@fpathstr
	product, project, prf = factors.split(fpath)
	for v in product_variants(product.route):
		img = product.image(v, project.factor, prf)
		if img.fs_type() != 'void':
			break
	else:
		sys.stderr.write(str(product.route) + "/" + fpathstr + " has no image\n")
		return inv.exit(248)

	if v == lsf.types.Variants(*identity.root_execution_context()):
		# Host executable.
		system_execute(systemctx, product.route, fpathstr, img, img, remainder)
		assert False # os.execv did not replace process image.

	system = lsf.Context()
	system.connect(systemctx)
	system.load()
	system.configure()
	sysexe = 'machines.execution.'
	sysexe += v.system
	sysexe += '-'
	sysexe += v.architecture
	sysvars = lsf.types.Variants(config['system-name'], config['system-architecture'])

	sysproduct, sysproject, sysfactor = system.split(lsf.types.factor@sysexe)
	sysdispatch = sysproduct.image(sysvars, sysproject.factor, sysfactor)
	sysdispatch.fs_require('.x') # machines.execution.variants Not an executable.

	system_execute(systemctx, product.route, fpathstr, sysdispatch, img, remainder)

	sys.stderr.write("os.execv did not replace process image\n")
	return inv.exit(254)
