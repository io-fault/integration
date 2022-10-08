"""
# Factor processing operations for build, test, delineate, and analyze.
"""
import sys
import os
from collections.abc import Set

from fault.time.sysclock import now

from fault.context import tools
from fault.project import system as lsf
from fault.system import files

from fault.transcript import terminal
from fault.transcript import execution
from fault.transcript.io import Log
from fault.transcript.metrics import Procedure
from fault.project import graph

from . import system

# Initialize workspace environment and project index.
def initialize(wkenv:system.Environment, config, command, *argv):
	from . import initialization

	if initialization.root(wkenv, config['intentions'], relevel) >= 0:
		summary = "workspace context initialized\n"
	else:
		summary = "workspace directory already exists\n"

	return summary

class SQueue(object):
	"""
	# Queue implementation providing completion signalling interfaces consistent
	# with &graph.Queue.
	"""

	def __init__(self, sequence):
		self.items = list(sequence)
		self.count = len(self.items)

	def take(self, i):
		r = self.items[:i]
		del self.items[:i]
		return r

	def finish(self, *items):
		pass

	def terminal(self):
		return not self.items

	def status(self):
		return (self.count - len(self.items), self.count)

def plan_testing(wkenv:system.Environment, intention:str, argv, pcontext:lsf.Context, identifier):
	"""
	# Create an invocation for processing the project from &pcontext selected using &identifier.
	"""
	from fault.system.execution import KInvocation
	pj = pcontext.project(identifier)
	project = pj.factor

	from system.root import query
	exeenv, exepath, xargv = query.dispatch('python')
	xargv.append('-d')

	if argv:
		kwcheck = (lambda x: check_keywords(argv, x))
	else:
		kwcheck = (lambda x: True) # Always true if unconstrainted

	for (fp, ft), fd in pj.select(lsf.types.factor@'test'):
		if not fp.identifier.startswith('test_') or not kwcheck(fp):
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

# Build the product or a project set.
def plan_processing(wkenv, command, intentions, argv, ident, /, link='metrics'):
	from system.root.query import dispatch
	from fault.system.execution import KInvocation

	env, exepath, xargv = dispatch('factors-cc')

	cache = wkenv.build_cache
	ccs = [wkenv.work_construction_context]
	pj = wkenv.work_project_context.project(ident)

	for ccontext in ccs:
		fpath = str(pj.factor)

		cmd = xargv + [
			str(ccontext), 'persistent', str(cache),
			':'.join(intentions) + '@' + link,
			str(wkenv.work_product_route), str(pj.factor)
		]
		ki = KInvocation(cmd[0], cmd)
		yield (fpath, (), None, ki)

def construct(wkenv:system.Environment,
		command:str,
		intentions:Set[str],
		relevel,
		limit, control, projectvector
	):
	from fault.transcript import proctheme
	wd = wkenv.work_product_route
	cc = wkenv.work_construction_context

	monitors, summary = terminal.aggregate(control, proctheme, limit, width=180)
	i = tools.partial(plan_processing, wkenv, command, intentions, [])

	if projectvector is not None:
		q = SQueue(projectvector)
	else:
		q = graph.Queue()
		q.extend(wkenv.work_project_context)

	meta = Log.stderr()
	log = Log.stdout()

	xid = 'build'
	log.xact_open(xid, "FPI: %s %s %s" %(command, str(wd), str(cc)), {})
	try:
		execution.dispatch(meta, log, i, control, monitors, summary, "FPI", q,)
	finally:
		log.xact_close(xid, summary.synopsis(), {})

