"""
# Testing and static analysis support.
"""
import os
from collections.abc import Iterable, Sequence

from fault.context import tools
from fault.system import files

from fault.time import system as time

from fault.transcript import terminal
from fault.transcript import fatetheme
from fault.transcript import execution

from fault.system.execution import KInvocation
from fault.project import system as lsf

from ..root import query
from . import filters

##
# Test types associated with their identifying prefix.
test_type_map = {
	'integration': 'i-',
	'unit': 'u-',
	'performance': 'p-',
	'explicit': 'x-',
	'static': 's-',
}

# fault.vector restricted parameters dictionary.
test_type_set_control = {
	'--integration': ('set-add', 'integration', 'test-types'),
	'--unit': ('set-add', 'unit', 'test-types'),
	'--performance': ('set-add', 'performance', 'test-types'),
	'--explicit': ('set-add', 'explicit', 'test-types'),
	'--static': ('set-add', 'static', 'test-types'),

	'-i': ('set-add', 'integration', 'test-types'),
	'-u': ('set-add', 'unit', 'test-types'),
	'-p': ('set-add', 'performance', 'test-types'),
	'-x': ('set-add', 'explicit', 'test-types'),
	'-s': ('set-add', 'static', 'test-types'),

	'-I': ('set-discard', 'integration', 'test-types'),
	'-U': ('set-discard', 'unit', 'test-types'),
	'-P': ('set-discard', 'performance', 'test-types'),
	'-X': ('set-discard', 'explicit', 'test-types'),
	'-S': ('set-discard', 'static', 'test-types'),
}

required = {
	'-f': ('sequence-append', 'test-filters')
}

options = (
	test_type_set_control, required
)

def plan(prefixes, keywords, factors:lsf.Context, identifier):
	"""
	# Create an invocation for processing the project from &factors selected using &identifier.
	"""

	from fault.system.execution import KInvocation
	pj = factors.project(identifier)
	project = pj.factor

	from system.root import query
	exeenv, exepath, xargv = query.dispatch('python')
	xargv.append('-d')

	if keywords:
		kwcheck = (lambda x: filters.check_keywords(keywords, x))
	else:
		kwcheck = (lambda x: True) # Always true if unconstrainted

	for (fp, ft), fd in pj.select(lsf.types.factor@'test'):
		if not fp.identifier[:2] in prefixes:
			continue
		if not kwcheck(fp):
			continue

		pj_fp = str(project)
		test_fp = str(fp)
		xid = '/'.join((pj_fp, test_fp))

		cmd = xargv + [
			'fault.test.bin.coherence',
			pj_fp, test_fp
		]
		env = dict(os.environ)
		env.update(exeenv)
		env['F_PROJECT'] = str(project)
		ki = KInvocation(cmd[0], cmd, environ=env)

		yield (pj_fp, (test_fp,), xid, ki)

def test(exits, meta, log, config, fx, cc, pdr:files.Path, argv):
	"""
	# Analyze the software's coherency.
	"""

	from fault.transcript import terminal
	from fault.transcript import fatetheme

	os.environ['PRODUCT'] = str(pdr)
	os.environ['F_PRODUCT'] = str(cc)
	os.environ['F_EXECUTION'] = str(fx)

	test_prefixes = set([
		test_type_map[x] for x in config['test-types'] or {'integration', 'unit'}
	])
	lanes = int(config['processing-lanes'])

	# Project Context
	factors = lsf.Context()
	pd = factors.connect(pdr)
	factors.load()
	factors.configure()

	# Allocate and configure control and monitors.
	control = terminal.setup()
	control.configure(lanes+1)

	monitors, summary = terminal.aggregate(control, fatetheme, lanes, width=160)

	try:
		log.xact_open('coherency', "Revealing fates.", {})

		q = filters.projectgraph(factors, argv)
		local_plan = tools.partial(plan, test_prefixes, config['test-filters'], factors)
		execution.dispatch(meta, log, local_plan, control, monitors, summary, "Fates", q, opened=True)
	finally:
		log.xact_close('coherency', summary.synopsis('Fates'), {})
		control.clear()
		control.flush()
