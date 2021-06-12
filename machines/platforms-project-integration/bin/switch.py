"""
# Execute a factor by using the configured plan for the identified architecture.
"""
import os
import sys
import itertools

from fault.system import files
from fault.system import process
from fault.system import execution
from fault.system import query
from fault.project import system as lsf

INTENTION='optimal'

def options(argv):
	i = 0
	farch = None
	parch = None
	for i, v in enumerate(argv):
		opt = v[:2]

		if opt == '-A':
			farch, *parch = v[2:].split('=', 1)
			if parch:
				parch = parch[0]
			else:
				parch = farch
		else:
			break

	return (farch, parch), argv[i:]

def main(inv:(process.Invocation)) -> (process.Exit):
	(factor_a, execute_a), argv = options(inv.argv)
	product_path, factor_path, *xargv = argv

	pfi = query.platform()

	# Project Context
	pdr = files.Path.from_path(product_path)
	ctx = lsf.Context()
	ctx.connect(pdr)
	ctx.load()

	pd, pj, fp = ctx.split(factor_path)

	os.environ['FACTOR'] = factor_path
	os.environ['F_SYSTEM'] = pfi.system
	os.environ['F_PRODUCT'] = str(pdr)
	os.environ['F_PROJECT'] = str(pj.factor)
	os.environ['F_PATH'] = str(fp)
	os.environ['F_PROJECT_ID'] = str(pj.identifier)

	# Scan for integrals executable by the platform in priority order.
	i = None
	for arch in pfi.architectures:
		variants = {'system': pfi.system, 'architecture': arch, 'intention': INTENTION}
		i = pj.image(variants, fp)
		if i.fs_type() != 'void':
			factor_a = arch
			break
	else:
		raise Exception("no architecture available for the selected factor")

	assert i is not None
	os.environ['F_ARCHITECTURE'] = factor_a
	os.environ['F_IMAGE'] = str(i)

	envvars, exe_path, argv = pfi.prepare(arch, factor_path, xargv)

	os.environ.update(envvars)
	os.execv(exe_path, argv)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
