"""
# Testing and static analysis support.
"""
import os
import contextlib
from collections.abc import Iterable, Sequence

from fault.context import tools
from fault.vector import recognition
from fault.system import files
from fault.system import process

from fault.system.execution import KInvocation
from fault.project import system as lsf

from ..root import query
from . import filters
from . import context
from . import map

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
restricted = {
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
	'-f': ('sequence-append', 'test-filters'),
	'-x': ('field-replace', 'machines-context-name'),
	'-X': ('field-replace', 'system-context-directory'),

	'-D': ('field-replace', 'product-directory'),
	'-L': ('field-replace', 'processing-lanes'),
}

def plan(prefixes, keywords, factors:lsf.Context, ctl:map.Controls, identifier):
	"""
	# Create an invocation for processing the project from &factors selected using &identifier.
	"""

	pj = factors.project(identifier)
	project = pj.factor
	test_pd, test_project, test_path = factors.split((project ** 1) / 'defects')
	test_path = test_project.factor / project.identifier
	test_pj_str = str(test_project.factor)

	exeenv, exepath, xargv = query.dispatch('python')
	xargv.append('-d')

	if keywords:
		kwcheck = (lambda x: filters.check_keywords(keywords, x))
	else:
		kwcheck = (lambda x: True) # Always true if unconstrainted

	for (fp, ft), fd in test_project.select(lsf.types.factor@project.identifier):
		if not fp.identifier[:2] in prefixes:
			continue
		if not kwcheck(fp):
			continue

		pj_fp = str(project)
		test_fp = str(fp)
		xid = '/'.join((test_pj_str, test_fp))

		cmd = xargv + [
			'fault.test.analyze',
			str(test_project.factor), test_fp
		]
		env = dict(os.environ)
		env.update(exeenv)
		env['F_PROJECT'] = str(project)
		ki = KInvocation(cmd[0], cmd, environ=env)

		yield (pj_fp, (test_fp,), xid, ki)

def test(exits, meta, log, config, cc, pdr:files.Path, argv):
	"""
	# Perform runtime analysis using the selected factors.
	"""

	os.environ['PRODUCT'] = str(pdr)
	os.environ['F_PRODUCT'] = str(cc)

	test_prefixes = set([
		test_type_map[x] for x in config['test-types'] or {'integration', 'unit'}
	])
	lanes = int(config['processing-lanes'])

	# Configured Factor Context
	factors = lsf.Context()
	factors.connect(pdr)
	factors.load()
	factors.configure()

	ctl = map.Controls(
		log, meta,
		query.ipath / 'python',
		'fault.test.analyze',
		ctl_plan = tools.partial(plan, test_prefixes, config['test-filters'], factors),
		ctl_argv = [],
		ctl_transcript_type = 'test-fates',
		ctl_lanes = int(config['processing-lanes']),
		ctl_opened_frames = False,
		ctl_factor_types = None,
		ctl_open_title = 'Revealing',
		ctl_close_title = 'Fates',
		ctl_operating_title = 'Testing',
	)

	map.execute(exits, ctl, filters.projectgraph(factors, argv))

def configure(restricted, required, argv):
	"""
	# Root option parser.
	"""
	config = {
		'processing-lanes': '8',
		'machines-context-name': 'machines',
		'system-context-directory': None,
		'product-directory': None,

		'test-types': set(),
		'test-filters': [],
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def main(inv:process.Invocation) -> process.Exit:
	pwd = process.fs_pwd()

	config, remainder = configure(restricted, required, inv.argv)

	if config['product-directory']:
		pdr = files.Path.from_path(config['product-directory'])
	else:
		pdr = pwd

	# Identify the system context to use to process factors.
	origin, cc = context.resolve(config['system-context-directory'], product=pdr)

	with contextlib.ExitStack() as ctx:
		test(ctx, map.Log.stderr(), map.Log.stdout(), config, cc, pdr, remainder)
	return inv.exit(0)
