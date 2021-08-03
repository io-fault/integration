"""
# Extend metrics or delineation construction contexts with adapters built against the selected
# LLVM implementation.

# The setup process will modify the tool support context referenced by the target construction context.
# The coverage tooling requires various LLVM libraries for extracting counters,
# and the delineation tooling requires (system/library)`libclang` and clang includes.
"""

import os
import sys
import importlib
import itertools
import pickle

from fault.system import files
from fault.text.bin import ifst

from ..llvm import query

project_infra = b"""! CONTEXT:
	/protocol/
		&<http://if.fault.io/project/infrastructure>

/fault-c-interfaces/
	- &<http://fault.io/integration/machine/include>
	- &<http://fault.io/integration/python/include>
"""

# Implementation
sdk_deline = b"""
/sdk-llvm/
	- &<http://fault.io/integration/machine/llvm>
"""

def delineatation(project_name, route):
	"""
	# Initialize the factors for clang delineation.
	"""
	from ..llvm import delineate

	llvm_path = (route.from_absolute(__file__) * project_name)
	pdpath = route@'local'
	pjpath = pdpath/project_name

	ifst.instantiate((pjpath/'bin'/'clang-delineate'), llvm_path/'formulas.txt', 'delineation')
	infra = project_infra + sdk_deline
	(pjpath/'infrastructure.txt').fs_store(infra)

	sdk_product = str(files.Path.from_absolute(__file__) ** 5) + "\n"
	(pdpath/'.product'/'CONNECTIONS').fs_init(sdk_product.encode('utf-8'))

	prefix = files.Path.from_absolute(syscmd) ** 2
	libdir = prefix / 'lib'
	incdir = prefix / 'include'
	dep = (incdir, libdir, 'clang')

	return ('llvm-delineation-libclang', query.delineation(*(map(str, dep))))

def coverage(project_name, route, args):
	"""
	# Initialize the factors for clang coverage.
	"""
	llvm_path = (route.from_absolute(__file__) * project_name)
	pdpath = route@'local'
	pjpath = pdpath/project_name

	ifst.instantiate((pjpath/'extensions'/project_name), llvm_path/'formulas.txt', 'instrumentation')

	# Get instrumentation support flags.
	source, merge, export, projections = query.instrumentation(*args)
	fsyms = (ctx_route / 'context' / 'symbols' / 'llvm-coverage-instrumentation')
	fsyms.fs_store(pickle.dumps(projections))
