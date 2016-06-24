"""
Test harness access for collecting metrics.

Invoking measure requires two or more command parameters. The first is the reporting
directory, for collected data, and the remainder being packages to test.
"""
import sys
import os
import functools

from .. import libmetrics

from ...routes import library as libroutes
from ...system import libcore

def main(work, target_dir, packages):
	target_fsdict = libmetrics.libfs.Dictionary.create(
		libmetrics.libfs.Hash('fnv1a_32', depth=1), target_dir
	)

	target_fsdict[b'metrics:packages'] = b'\n'.join(x.encode('utf-8') for x in packages)

	p = None
	for package in packages:
		p = libmetrics.Harness(work, target_fsdict, package, sys.stderr)
		p.execute(p.root(libroutes.Import.from_fullname(package)), ())
		# Build measurements.

	fct = os.environ.get('FAULT_COVERAGE_TOTALS')
	if fct:
		libmetrics.Harness.merge_instrumentation_metrics(work, fct)

	libmetrics.prepare(target_fsdict)

	raise SystemExit(0)

if __name__ == '__main__':
	import atexit
	target_dir, *packages = sys.argv[1:]
	if not packages:
		raise TypeError("command invoked with one parameter; requires: '.bin.measure target_dir packages ...'")

	# Setup temporary directory for instrumentation/coverage storage.
	if 'FAULT_COVERAGE_DIRECTORY' in os.environ:
		work = libroutes.File.from_absolute(os.environ['FAULT_COVERAGE_DIRECTORY'])
		work.init('directory')
	else:
		cm = libroutes.File.temporary()
		work = cm.__enter__()
		atexit.register(functools.partial(cm.__exit__, None, None, None))

	# Remove core constraints if any.
	cm = libcore.constraint(None)
	cm.__enter__()
	atexit.register(functools.partial(cm.__exit__, None, None, None))

	# Work CM is here and not further down because it needs to be global
	# The child processes raise replacements to control the context.
	llvm = (work / 'llvm')
	llvm.init('directory')

	# Adjust the profile file environment to a trap file.
	# The actual file is set before each test.
	os.environ['LLVM_PROFILE_FILE'] = str(llvm / 'trap.profraw')

	libmetrics.libsys.control(functools.partial(main, work, target_dir, packages))
