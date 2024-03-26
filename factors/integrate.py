"""
# Factor integration execution for building images using a system context.
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

# Added to &restricted when mode is 'executable'.
executable_features = {
	'-m': ('set-add', 'metrics', 'features'),

	'-o': ('set-add', 'portable', 'features'),
	'-O': ('set-add', 'optimal', 'features'),
	'-g': ('set-add', 'debug', 'features'),

	'--profile': ('set-add', 'profile', 'features'),
	'--coverage': ('set-add', 'coverage', 'features'),
}

restricted = {
	# Reprocess levels.
	'-N': ('field-replace', -1, 'relevel'),
	'-n': ('field-replace', +0, 'relevel'),
	'-r': ('field-replace', +1, 'relevel'),
	'-R': ('field-replace', +2, 'relevel'),

	# Defaults to update when missing.
	'-u': ('field-replace', 'never', 'update-product-index'),
	'-U': ('field-replace', 'always', 'update-product-index'),

	'-c': ('field-replace', 'transient', 'cache-type'),
	'-.': ('ignore', None, None),
}

required = {
	'-x': ('field-replace', 'machines-context-name'),
	'-X': ('field-replace', 'system-context-directory'),

	'-D': ('field-replace', 'product-directory'),
	'-L': ('field-replace', 'processing-lanes'),
	'-C': ('field-replace', 'persistent-cache'),
}

def plan(command,
		cc:files.Path,
		ccmode:str,
		factors:lsf.Context,
		features:Sequence[str],
		cachetype:str,
		cachepath:files.Path,
		ctl:map.Controls,
		identifier,
	):
	"""
	# Create an invocation for processing &pj with &cc.
	"""

	pj = factors.project(identifier)
	project = pj.factor
	env, exepath, xargv = query.dispatch('factors-cc')

	pj_fp = str(project)
	ki = KInvocation(xargv[0], xargv + [
		str(cc), ccmode, cachetype, str(cachepath),
		':'.join(features),
		str(pj.product.route),
		pj_fp,
	])

	# Factor Processing Instructions
	yield (pj_fp, (), pj_fp, ki)

def dispatch(exits, meta, log, config, cc, pdr:files.Path, argv):
	"""
	# Complete build connecting requirements and updating indexes.
	"""

	from fault.transcript.metrics import Procedure
	zero = Procedure.create()
	os.environ['PRODUCT'] = str(pdr)
	os.environ['F_PRODUCT'] = str(cc)
	os.environ['FPI_REBUILD'] = str(config['relevel'])
	lanes = int(config['processing-lanes'])

	projects = argv
	features = sorted(list(config['features']))
	if not features:
		features = ['optimal']

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

	# Configured Factor Context
	factors = lsf.Context()
	factors.connect(pdr)
	factors.load()
	factors.configure()

	ctl = map.Controls(
		log, meta,
		query.ipath / 'integration',
		'system.images.render',
		ctl_plan = tools.partial(
			plan, 'integrate',
			cc,
			config['construction-mode'],
			factors, features,
			cachetype, cachepath,
		),
		ctl_argv = [],
		ctl_transcript_type = 'processing-units',
		ctl_lanes = int(config['processing-lanes']),
		ctl_opened_frames = True,
		ctl_factor_types = None,
		ctl_open_title = 'Factor Processing Instructions',
		ctl_operating_title = 'FPI',
		ctl_close_title = 'Factors',
	)

	map.execute(exits, ctl, filters.projectgraph(factors, projects))

def configure(restricted, required, argv):
	config = {
		'features': set(),
		'processing-lanes': '4',
		'machines-context-name': 'machines',
		'system-context-directory': None,
		'construction-mode': 'executable',
		'persistent-cache': None,
		'cache-type': 'persistent',
		'product-directory': None,

		'interpreted-connections': [],
		'interpreted-disconnections': [],
		'direct-connections': [],
		'direct-disconnections': [],

		'relevel': 0,
		'cache-directory': None,
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def main(inv:process.Invocation, mode='executable', features=None) -> process.Exit:
	pwd = process.fs_pwd()

	if mode == 'executable':
		res = restricted | executable_features
	else:
		res = restricted

	config, remainder = configure(res, required, inv.argv)
	config['construction-mode'] = mode
	if features is not None:
		config['features'] = features

	if config['product-directory']:
		pdr = files.Path.from_path(config['product-directory'])
	else:
		pdr = pwd

	# Identify the system context to use to process factors.
	origin, cc = context.resolve(config['system-context-directory'], product=pdr)

	if config['cache-directory'] is not None:
		cache = (pwd@config['cache-directory'])
	else:
		cache = (pdr/'.cache')

	with contextlib.ExitStack() as ctx:
		dispatch(ctx, map.Log.stderr(), map.Log.stdout(), config, cc, pdr, remainder)
	return inv.exit(0)
