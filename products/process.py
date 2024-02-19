"""
# Product builds and tests for system integration.
"""
import os
from collections.abc import Iterable, Sequence

from fault.context import tools
from fault.system import files

from fault.transcript import terminal
from fault.transcript import proctheme
from fault.transcript import execution

from fault.system.execution import KInvocation
from fault.project import system as lsf

from ..root import query
from . import filters

options = (
	{
		'-O': ('set-add', 'optimal', 'features'),
		'-o': ('set-add', 'portable', 'features'),
		'-g': ('set-add', 'debug', 'features'),

		'-y': ('set-add', 'auxilary', 'features'),
		'-Y': ('set-add', 'capture', 'features'),

		'--profile': ('set-add', 'profile', 'features'),
		'--coverage': ('set-add', 'coverage', 'features'),

		# Reprocess levels.
		'-N': ('field-replace', -1, 'relevel'),
		'-n': ('field-replace', +0, 'relevel'),
		'-r': ('field-replace', +1, 'relevel'),
		'-R': ('field-replace', +2, 'relevel'),

		# Defaults to update when missing.
		'-u': ('field-replace', 'never', 'update-product-index'),
		'-U': ('field-replace', 'always', 'update-product-index'),
	},
	{}
)

def plan(command,
		cc:files.Path,
		factors:lsf.Context,
		features:Sequence[str],
		cachetype:str,
		cachepath:files.Path,
		identifier,
		executable=None,
		link=None,
	):
	"""
	# Create an invocation for processing &pj with &cc.
	"""

	pj = factors.project(identifier)
	project = pj.factor
	if executable is not None:
		env = dict()
		exepath = executable
		xargv = [executable]
	else:
		env, exepath, xargv = query.dispatch('factors-cc')

	if link is not None:
		metricslink = '@' + link
	else:
		metricslink = ''

	pj_fp = str(project)
	ki = KInvocation(xargv[0], xargv + [
		str(cc), cachetype, str(cachepath),
		':'.join(features) + metricslink,
		str(pj.product.route),
		pj_fp,
	])

	# Factor Processing Instructions
	yield (pj_fp, (), pj_fp, ki)

def integrate(exits, meta, log, config, fx, cc, pdr:files.Path, argv):
	"""
	# Complete build connecting requirements and updating indexes.
	"""

	from fault.transcript.metrics import Procedure
	zero = Procedure.create()
	os.environ['PRODUCT'] = str(pdr)
	os.environ['F_PRODUCT'] = str(cc)
	os.environ['F_EXECUTION'] = str(fx)
	os.environ['FPI_REBUILD'] = str(config['relevel'])

	xdelineate = config.get('disable-delineation', True) == False

	lanes = int(config['processing-lanes'])
	connections = []

	idx_update = config.get('update-product-index', 'missing')
	if idx_update != 'never':
		# Default for integrate is to update if it is missing.
		# This is different from &manipulate.delta's default.
		from . import manipulate
		if manipulate.index(lsf.Product(pdr), idx_update):
			meta.notice("updated (" + str(idx_update) + ") project index using the directory")

	cachetype = config['cache-type']
	if cachetype == 'transient':
		# Explicit transient, -c.
		cachepath = exits.enter_context(files.Path.fs_tmpdir())
	else:
		if config['persistent-cache']:
			# Explicit cache directory.
			cachepath = config['persistent-cache']
		elif (pdr/'.cache').fs_type() == 'directory':
			# Cache directory present in product.
			cachepath = (pdr/'.cache')
		else:
			# Transient fallback.
			cachetype = 'transient'
			cachepath = exits.enter_context(files.Path.fs_tmpdir())

	# Project Context
	factors = lsf.Context()
	pd = factors.connect(pdr)
	factors.load()
	factors.configure()

	projects = argv
	features = sorted(list(config['features']))

	# Signal factors.construct to create links to measurements.
	if cachetype == 'persistent':
		metricslink = 'metrics'
	else:
		metricslink = None

	# Allocate and configure control and monitors.
	control = terminal.setup()
	control.configure(lanes+1)
	monitors, summary = terminal.aggregate(control, proctheme, lanes, width=160)

	try:
		log.xact_open('integration', "Factor Processing Instructions", {})
		try:
			ctxid = cc.identifier

			q = filters.projectgraph(factors, projects)
			local_plan = tools.partial(
				plan, 'integrate',
				cc, factors, features,
				cachetype, cachepath,
				link=metricslink
			)
			execution.dispatch(meta, log, local_plan, control, monitors, summary, "FPI", q, opened=True)
		finally:
			log.xact_close('integration', summary.synopsis("FPI"), {})
	finally:
		control.clear()
		control.flush()

def measure(*args):
	return integrate(*args)
