"""
Validate a project as functioning by performing its tests against the *active variant*.
"""
import os
import sys
import functools
import collections
import signal

from ...system import library as libsys
from ...system import libcore
from ...routes import library as libroutes
from .. import libharness

# The escapes are used directly to avoid dependencies.
exits = {
	'explicit': '\x1b[38;5;237m' 'x' '\x1b[0m',
	'skip': '\x1b[38;5;237m' 's' '\x1b[0m',
	'return': '\x1b[38;5;235m' '.' '\x1b[0m',
	'pass': '\x1b[38;5;235m' '.' '\x1b[0m',
	'divide': '\x1b[38;5;237m' '/' '\x1b[0m',
	'fail': '\x1b[38;5;196m' '!' '\x1b[0m',
	'core': '\x1b[38;5;202m' '!' '\x1b[0m',
	'expire': '\x1b[38;5;202m' '!' '\x1b[0m',
}

class Harness(libharness.Harness):
	"""
	The collection and execution of a series of tests for the purpose
	of validating a configured build.

	This harness executes many tests in parallel. Validation should be quick
	and generally quiet.
	"""
	concurrently = staticmethod(libsys.concurrently)

	def __init__(self, package, status, role='optimal'):
		super().__init__(package, role=role)
		self.status = status
		self.metrics = collections.Counter() # For division.
		self.tests = []

	def dispatch(self, test):
		# Run self.seal() in a fork
		seal = self.concurrently(lambda: self.seal(test))
		self.tests.append(seal)

	def complete(self, test):
		l = []
		result = test(status_ref = l.append)

		if result is None:
			result = {-1: 1}

		pid, status = l[0]

		if os.WCOREDUMP(status):
			result = {-1: 1}
			fate = 'core'
		elif not os.WIFEXITED(status):
			# redrum
			try:
				os.kill(pid, signal.SIGKILL)
			except OSError:
				pass

		self.metrics.update(result)

	def seal(self, test):
		self.status.write('\x1b[38;5;234m' '>' '\x1b[0m')
		self.status.flush() # Clear local buffers before fork.

		try:
			signal.signal(signal.SIGALRM, test.timeout)
			signal.alarm(8)

			with test.exits:
				test.seal()
		finally:
			signal.alarm(0)
			signal.signal(signal.SIGALRM, signal.SIG_IGN)

		if isinstance(test.fate, self.libtest.Divide):
			# Descend. Clear in case of subdivide.
			self.metrics.clear()
			del self.tests[:]

			# Divide returned the gathered tests,
			# dispatch all of them and wait for completion.

			divisions = test.fate.content
			self.execute(divisions, ())
			for x in self.tests:
				self.complete(x)

			self.status.write(exits['divide'])
			return dict(self.metrics)
		else:
			fate = test.fate.__class__.__name__.lower()
			self.status.write(exits[fate])
			return {test.fate.impact: 1}

def main(package, modules, role='optimal'):
	red = lambda x: '\x1b[38;5;196m' + x + '\x1b[0m'
	green = lambda x: '\x1b[38;5;46m' + x + '\x1b[0m'

	sys.dont_write_bytecode = True
	root = libroutes.Import.from_fullname(package)

	if getattr(root.module(), '__factor_type__', None) == 'context':
		pkgset = root.subnodes()[0]
		pkgset.sort()
	else:
		pkgset = [root]

	failures = 0

	for pkg in pkgset:
		sys.stderr.write(str(pkg) + ': ^')
		sys.stderr.flush()

		p = Harness(str(pkg), sys.stderr, role=role)
		p.execute(p.root(pkg), [])
		for x in p.tests:
			p.complete(x)

		f = p.metrics.get(-1, 0)
		sys.stderr.write(';\r')
		if not f:
			sys.stderr.write(green(str(pkg)))
		else:
			sys.stderr.write(red(str(pkg)))

		sys.stderr.write('\n')
		sys.stderr.flush()

		failures += f

	raise SystemExit(min(failures, 201))

if __name__ == '__main__':
	command, package, *modules = sys.argv
	try:
		os.nice(10)
	except:
		# Ignore nice() failures.
		pass

	with libcore.constraint():
		libsys.control(main, package, modules)