def coherency(wkenv:system.Environment,
		intentions, limit, control, pjv,
	):
	from fault.transcript import fatetheme

	# Project Context
	metrics = Procedure.create()
	monitors, summary = terminal.aggregate(control, fatetheme, limit, width=160)
	status = (control, monitors, summary)
	xc = wkenv.work_execution_context

	meta = Log.stderr()
	log = Log.stdout()

	for intent in intentions:
		xid = 'test/' + intent
		log.xact_open(xid, "Testing %s %s" %(intent, str(xc)), {})
		try:
			os.environ['INTENTION'] = intent

			# The queues have state, so they must be rebuilt for each intention.
			if pjv is not None:
				q = SQueue(pjv)
			else:
				q = graph.Queue()
				q.extend(wkenv.work_project_context)

			i = tools.partial(plan_testing, wkenv, intent, [], wkenv.work_project_context)

			execution.dispatch(meta, log, i, control, monitors, summary, "Fates", q,)
			metrics += summary.profile()[-1]
		finally:
			summary.title('Fates', intent)
			log.xact_close(xid, summary.synopsis(), {})

def configure(wkenv, lanes, relevel, argv):
	wkenv.load()

	lanes = int(lanes)
	os.environ['FPI_REBUILD'] = str(relevel)
	os.environ['F_PRODUCT'] = str(wkenv.work_product_route)

	cc = wkenv.work_construction_context
	projectvector = None
	if argv and argv[0] != '.':
		try:
			projectvector = [
				wkenv.work_project_context.split(x)[1].identifier
				for x in map(lsf.types.factor.__matmul__, argv)
			]
		except LookupError:
			projectvector = [
				pj.identifier for pj in wkenv.work_project_context.iterprojects()
			]

	limit = min(lanes, len(projectvector) if projectvector is not None else lanes)
	control = terminal.setup()
	control.configure(limit+1)

	return limit, control, projectvector

def check_keywords(keywords, name, Table=str.maketrans('_.-', '   ')):
	name_str = str(name)
	name_set = set(str(name).translate(Table).split())
	empty_constraints = 0

	for k in keywords:
		ccode = k[:1]

		if ccode == '@':
			if name_str == k[1:]:
				return True
		elif ccode == '.':
			if name_str.endswith(k[1:]):
				return True
		elif ccode == '+':
			# Whitelist
			if k[1:] in name_set:
				return True
		elif ccode == '-':
			# Blacklist
			if k[1:] in name_set:
				return False
		elif k in name_str:
			return True
		else:
			if k.strip() == '':
				empty_constraints += 1

	# False, normally. True when all the keywords were whitespace.
	return len(keywords) == empty_constraints

def build(wkenv:system.Environment,
		intentions:Set[str],
		relevel, lanes, argv
	):
	# Command used to process factors for execution.
	limit, control, pjv = configure(wkenv, lanes, relevel, argv)
	construct(wkenv, 'build', intentions, relevel, limit, control, pjv)

def delineate(wkenv:system.Environment,
		relevel, lanes, argv
	):
	# Command used to process factors for introspection and documentation.
	limit, control, pjv = configure(wkenv, lanes, relevel, argv)
	construct(wkenv, 'delineate', {'delineated'}, relevel, limit, control, pjv)

def analyze(wkenv:system.Environment,
		relevel,
		lanes,
		argv
	):
	# Command used to process factors for analysis.
	limit, control, pjv = configure(wkenv, lanes, relevel, argv)
	construct(wkenv, 'analyze', {'analysis'}, relevel, limit, control, pjv)

def measure(wkenv:system.Environment,
		intentions:Set[str],
		relevel,
		lanes,
		argv,
	):
	# Command used to process factors for measurement.
	limit, control, pjv = configure(wkenv, lanes, relevel, argv)

	# Delineate sources; intentions is irrelevant here and substituted with 'delineated'.
	construct(wkenv, 'measure/delineate', {'delineated'}, relevel, limit, control, pjv)

	# Build and Test the cited intentions.
	construct(wkenv, 'measure/build', intentions, relevel, limit, control, pjv)
	coherency(wkenv, intentions, limit, control, pjv)

	# Aggregate metrics from syntax measurements and trapped test runtime data.
	construct(wkenv, 'measure/report', {'metrics'}, relevel, limit, control, pjv)

def test(
		wkenv:system.Environment,
		intentions:Set[str],
		relevel:int,
		lanes:int,
		argv,
	):
	limit, control, pjv = configure(wkenv, lanes, relevel, argv)
	coherency(wkenv, intentions, limit, control, pjv)
